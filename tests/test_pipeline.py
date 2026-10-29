"""Regression tests for catalog boundaries and batch failure handling."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from documents import DOCUMENTS, load_documents, verify_input
from batch import process_document, select_jobs, main


class PipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        for folder in ('input', 'source/example/assets', 'verification', 'output', 'scripts', 'runs'):
            (self.root / folder).mkdir(parents=True)
        (self.root / 'input/example.pdf').write_bytes(b'%PDF-test-fixture')
        (self.root / 'source/example/content.md').write_text('# Example\n')
        self.config = {
            'id': 'example', 'department': 'test-unit', 'input': 'input/example.pdf',
            'sha256': hashlib.sha256(b'%PDF-test-fixture').hexdigest(),
            'source': 'source/example/content.md', 'verification': 'verification/example',
            'output': 'output/example',
            'title': 'Example', 'evidence_pages': {}, 'verifier': 'scripts/verify_example.py',
        }

    def catalog(self, entries=None):
        path = self.root / 'catalog.json'
        path.write_text(json.dumps({'version': 1, 'documents': entries or [self.config]}))
        return load_documents(path, self.root)

    def run_job(self, stage='all'):
        return process_document('example', self.config, stage, self.root / 'runs', 10, self.root)

    def test_existing_pilot_catalog_and_hashes(self):
        self.assertEqual(len(DOCUMENTS), 2)
        for config in DOCUMENTS.values():
            self.assertEqual(verify_input(config), config['sha256'])

    def test_catalog_normalizes_evidence_page_numbers(self):
        self.config['evidence_pages'] = {'14': 'source/example/assets/page.png'}
        self.assertEqual(self.catalog()['example']['evidence_pages'], {14: 'source/example/assets/page.png'})

    def test_catalog_rejects_duplicate_ids_ignoring_case(self):
        other = deepcopy(self.config)
        other['id'] = 'EXAMPLE'
        with self.assertRaisesRegex(ValueError, 'Duplicate'):
            self.catalog([self.config, other])

    def test_catalog_rejects_shared_verification_directory(self):
        other = deepcopy(self.config)
        other['id'] = 'second'
        other['output'] = 'output/second'
        with self.assertRaisesRegex(ValueError, 'verification directory is shared'):
            self.catalog([self.config, other])

    def test_catalog_rejects_shared_output_directory(self):
        other = deepcopy(self.config)
        other['id'] = 'second'
        other['verification'] = 'verification/second'
        with self.assertRaisesRegex(ValueError, 'output directory is shared'):
            self.catalog([self.config, other])

    def test_catalog_rejects_another_documents_assets(self):
        self.config['evidence_pages'] = {'1': 'source/other/assets/page.png'}
        with self.assertRaisesRegex(ValueError, 'escapes'):
            self.catalog()

    def test_catalog_rejects_assets_directory_symlink_to_another_document(self):
        assets = self.root / 'source/example/assets'
        assets.rmdir()
        other = self.root / 'source/other/assets'
        other.mkdir(parents=True)
        assets.symlink_to(other, target_is_directory=True)
        with self.assertRaisesRegex(ValueError, 'escapes its document folder'):
            self.catalog()

    def test_catalog_rejects_unsafe_paths(self):
        for field, value in [('input', '../outside.pdf'), ('input', '/tmp/input.pdf'),
                             ('source', 'config/content.md'), ('verifier', 'source/run.py'),
                             ('verification', 'source/evidence'), ('output', 'source/output'),
                             ('output', '../outside'), ('output', 'output')]:
            with self.subTest(field=field, value=value):
                config = deepcopy(self.config)
                config[field] = value
                with self.assertRaises(ValueError):
                    self.catalog([config])

    def test_catalog_rejects_symlink_outside_workspace(self):
        with TemporaryDirectory() as outside:
            target = Path(outside) / 'outside.pdf'
            target.write_bytes(b'outside')
            (self.root / 'input/link.pdf').symlink_to(target)
            self.config['input'] = 'input/link.pdf'
            with self.assertRaisesRegex(ValueError, 'escapes'):
                self.catalog()

    def test_catalog_rejects_invalid_hash_and_unsupported_format(self):
        for field, value in [('sha256', 'unverified'), ('input', 'input/example.docx')]:
            config = deepcopy(self.config)
            config[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                self.catalog([config])

    def test_department_filter_and_invalid_selections(self):
        catalog = {'example': self.config, 'other': {**self.config, 'department': 'other-unit'}}
        self.assertEqual(list(select_jobs(catalog, department='test-unit')), ['example'])
        self.assertEqual(list(select_jobs(catalog, names=['other'])), ['other'])
        with self.assertRaises(ValueError):
            select_jobs(catalog, department='missing')
        with self.assertRaises(ValueError):
            select_jobs(catalog, names=['typo'])

    @patch('batch.subprocess.run')
    def test_changed_input_blocks_execution(self, run):
        (self.root / 'input/example.pdf').write_bytes(b'changed')
        result = self.run_job()
        self.assertEqual(result['status'], 'failed')
        self.assertIn('changed', result['detail'])
        run.assert_not_called()

    @patch('batch.subprocess.run')
    def test_missing_canonical_content_requires_reconstruction(self, run):
        (self.root / 'source/example/content.md').unlink()
        result = self.run_job('build')
        self.assertEqual(result['status'], 'needs_reconstruction')
        run.assert_not_called()

    @patch('batch.subprocess.run')
    def test_missing_verifier_is_not_success(self, run):
        self.config['verifier'] = None
        self.assertEqual(self.run_job('verify')['status'], 'needs_verifier')
        run.assert_not_called()

    @patch('batch.subprocess.run', return_value=subprocess.CompletedProcess([], 0))
    def test_success_still_requires_human_review(self, run):
        result = self.run_job()
        self.assertEqual(result['status'], 'checks_passed_needs_review')
        self.assertEqual(result['human_review'], 'not_recorded')
        self.assertEqual(run.call_count, 3)
        self.assertEqual([entry['stage'] for entry in result['stages']], ['extract', 'build', 'verify'])

    @patch('batch.subprocess.run', return_value=subprocess.CompletedProcess([], 2))
    def test_failure_stops_dependent_stages(self, run):
        result = self.run_job()
        self.assertEqual(result['status'], 'failed')
        self.assertEqual(run.call_count, 1)

    @patch('batch.subprocess.run', side_effect=subprocess.TimeoutExpired('extract', 10))
    def test_stage_timeout_is_reported(self, run):
        self.assertEqual(self.run_job()['status'], 'timed_out')
        self.assertEqual(run.call_count, 1)

    def test_source_changed_during_job_invalidates_success(self):
        def change_source(*args, **kwargs):
            (self.root / 'input/example.pdf').write_bytes(b'changed during job')
            return subprocess.CompletedProcess([], 0)
        with patch('batch.subprocess.run', side_effect=change_source):
            self.assertEqual(self.run_job('build')['status'], 'failed')

    def test_batch_continues_after_failure_and_returns_nonzero(self):
        selected = {'example': self.config, 'second': {**self.config, 'id': 'second'}}
        results = [{'id': 'example', 'status': 'failed'},
                   {'id': 'second', 'status': 'checks_passed_needs_review'}]
        with patch('batch.DOCUMENTS', selected), patch('batch.ROOT', self.root), \
                patch('batch.process_document', side_effect=results) as process, patch('builtins.print'):
            self.assertEqual(main([]), 1)
        self.assertEqual(process.call_count, 2)
        reports = list((self.root / 'output/runs').glob('*/report.json'))
        report = json.loads(reports[0].read_text())
        self.assertEqual(report['documents'], results)
        self.assertEqual(report['status'], 'completed_with_blockers')

    def test_dry_run_writes_nothing_and_runs_nothing(self):
        with patch('batch.ROOT', self.root), patch('batch.process_document') as process, \
                patch('builtins.print'):
            self.assertEqual(main(['--dry-run']), 0)
        process.assert_not_called()
        self.assertEqual(list((self.root / 'output').iterdir()), [])


if __name__ == '__main__':
    unittest.main()
