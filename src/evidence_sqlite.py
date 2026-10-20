"""Capa técnica SQLite para el contrato de normalización v1; sin semántica comercial."""
import argparse
from collections import Counter
import csv
from contextlib import closing
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SCHEMA_VERSION = 1
DUPLICATE_DEFINITION = 'Exact raw_text equality, excluding line terminator; all occurrences retained.'
ALIGNMENT_POLICY = '13 fields positional only; 11 fields preserved without alignment.'
RECORD_KEYS = {'row_id', 'source_sha256', 'source_line', 'original_field_count',
               'validation_status', 'original_fields', 'positional_fields_13', 'raw_text', 'line_ending'}
REPORT_KEYS = {'pipeline_version', 'execution_status', 'source_sha256_before',
               'source_sha256_after', 'source_read_sha256', 'output_sha256', 'physical_lines',
               'records_written', 'blank_lines', 'field_count_distribution',
               'validation_status_distribution', 'pending_schema_records', 'invalid_records',
               'semantic_validation_pending_records', 'duplicate_definition', 'duplicate_groups',
               'duplicate_excess_records', 'duplicate_involved_records', 'alignment_policy',
               'audit_acceptance_checked'}
DDL = (
    'CREATE TABLE source_file (source_sha256 TEXT PRIMARY KEY NOT NULL, physical_lines INTEGER NOT NULL CHECK(physical_lines>=0), pipeline_version TEXT NOT NULL)',
    'CREATE TABLE import_manifest (schema_version INTEGER NOT NULL, records_sha256 TEXT NOT NULL, quality_sha256 TEXT NOT NULL)',
    '''CREATE TABLE occurrence (row_id TEXT PRIMARY KEY NOT NULL, source_sha256 TEXT NOT NULL REFERENCES source_file,
       source_line INTEGER NOT NULL CHECK(source_line>0), original_field_count INTEGER CHECK(original_field_count>=0),
       validation_status TEXT NOT NULL, raw_text TEXT NOT NULL, line_ending TEXT NOT NULL CHECK(line_ending IN ('',char(10),char(13)||char(10))),
       UNIQUE(source_sha256,source_line))''',
    '''CREATE TABLE original_field (row_id TEXT NOT NULL REFERENCES occurrence,
       position INTEGER NOT NULL CHECK(position>0), value TEXT NOT NULL, PRIMARY KEY(row_id,position))''',
    '''CREATE TABLE blank_line (source_sha256 TEXT NOT NULL REFERENCES source_file,
       source_line INTEGER NOT NULL CHECK(source_line>0), line_ending TEXT NOT NULL,
       PRIMARY KEY(source_sha256,source_line))''',
    '''CREATE TABLE quality_result (source_sha256 TEXT NOT NULL REFERENCES source_file,
       property TEXT NOT NULL, value_json TEXT NOT NULL, PRIMARY KEY(source_sha256,property))''',
    'CREATE INDEX occurrence_width ON occurrence(original_field_count)',
    'CREATE INDEX occurrence_content ON occurrence(raw_text)',
)
TABLES = {'source_file': 'source_sha256', 'import_manifest': 'schema_version',
          'occurrence': 'source_line', 'original_field': 'row_id,position',
          'blank_line': 'source_line', 'quality_result': 'property'}


class EvidenceError(ValueError):
    """Entrada o destino incompatibles; no se acepta una carga parcial."""


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(path):
    result = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            result.update(block)
    return result.hexdigest()


def require(condition, message):
    if not condition:
        raise EvidenceError(message)


def strict_json(text):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Clave JSON repetida.')
            result[key] = value
        return result
    def constant(_):
        raise EvidenceError('Constante JSON no finita.')
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def read_database(path):
    """Conexión de solo lectura: nunca crea un destino ausente."""
    connection = sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)
    connection.execute('PRAGMA foreign_keys=ON')
    connection.execute('PRAGMA query_only=ON')
    return connection


def _validate_record(record, source_hash, previous):
    require(type(record) is dict and set(record) == RECORD_KEYS, 'Contrato de registro incompatible.')
    line = record['source_line']
    require(type(line) is int and line > previous, 'Líneas fuente inválidas, repetidas o desordenadas.')
    require(record['source_sha256'] == source_hash and record['row_id'] == f'{source_hash}:{line}', 'Trazabilidad de registro incompatible.')
    raw, ending = record['raw_text'], record['line_ending']
    require(type(raw) is str and raw != '' and '\r' not in raw and '\n' not in raw,
            'Texto original incompatible con contrato de línea física.')
    require(not (line == 1 and raw.startswith('\ufeff')), 'BOM incompatible con v1.')
    require(type(ending) is str and ending in ('', '\n', '\r\n'), 'Terminador incompatible.')
    previous_limit = csv.field_size_limit(131072)
    try:
        try:
            fields = next(csv.reader([raw], strict=True))
        except csv.Error as error:
            require('unexpected end of data' not in str(error) and 'field larger than field limit' not in str(error),
                    'Formato rechazado por v1.')
            fields = None
    finally:
        csv.field_size_limit(previous_limit)
    width = len(fields) if fields is not None else None
    status = {13: 'structural_13_semantics_unverified', 11: 'pending_schema_11'}.get(
        width, 'invalid_csv' if width is None else 'invalid_field_count')
    positional = {f'field_{i:02d}': value for i, value in enumerate(fields, 1)} if width == 13 else None
    require(canonical([record['original_fields'], record['original_field_count'], record['validation_status'], record['positional_fields_13']])
            == canonical([fields, width, status, positional]), 'Campos, anchura, estado o posiciones incompatibles con raw_text.')
    return line, raw, ending, fields, width, status


def _populate(connection, records, report, records_hash, quality_hash):
    """Valida contrato/reconstrucción dentro de una transacción aún no aceptada."""
    require(type(report) is dict and set(report) == REPORT_KEYS, 'Contrato quality.json incompatible.')
    source_hash = report['source_sha256_before']
    require(type(source_hash) is str and re.fullmatch('[0-9a-f]{64}', source_hash), 'Hash fuente inválido.')
    require(type(report['audit_acceptance_checked']) is bool, 'Indicador auditado inválido.')
    physical = report['physical_lines']
    require(type(physical) is int and physical >= 0, 'Cantidad de líneas inválida.')
    blanks = report['blank_lines']
    require(type(blanks) is list, 'Contrato de líneas vacías incompatible.')
    blank_map = {}
    previous = 0
    for item in blanks:
        require(type(item) is dict and set(item) == {'source_line', 'line_ending'}, 'Línea vacía incompatible.')
        line, ending = item['source_line'], item['line_ending']
        require(type(line) is int and previous < line <= physical and type(ending) is str
                and ending in ('', '\n', '\r\n'), 'Líneas vacías inválidas.')
        blank_map[line] = ending
        previous = line
    for statement in DDL:
        connection.execute(statement)
    connection.execute('PRAGMA user_version=1')
    connection.execute('INSERT INTO source_file VALUES (?,?,?)', (source_hash, physical, '1'))
    connection.execute('INSERT INTO import_manifest VALUES (?,?,?)', (SCHEMA_VERSION, records_hash, quality_hash))
    connection.executemany('INSERT INTO blank_line VALUES (?,?,?)', ((source_hash, line, ending) for line, ending in blank_map.items()))
    contents, widths, statuses = Counter(), Counter(), Counter()
    source_digest = hashlib.sha256()
    next_line, total = 1, 0

    def append_source(line, raw, ending):
        require(ending != '' or line == physical, 'Terminador final ausente antes del fin de fuente.')
        source_digest.update((raw + ending).encode('utf-8'))

    with records.open(encoding='utf-8', newline='') as stream:
        for text in stream:
            record = strict_json(text)
            line, raw, ending, fields, width, status = _validate_record(record, source_hash, next_line - 1)
            require(line <= physical and line not in blank_map, 'Línea fuera de rango o solapada.')
            while next_line < line:
                require(next_line in blank_map, 'Falta ocurrencia o línea fuente.')
                append_source(next_line, '', blank_map[next_line])
                next_line += 1
            append_source(line, raw, ending)
            connection.execute('INSERT INTO occurrence VALUES (?,?,?,?,?,?,?)',
                               (record['row_id'], source_hash, line, width, status, raw, ending))
            if fields is not None:
                connection.executemany('INSERT INTO original_field VALUES (?,?,?)',
                                       ((record['row_id'], i, value) for i, value in enumerate(fields, 1)))
            next_line = line + 1
            total += 1
            contents[raw] += 1
            widths[str(width) if width is not None else 'unparseable'] += 1
            statuses[status] += 1
    while next_line <= physical:
        require(next_line in blank_map, 'Fuente incompleta al final.')
        append_source(next_line, '', blank_map[next_line])
        next_line += 1
    reconstructed = source_digest.hexdigest()
    require(reconstructed == source_hash, 'La reconstrucción no coincide con SHA-256 fuente.')
    expected = {
        'pipeline_version': '1', 'execution_status': 'complete', 'source_sha256_before': reconstructed,
        'source_sha256_after': reconstructed, 'source_read_sha256': reconstructed, 'output_sha256': records_hash,
        'physical_lines': physical, 'records_written': total, 'blank_lines': blanks,
        'field_count_distribution': dict(widths), 'validation_status_distribution': dict(statuses),
        'pending_schema_records': statuses['pending_schema_11'],
        'invalid_records': statuses['invalid_csv'] + statuses['invalid_field_count'],
        'semantic_validation_pending_records': total, 'duplicate_definition': DUPLICATE_DEFINITION,
        'duplicate_groups': sum(n > 1 for n in contents.values()),
        'duplicate_excess_records': sum(n - 1 for n in contents.values()),
        'duplicate_involved_records': sum(n for n in contents.values() if n > 1),
        'alignment_policy': ALIGNMENT_POLICY, 'audit_acceptance_checked': report['audit_acceptance_checked'],
    }
    require(canonical(report) == canonical(expected), 'quality.json no coincide con la evidencia reconstruida.')
    if report['audit_acceptance_checked']:
        require(source_hash == '09d8a61644f66cbb9ad8c50f59180978a0995d121196faf25ef28083dd7b84a2'
                and total == 95911 and dict(widths) == {'13': 90559, '11': 5352}
                and expected['duplicate_excess_records'] == 2589, 'Declaración audit_acceptance_checked inconsistente.')
    connection.executemany('INSERT INTO quality_result VALUES (?,?,?)',
                           ((source_hash, key, canonical(value)) for key, value in report.items()))
    require(not connection.execute('PRAGMA foreign_key_check').fetchall(), 'Error referencial.')
    require(connection.execute('PRAGMA integrity_check').fetchone() == ('ok',), 'Error de integridad SQLite.')


def _same_database(left, right):
    """Comparación completa, incluyendo esquema; no confía solo en el manifiesto."""
    schema = "SELECT type,name,tbl_name,sql FROM sqlite_master WHERE name NOT LIKE 'sqlite_%' ORDER BY type,name"
    if left.execute(schema).fetchall() != right.execute(schema).fetchall():
        return False
    if left.execute('PRAGMA user_version').fetchone() != right.execute('PRAGMA user_version').fetchone():
        return False
    sentinel = object()
    for table, order in TABLES.items():
        a = iter(left.execute(f'SELECT * FROM {table} ORDER BY {order}'))
        b = iter(right.execute(f'SELECT * FROM {table} ORDER BY {order}'))
        while True:
            x, y = next(a, sentinel), next(b, sentinel)
            if x is sentinel and y is sentinel:
                break
            if x != y:
                return False
    return True


def load(records, quality, database):
    records, quality, database = (Path(p).resolve() for p in (records, quality, database))
    require(records != quality and database not in (records, quality), 'Rutas de entrada/salida solapadas.')
    for folder in ('data/raw', 'data/processed', 'src', 'tests'):
        protected = ROOT / folder
        require(database != protected and protected not in database.parents, 'Destino dentro de una carpeta protegida.')
    require(database.suffix.lower() in ('.sqlite', '.sqlite3', '.db'), 'Destino debe ser SQLite (.sqlite/.sqlite3/.db).')
    records_hash, quality_hash = digest(records), digest(quality)
    report = strict_json(quality.read_text(encoding='utf-8'))
    require(type(report) is dict and report.get('output_sha256') == records_hash, 'Hash de records.jsonl incompatible.')
    require(set(report) == REPORT_KEYS and report.get('pipeline_version') == '1'
            and report.get('execution_status') == 'complete', 'Reporte incompleto o versión incompatible.')
    database.parent.mkdir(parents=True, exist_ok=True)
    # No reemplaza ningún archivo; el enlace final exclusivo evita carreras sobre el destino.
    with tempfile.TemporaryDirectory(prefix='.evidence-', dir=database.parent) as staging:
        temporary = Path(staging) / 'build.sqlite'
        connection = sqlite3.connect(temporary)
        try:
            connection.execute('PRAGMA foreign_keys=ON')
            connection.execute('BEGIN IMMEDIATE')
            _populate(connection, records, report, records_hash, quality_hash)
            require(digest(records) == records_hash and digest(quality) == quality_hash, 'Entradas cambiaron durante la carga.')
            connection.commit()
        except BaseException:
            connection.rollback()
            raise
        finally:
            connection.close()
        if database.exists():
            with closing(read_database(temporary)) as proposed, closing(read_database(database)) as existing:
                require(_same_database(proposed, existing), 'Destino existente distinto: no se sobrescribe.')
            state = 'unchanged'
        else:
            os.link(temporary, database)
            state = 'created'
    return {'status': state, 'records': report['records_written'], 'source_sha256': report['source_sha256_before']}


def inspect_database(database, query='summary', row_id=None):
    connection = read_database(database)
    try:
        require(connection.execute('PRAGMA user_version').fetchone() == (SCHEMA_VERSION,), 'Versión SQLite incompatible.')
        if query == 'summary':
            return {'occurrences': connection.execute('SELECT COUNT(*) FROM occurrence').fetchone()[0],
                    'fields': connection.execute('SELECT COUNT(*) FROM original_field').fetchone()[0],
                    'widths': {str(width) if width is not None else 'unparseable': count
                               for width, count in connection.execute('SELECT original_field_count,COUNT(*) FROM occurrence GROUP BY original_field_count')}}
        if query == 'quality':
            return {key: json.loads(value) for key, value in connection.execute('SELECT property,value_json FROM quality_result ORDER BY property')}
        if query == 'multiplicity':
            groups = connection.execute('SELECT COUNT(*) FROM occurrence GROUP BY raw_text HAVING COUNT(*)>1')
            counts = [n for (n,) in groups]
            return {'duplicate_groups': len(counts), 'duplicate_excess_records': sum(n-1 for n in counts),
                    'duplicate_involved_records': sum(counts)}
        require(query == 'record' and row_id is not None, 'Consulta de ocurrencia requiere --row-id.')
        row = connection.execute('SELECT * FROM occurrence WHERE row_id=?', (row_id,)).fetchone()
        require(row is not None, 'Ocurrencia no encontrada.')
        fields = [value for (value,) in connection.execute('SELECT value FROM original_field WHERE row_id=? ORDER BY position', (row_id,))]
        fields = None if row[3] is None else fields
        return dict(zip(('row_id', 'source_sha256', 'source_line', 'original_field_count', 'validation_status', 'raw_text', 'line_ending'), row),
                    original_fields=fields, positional_fields_13={f'field_{i:02d}': value for i,value in enumerate(fields,1)} if row[3] == 13 else None)
    finally:
        connection.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    loader = commands.add_parser('load')
    loader.add_argument('--records', type=Path, required=True)
    loader.add_argument('--quality', type=Path, required=True)
    loader.add_argument('--database', type=Path, required=True)
    query = commands.add_parser('query')
    query.add_argument('--database', type=Path, required=True)
    query.add_argument('--query', choices=['summary', 'quality', 'multiplicity', 'record'], default='summary')
    query.add_argument('--row-id')
    args = parser.parse_args()
    try:
        result = (load(args.records, args.quality, args.database) if args.command == 'load'
                  else inspect_database(args.database, args.query, args.row_id))
        print(canonical(result))
    except (OSError, ValueError, RuntimeError, sqlite3.Error, UnicodeError):
        # No volcar registros, IDs ni rutas personales en errores del CLI.
        parser.exit(1, 'Error: carga/consulta rechazada; comprobar contrato, integridad, rutas y permisos.\n')


if __name__ == '__main__':
    main()
