"""Document-specific paths and immutable source fingerprints."""
from pathlib import Path
import argparse
ROOT = Path(__file__).resolve().parents[1]
DOCUMENTS = {
    '2023-BA-Year0-Plan': {
        'sha256': '1625ff6a4f7b8d0397b09b8b0a934fde01f32fd22b9b3c0a46c5313f4d8389e1',
        'source': 'source/assessment-plan.md', 'verification': 'verification',
        'title': 'Year 0 Assessment Plan Report | Academic Year 2023-2024',
        'evidence_pages': {14: 'assets/survey-outcomes-source-page-14.png'},
    },
    '2025-Year0-DS-Plan': {
        'sha256': '798dab9341e8a9e4aadf8aa6b243cd068aeee50d07c1516823176c5caf224565',
        'source': 'source/2025-Year0-DS-Plan/assessment-plan.md',
        'verification': 'verification/2025-Year0-DS-Plan',
        'title': 'Year 0 Assessment Plan | Data Science | Academic Year 2025-2026',
        'evidence_pages': {},
    },
}
def select_document():
    parser = argparse.ArgumentParser()
    parser.add_argument('--document', choices=DOCUMENTS, default='2023-BA-Year0-Plan',
                        help='PDF filename without extension; defaults to the original pilot')
    name = parser.parse_args().document
    return name, DOCUMENTS[name]
