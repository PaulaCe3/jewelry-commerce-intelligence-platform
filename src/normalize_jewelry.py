"""Normalización posicional conservadora, sin dependencias externas."""
import argparse
from collections import Counter
import csv
import hashlib
import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AUDITED_SHA256 = '09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2'
VERSION = '1'
MAX_FIELD_CHARS = 131072


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def encode_json(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'))


def normalize(source, destination, *, check_audit=False):
    """Crea un directorio nuevo; quality.json es el marcador de ejecución completa.

    Una línea física por registro. BOM, CR aislado, campos excesivos y comillas
    sin cerrar se rechazan sin publicar quality.json; nunca se adivinan columnas.
    """
    source, destination = Path(source).resolve(), Path(destination).resolve()
    raw_root = ROOT / 'data' / 'raw'
    if (destination == source.parent or source.parent in destination.parents
            or destination == raw_root or raw_root in destination.parents
            or destination == source or destination in source.parents):
        raise ValueError('El destino no puede contener el original ni estar en su carpeta o en data/raw.')
    before = sha256(source)
    if check_audit and before != AUDITED_SHA256:
        raise ValueError('SHA-256 distinto del archivo auditado; no se genera salida.')
    destination.mkdir(parents=True, exist_ok=False)
    output = destination / 'records.jsonl'
    widths, statuses, contents = Counter(), Counter(), Counter()
    blank_lines = []
    total = 0
    physical_lines = 0
    read_hash = hashlib.sha256()
    try:
        with source.open('rb') as incoming, output.open('x', encoding='utf-8', newline='\n') as outgoing:
            for line_number, binary in enumerate(incoming, 1):
                physical_lines = line_number
                read_hash.update(binary)
                text = binary.decode('utf-8', errors='strict')
                ending = '\r\n' if text.endswith('\r\n') else '\n' if text.endswith('\n') else ''
                raw = text[:-len(ending)] if ending else text
                if line_number == 1 and raw.startswith('\ufeff'):
                    raise ValueError('UTF-8 con BOM no admitido; no se elimina el BOM automáticamente.')
                if '\r' in raw:
                    raise ValueError('CR aislado o dentro de un campo no admitido; usar LF o CRLF.')
                if raw == '':
                    blank_lines.append({'source_line': line_number, 'line_ending': ending})
                    continue
                fields = None
                previous_limit = csv.field_size_limit(MAX_FIELD_CHARS)
                try:
                    fields = next(csv.reader([raw], strict=True))
                except csv.Error as error:
                    if 'unexpected end of data' in str(error) or 'field larger than field limit' in str(error):
                        raise ValueError('CSV multilínea/comillas sin cerrar o campo mayor a 131072 caracteres no admitido.') from error
                finally:
                    csv.field_size_limit(previous_limit)
                width = len(fields) if fields is not None else None
                if width == 13:
                    status = 'structural_13_semantics_unverified'
                    positional = {f'field_{i:02d}': value for i, value in enumerate(fields, 1)}
                else:
                    positional = None
                    status = ('pending_schema_11' if width == 11 else
                              'invalid_csv' if fields is None else 'invalid_field_count')
                record = {
                    'row_id': f'{before}:{line_number}',
                    'source_sha256': before,
                    'source_line': line_number,
                    'original_field_count': width,
                    'validation_status': status,
                    'original_fields': fields,
                    'positional_fields_13': positional,
                    'raw_text': raw,
                    'line_ending': ending,
                }
                outgoing.write(encode_json(record) + '\n')
                total += 1
                widths[str(width) if width is not None else 'unparseable'] += 1
                statuses[status] += 1
                contents[raw] += 1
    finally:
        after = sha256(source)
        if before != after:
            raise RuntimeError('El original cambió durante la ejecución; salida incompleta, no utilizable.')
    if read_hash.hexdigest() != before:
        raise RuntimeError('El contenido leído no coincide con el hash inicial; salida incompleta.')
    excess = sum(count - 1 for count in contents.values())
    if check_audit and (total != 95911 or dict(widths) != {'13': 90559, '11': 5352} or excess != 2589):
        raise RuntimeError('No se cumplen los conteos auditados; salida incompleta.')
    report = {
        'pipeline_version': VERSION,
        'execution_status': 'complete',
        'source_sha256_before': before,
        'source_sha256_after': after,
        'source_read_sha256': read_hash.hexdigest(),
        'output_sha256': sha256(output),
        'physical_lines': physical_lines,
        'records_written': total,
        'blank_lines': blank_lines,
        'field_count_distribution': dict(widths),
        'validation_status_distribution': dict(statuses),
        'pending_schema_records': statuses['pending_schema_11'],
        'invalid_records': statuses['invalid_csv'] + statuses['invalid_field_count'],
        'semantic_validation_pending_records': total,
        'duplicate_definition': 'Exact raw_text equality, excluding line terminator; all occurrences retained.',
        'duplicate_groups': sum(count > 1 for count in contents.values()),
        'duplicate_excess_records': excess,
        'duplicate_involved_records': sum(count for count in contents.values() if count > 1),
        'alignment_policy': '13 fields positional only; 11 fields preserved without alignment.',
        'audit_acceptance_checked': check_audit,
    }
    # Publicar el marcador solo después de escribir, vaciar y cerrar el reporte.
    # link es exclusivo: no reemplaza un quality.json existente (también en POSIX).
    pending_report = destination / '.quality.json.partial'
    with pending_report.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(encode_json(report) + '\n')
        stream.flush()
        os.fsync(stream.fileno())
    os.link(pending_report, destination / 'quality.json')
    # El alias temporal no afecta la validez del marcador ya publicado.
    try:
        pending_report.unlink()
    except OSError:
        pass
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True, help='Directorio nuevo dentro de data/processed.')
    parser.add_argument('--check-audit', action='store_true', help='Exigir hash y conteos de la auditoría documentada.')
    args = parser.parse_args()
    processed = (ROOT / 'data' / 'processed').resolve()
    destination = args.output_dir.resolve()
    if processed not in destination.parents:
        parser.error('--output-dir debe ser un subdirectorio nuevo de data/processed.')
    try:
        report = normalize(ROOT / 'data' / 'raw' / 'jewelry.csv', destination, check_audit=args.check_audit)
    except (OSError, ValueError, RuntimeError, UnicodeError) as error:
        parser.exit(1, f'Error: {error}\n')
    print(encode_json(report))


if __name__ == '__main__':
    main()
