#!/usr/bin/env python3
"""Run registered PDF jobs sequentially; successful checks still need review."""
import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4

from documents import DOCUMENTS, ROOT, local_path, verify_input

SUCCESS = {'completed_unreviewed', 'checks_passed_needs_review'}


def select_jobs(documents, department=None, names=None):
    unknown = set(names or []) - documents.keys()
    if unknown:
        raise ValueError('Unknown document IDs: ' + ', '.join(sorted(unknown)))
    selected = {name: config for name, config in documents.items()
                if (not department or config['department'] == department)
                and (not names or name in names)}
    if not selected:
        raise ValueError('No documents match the requested selection')
    return selected


def commands_for(name, config, stage, root=ROOT):
    stages = ('extract', 'build', 'verify') if stage == 'all' else (stage,)
    commands = []
    for item in stages:
        if item == 'verify':
            verifier = config.get('verifier')
            command = [sys.executable, str(local_path(verifier, root, 'scripts'))] if verifier else None
        else:
            command = [sys.executable, str(root / 'scripts' / f'{item}.py'), '--document', name]
        commands.append((item, command))
    return commands


def process_document(name, config, stage, run_dir, timeout, root=ROOT):
    result = {'id': name, 'department': config['department'],
              'source_sha256': config['sha256'], 'status': 'failed',
              'human_review': 'not_recorded', 'stages': []}
    started = time.monotonic()
    try:
        verify_input(config, root)
        for item, command in commands_for(name, config, stage, root):
            if command is None:
                result.update(status='needs_verifier', detail='No fidelity verifier is registered.')
                break
            if item == 'build' and not local_path(config['source'], root, 'source').is_file():
                result.update(status='needs_reconstruction', detail='Canonical Markdown must be reconstructed and reviewed first.')
                break
            log = run_dir / f'{name}-{item}.log'
            record = {'stage': item, 'log': log.name}
            result['stages'].append(record)
            with log.open('w', encoding='utf-8') as stream:
                try:
                    completed = subprocess.run(command, cwd=root, stdout=stream,
                                               stderr=subprocess.STDOUT, timeout=timeout, check=False)
                except subprocess.TimeoutExpired:
                    record['status'] = 'timed_out'
                    result.update(status='timed_out', detail=f'{item} exceeded {timeout} seconds.')
                    break
            record.update(returncode=completed.returncode,
                          status='passed' if completed.returncode == 0 else 'failed')
            if completed.returncode:
                result['detail'] = f'{item} failed; see {log.name}.'
                break
        else:
            result['status'] = ('checks_passed_needs_review' if stage in ('all', 'verify')
                                else 'completed_unreviewed')
        # Detect a source edited during processing as well as before it.
        verify_input(config, root)
    except (OSError, ValueError) as exc:
        result.update(status='failed', detail=str(exc))
    result['elapsed_seconds'] = round(time.monotonic() - started, 3)
    return result


def positive_timeout(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('timeout must be a positive number of seconds')
    return number


def write_report(path, report):
    temporary = path.with_suffix('.tmp')
    temporary.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    temporary.replace(path)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--department', help='Department slug from config/documents.json')
    parser.add_argument('--document', action='append', help='Document ID; repeat to select several')
    parser.add_argument('--stage', choices=('extract', 'build', 'verify', 'all'), default='all')
    parser.add_argument('--timeout', type=positive_timeout, default=300, help='Seconds per stage (default: 300)')
    parser.add_argument('--dry-run', action='store_true', help='Show the plan without running jobs or writing files')
    args = parser.parse_args(argv)
    try:
        selected = select_jobs(DOCUMENTS, args.department, args.document)
    except ValueError as exc:
        parser.error(str(exc))
    if args.dry_run:
        plan = [{'id': name, 'department': config['department'],
                 'stages': [{'stage': stage, 'command': command}
                            for stage, command in commands_for(name, config, args.stage)]}
                for name, config in selected.items()]
        print(json.dumps(plan, indent=2))
        return 0
    run_dir = ROOT / 'output' / 'runs' / uuid4().hex
    run_dir.mkdir(parents=True)
    report_path = run_dir / 'report.json'
    report = {'schema_version': 1, 'started_at': datetime.now(timezone.utc).isoformat(),
              'stage': args.stage, 'status': 'running',
              'scope': 'Local PDF processing and fidelity checks; no publication or accessibility certification.',
              'documents': [{'id': name, 'status': 'not_started'} for name in selected]}
    write_report(report_path, report)
    for index, (name, config) in enumerate(selected.items()):
        report['documents'][index]['status'] = 'running'
        write_report(report_path, report)
        result = process_document(name, config, args.stage, run_dir, args.timeout)
        report['documents'][index] = result
        write_report(report_path, report)
        print(f'{name}: {result["status"]}', flush=True)
    failed = any(result['status'] not in SUCCESS for result in report['documents'])
    report['status'] = 'completed_with_blockers' if failed else 'completed_unreviewed'
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    write_report(report_path, report)
    print(f'Report: {report_path.relative_to(ROOT)}')
    return 1 if failed else 0


if __name__ == '__main__':
    raise SystemExit(main())
