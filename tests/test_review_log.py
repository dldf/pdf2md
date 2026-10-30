"""Check that review warnings survive relocation out of the Markdown."""
from pathlib import Path
import sys
from tempfile import TemporaryDirectory
import unittest

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from convert import convert_pdf


class ReviewLogTests(unittest.TestCase):
    def convert(self, flagged=False):
        temporary = TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        pdf = root / 'source.pdf'
        destination = root / 'converted'
        with pymupdf.open() as document:
            page = document.new_page()
            page.insert_text((72, 90), 'A plain paragraph with enough text to need no page review.')
            if flagged:
                page = document.new_page()
                page.draw_circle((150, 150), 30)
                page.insert_text((130, 150), 'Figure')
            document.save(pdf)
        result = convert_pdf(pdf, destination)
        return destination, result

    def test_multiple_warnings_count_as_one_flagged_page(self):
        folder, result = self.convert(flagged=True)
        markdown = (folder / 'content.md').read_text()
        log = (folder / 'review/log.txt').read_text()
        self.assertEqual(result, (2, 1))
        self.assertEqual(log.splitlines()[:2], [str((folder / 'content.md').resolve()),
                                               '2 pages, 1 flagged for review:'])
        self.assertEqual(log.count('  Page 2/2 : '), 1)
        for reason in ('Vector graphics preserved as an image', 'Little or no extractable text'):
            self.assertIn(reason, log)
            self.assertNotIn(reason, markdown)
        self.assertIn('> **Review page 2:** [Original page image](review/p002-original.png)', markdown)
        self.assertTrue((folder / 'review/p002-original.png').exists())

    def test_unflagged_document_also_has_a_log(self):
        folder, result = self.convert()
        self.assertEqual(result, (1, 0))
        self.assertEqual((folder / 'review/log.txt').read_text().splitlines(),
                         [str((folder / 'content.md').resolve()), '1 pages, 0 flagged for review:'])
        self.assertNotIn('**Review page', (folder / 'content.md').read_text())


if __name__ == '__main__':
    unittest.main()
