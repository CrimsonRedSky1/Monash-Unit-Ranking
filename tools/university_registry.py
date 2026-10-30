"""Shared registration and unit validation; no fetching or file writes on import."""
from dataclasses import dataclass
from typing import Callable
from urllib.parse import urlparse
import re

@dataclass(frozen=True)
class ImportAdapter:
    discover: Callable[[str], list[str]]
    parse: Callable[[str, str], dict]
    coverage_note: str = ''
    supported_years: tuple[str, ...] = ()

class UniversityRegistry:
    def __init__(self):
        self.universities = {}
        self.adapters = {}

    def register_university(self, details):
        uid = details.get('id', '')
        if not isinstance(uid, str) or not re.fullmatch(r'[a-z][a-z0-9_-]*', uid):
            raise ValueError('University ID must be a lowercase identifier')
        if uid in self.universities:
            raise ValueError(f'Duplicate university: {uid}')
        for field in ('name', 'short_name', 'handbook'):
            if not isinstance(details.get(field), str) or not details[field].strip():
                raise ValueError(f'{uid}: missing {field}')
        if urlparse(details['handbook']).scheme != 'https':
            raise ValueError(f'{uid}: handbook must use HTTPS')
        self.universities[uid] = dict(details)

    def register_importer(self, uid, adapter):
        if uid not in self.universities:
            raise ValueError(f'Unknown university: {uid}')
        if uid in self.adapters:
            raise ValueError(f'Duplicate importer: {uid}')
        if not callable(adapter.discover) or not callable(adapter.parse):
            raise ValueError('Importer needs discovery and parser functions')
        self.adapters[uid] = adapter

    def importer(self, uid, year):
        if uid not in self.universities:
            raise ValueError(f'Unknown university: {uid}')
        if uid not in self.adapters:
            raise ValueError(f'{uid}: automatic import is not configured; existing catalogue is retained')
        adapter = self.adapters[uid]
        if adapter.supported_years and year not in adapter.supported_years:
            raise ValueError(f'{uid}: importer supports years {", ".join(adapter.supported_years)} only')
        return adapter

def validate_unit(record, university, year=None):
    """Validate the common record contract while retaining source-specific fields."""
    if not isinstance(record, dict):
        raise ValueError('Parser must return a unit object')
    result = dict(record)
    for field in ('id', 'university', 'code', 'name', 'faculty', 'source'):
        if not isinstance(result.get(field), str) or not result[field].strip():
            raise ValueError(f'Unit missing {field}')
        result[field] = result[field].strip()
    if result['university'] != university or not result['id'].startswith(university + ':') or not result['id'].split(':', 1)[1]:
        raise ValueError('Unit identity does not match its university')
    parsed = urlparse(result['source'])
    if parsed.scheme != 'https' or not parsed.netloc:
        raise ValueError('Unit source must be an HTTPS URL')
    unit_year = str(result.get('year', ''))
    if not re.fullmatch(r'\d{4}', unit_year) or (year is not None and unit_year != str(year)):
        raise ValueError('Unit year does not match requested catalogue year')
    result['year'] = unit_year
    result.setdefault('description', '')
    result.setdefault('credits', '')
    return result
