"""Validated local PDF catalog, shared by single-document and batch commands."""
from pathlib import Path
import argparse
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[1]


def local_path(value, root=ROOT, directory=None):
    """Reject absolute paths, traversal, and symlinks escaping the workspace."""
    if not isinstance(value, str) or not value.strip():
        raise ValueError('Catalog paths must be nonempty strings')
    path = Path(value)
    if path.is_absolute() or '..' in path.parts:
        raise ValueError(f'Catalog path must be relative: {value}')
    resolved = (root / path).resolve()
    boundary = (root / directory).resolve() if directory else root.resolve()
    if not boundary.is_relative_to(root.resolve()) or not resolved.is_relative_to(boundary):
        raise ValueError(f'Catalog path escapes its directory: {value}')
    if resolved == boundary:
        raise ValueError(f'Catalog path must name an item within its directory: {value}')
    return resolved


def load_documents(path=None, root=ROOT):
    path = path or root / 'config/documents.json'
    raw = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(raw, dict) or raw.get('version') != 1 or not isinstance(raw.get('documents'), list):
        raise ValueError('Expected document catalog version 1 with a documents list')
    documents = {}
    destinations = set()
    for original in raw['documents']:
        if not isinstance(original, dict):
            raise ValueError('Each catalog entry must be an object')
        entry = dict(original)
        for field in ('id', 'department'):
            value = entry.get(field)
            if not isinstance(value, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]*', value):
                raise ValueError(f'Invalid {field}: {value!r}')
        name = entry['id']
        if name.casefold() in {key.casefold() for key in documents}:
            raise ValueError(f'Duplicate document ID: {name}')
        if not isinstance(entry.get('title'), str) or not entry['title'].strip():
            raise ValueError(f'{name}: missing title')
        if not isinstance(entry.get('sha256'), str) or not re.fullmatch(r'[0-9a-f]{64}', entry['sha256']):
            raise ValueError(f'{name}: invalid SHA-256')
        input_path = local_path(entry.get('input'), root, 'input')
        if input_path.suffix.lower() != '.pdf':
            raise ValueError(f'{name}: only the PDF processing route is implemented')
        source = local_path(entry.get('source'), root, 'source')
        for field in ('output', 'verification'):
            folder = local_path(entry.get(field), root, field)
            destination = str(folder).casefold()
            if destination in destinations:
                raise ValueError(f'{name}: {field} directory is shared by two documents')
            destinations.add(destination)
        verifier = entry.get('verifier')
        if verifier is not None:
            if local_path(verifier, root, 'scripts').suffix != '.py':
                raise ValueError(f'{name}: verifier must be a local Python script')
        evidence = entry.get('evidence_pages', {})
        if not isinstance(evidence, dict):
            raise ValueError(f'{name}: evidence_pages must be an object')
        entry['evidence_pages'] = {}
        assets = (source.parent / 'assets').resolve()
        if not assets.is_relative_to(source.parent):
            raise ValueError(f'{name}: assets directory escapes its document folder')
        for page, asset in evidence.items():
            if not re.fullmatch(r'[1-9][0-9]*', page):
                raise ValueError(f'{name}: evidence page must be a positive integer')
            local_path(asset, root, assets)
            entry['evidence_pages'][int(page)] = asset
        documents[name] = entry
    if not documents:
        raise ValueError('Document catalog is empty')
    return documents


def verify_input(config, root=ROOT):
    path = local_path(config['input'], root, 'input')
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    if digest != config['sha256']:
        raise ValueError(f'Source PDF changed: {config["input"]}. Review the new version first.')
    return digest


DOCUMENTS = load_documents()


def select_document():
    parser = argparse.ArgumentParser()
    parser.add_argument('--document', choices=DOCUMENTS, default='2023-BA-Year0-Plan',
                        help='PDF filename without extension; defaults to the original pilot')
    name = parser.parse_args().document
    return name, DOCUMENTS[name]
