"""Oráculo de QA: no importa funciones, constantes ni serializadores del pipeline."""
from collections import Counter
import csv
import hashlib
import json
from pathlib import Path


def digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(65536), b''):
            digest.update(block)
    return digest.hexdigest()


def validate_output(source, directory, *, audit_checked):
    source, directory = Path(source), Path(directory)
    digest = digest_file(source)
    counts, widths, states = Counter(), Counter(), Counter()
    blanks, identifiers = [], set()
    physical = total = 0
    with source.open('rb') as incoming, (directory / 'records.jsonl').open(encoding='utf-8') as outgoing:
        for number, binary in enumerate(incoming, 1):
            physical = number
            text = binary.decode('utf-8')
            ending = '\r\n' if text.endswith('\r\n') else '\n' if text.endswith('\n') else ''
            raw = text[:len(text)-len(ending)] if ending else text
            if raw == '':
                blanks.append({'source_line': number, 'line_ending': ending})
                continue
            try:
                fields = next(csv.reader([raw], strict=True))
            except csv.Error:
                fields = None
            width = len(fields) if fields is not None else None
            state = {13: 'structural_13_semantics_unverified', 11: 'pending_schema_11'}.get(width)
            if state is None:
                state = 'invalid_csv' if fields is None else 'invalid_field_count'
            expected = {
                'row_id': digest + ':' + str(number),
                'source_sha256': digest,
                'source_line': number,
                'original_field_count': width,
                'validation_status': state,
                'original_fields': fields,
                'positional_fields_13': dict(zip(['field_%02d' % i for i in range(1,14)], fields)) if width == 13 else None,
                'raw_text': raw,
                'line_ending': ending,
            }
            line = outgoing.readline()
            if not line:
                raise AssertionError('Falta registro de salida en línea fuente ' + str(number))
            actual = json.loads(line)
            # Comparación serializada exige también tipos (True no equivale a 1).
            if json.dumps(actual, sort_keys=True) != json.dumps(expected, sort_keys=True):
                raise AssertionError('Registro o metadatos distintos en línea fuente ' + str(number))
            if actual['row_id'] in identifiers:
                raise AssertionError('ID repetido')
            identifiers.add(actual['row_id'])
            total += 1
            counts[raw] += 1
            widths[str(width) if width is not None else 'unparseable'] += 1
            states[state] += 1
        if outgoing.read():
            raise AssertionError('Hay registros extra en salida')
    expected_report = {
        'pipeline_version': '1', 'execution_status': 'complete',
        'source_sha256_before': digest, 'source_sha256_after': digest,
        'source_read_sha256': digest,
        'output_sha256': digest_file(directory / 'records.jsonl'),
        'physical_lines': physical, 'records_written': total, 'blank_lines': blanks,
        'field_count_distribution': dict(widths), 'validation_status_distribution': dict(states),
        'pending_schema_records': states['pending_schema_11'],
        'invalid_records': states['invalid_csv'] + states['invalid_field_count'],
        'semantic_validation_pending_records': total,
        'duplicate_definition': 'Exact raw_text equality, excluding line terminator; all occurrences retained.',
        'duplicate_groups': sum(1 for value in counts.values() if value > 1),
        'duplicate_excess_records': total - len(counts),
        'duplicate_involved_records': sum(value for value in counts.values() if value > 1),
        'alignment_policy': '13 fields positional only; 11 fields preserved without alignment.',
        'audit_acceptance_checked': audit_checked,
    }
    actual_report = json.loads((directory / 'quality.json').read_text(encoding='utf-8'))
    if json.dumps(actual_report, sort_keys=True) != json.dumps(expected_report, sort_keys=True):
        differences = sorted(key for key in set(actual_report) | set(expected_report)
                             if json.dumps(actual_report.get(key), sort_keys=True) != json.dumps(expected_report.get(key), sort_keys=True))
        raise AssertionError('quality.json no coincide: ' + ', '.join(differences))
    if digest_file(source) != digest:
        raise AssertionError('Original alterado durante la verificación')
    return expected_report
