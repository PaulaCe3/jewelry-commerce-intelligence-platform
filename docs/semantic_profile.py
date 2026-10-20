"""Perfil semántico de solo lectura. Emite agregados, nunca filas ni IDs."""
from collections import Counter, defaultdict
import csv
from datetime import datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''):
            result.update(block)
    return result.hexdigest()


def profile():
    source = ROOT / 'data/raw/jewelry.csv'
    protected = [p for folder in ['data/raw', 'data/processed', 'src', 'tests']
                 for p in (ROOT/folder).rglob('*') if p.is_file()]
    before = {str(p.relative_to(ROOT)): digest(p) for p in protected}
    columns = {width: [Counter() for _ in range(width)] for width in (11,13)}
    widths, duplicates, years, syntax = Counter(), Counter(), Counter(), Counter()
    orders = defaultdict(lambda: defaultdict(set))
    products = defaultdict(lambda: defaultdict(set))
    attributes = defaultdict(lambda: [set() for _ in range(7)])
    product_prices = defaultdict(set)
    user_genders = defaultdict(set)
    category_codes = defaultdict(set)
    code_categories = defaultdict(set)
    dates, calendar, date_issues = [], set(), 0
    blank = 0
    with source.open(encoding='utf-8', newline='') as stream:
        for line in stream:
            row = next(csv.reader([line], strict=True))
            if not row:
                blank += 1
                continue
            width = len(row)
            widths[width] += 1
            syntax[(width, line.count(','), line.count('"'), line.count(';'), line.count('\t'))] += 1
            duplicates[line.rstrip('\r\n')] += 1
            years[(row[0][:4],width)] += 1
            for i, value in enumerate(row): columns[width][i][value] += 1
            try:
                date = datetime.strptime(row[0], '%Y-%m-%d %H:%M:%S UTC')
                dates.append(date)
                calendar.add(date.date())
            except ValueError:
                date_issues += 1
            candidate_user = row[8] if width == 13 else row[6]
            orders[row[1]][width].add((row[0],candidate_user))
            products[row[2]][width].add(candidate_user)
            if width == 13:
                for k,i in enumerate([4,5,6,9,10,11,12]):
                    if row[i]: attributes[row[2]][k].add(row[i])
                product_prices[row[2]].add(row[7])
                if row[9]: user_genders[candidate_user].add(row[9])
                if row[5]:
                    category_codes[row[4]].add(row[5])
                    code_categories[row[5]].add(row[4])
    def describe(counter, position, width):
        nonempty = [v for v in counter if v]
        result = {'position':position, 'empty':counter[''], 'distinct_nonempty':len(nonempty),
                  'whitespace_only':sum(n for v,n in counter.items() if v and not v.strip()),
                  'literal_null_tokens':sum(n for v,n in counter.items() if v.lower() in ['null','none','nan','na','n/a']),
                  'digit_only_rows':sum(n for v,n in counter.items() if v.isascii() and v.isdigit()),
                  'length_range_nonempty':[min(map(len,nonempty)),max(map(len,nonempty))] if nonempty else None}
        # Only public-like low-cardinality domains, never identifiers.
        if (width==13 and position in [4,6,7,10,11,12,13]):
            result['domain_counts'] = dict(sorted(counter.items()))
        if (width,position) in [(13,8),(11,6)]:
            values = [Decimal(v) for v in nonempty]
            result['numeric_minmax'] = [str(min(values)),str(max(values))]
            result['zero_rows'] = sum(n for v,n in counter.items() if Decimal(v)==0)
            result['negative_rows'] = sum(n for v,n in counter.items() if Decimal(v)<0)
            result['nonfinite_rows'] = sum(n for v,n in counter.items() if not Decimal(v).is_finite())
            result['decimal2_rows'] = sum(n for v,n in counter.items() if len(v.split('.'))==2 and len(v.split('.')[1])==2)
        return result
    shared = [value for value in orders.values() if len(value)==2]
    long_users = set(columns[13][8]) - {''}
    short_users = set(columns[11][6]) - {''}
    missing_days=[]
    day=min(calendar)
    while day<=max(calendar):
        if day not in calendar: missing_days.append(str(day))
        day += timedelta(days=1)
    report_path=ROOT/'data/processed/normalization-v1/quality.json'
    metadata=json.loads(report_path.read_text(encoding='utf-8'))
    output_states=Counter(); output_records=0; output_widths=Counter(); null_cells=0; pending_aligned=0
    with (report_path.parent/'records.jsonl').open(encoding='utf-8') as stream:
        for line in stream:
            row=json.loads(line); output_records+=1
            output_states[row['validation_status']]+=1
            output_widths[row['original_field_count']]+=1
            null_cells += sum(v is None for v in row['original_fields'])
            if row['original_field_count']==11 and row['positional_fields_13'] is not None: pending_aligned+=1
    result={
        'source_sha256':before['data\\raw\\jewelry.csv'] if 'data\\raw\\jewelry.csv' in before else before['data/raw/jewelry.csv'],
        'source_bytes':source.stat().st_size, 'blank_lines':blank, 'rows':sum(widths.values()),'widths':dict(widths),
        'columns':{str(w):[describe(c,i+1,w) for i,c in enumerate(cs)] for w,cs in columns.items()},
        'syntax':[{'width_commas_quotes_semicolons_tabs':list(k),'rows':v} for k,v in syntax.items()],
        'year_width_rows':[[list(k),v] for k,v in sorted(years.items())],
        'date_range':[str(min(dates)),str(max(dates))],'date_parse_errors':date_issues,'missing_calendar_days':missing_days,
        'duplicate_groups':sum(n>1 for n in duplicates.values()),'duplicate_excess':sum(n-1 for n in duplicates.values()),
        'relations':{'candidate_orders_all':len(orders),'orders_with_multiple_date_user':sum(len(set().union(*v.values()))>1 for v in orders.values()),
                     'orders_shared_widths':len(shared),'shared_orders_same_date_user':sum(v[11]==v[13] for v in shared),
                     'product_ids_all':len(products),'products_shared_widths':sum(len(v)>1 for v in products.values()),
                     'users_long':len(long_users),'users_short':len(short_users),'users_intersection':len(long_users&short_users),
                     'short_rows_user_seen_long':sum(n for v,n in columns[11][6].items() if v in long_users),
                     'products_with_multiple_nonempty_attribute':dict(zip(['p5','p6','p7','p10','p11','p12','p13'],[sum(len(v[i])>1 for v in attributes.values()) for i in range(7)])),
                     'products_with_multiple_prices':sum(len(v)>1 for v in product_prices.values()),
                     'candidate_users_with_both_gender_codes':sum(len(v)>1 for v in user_genders.values()),
                     'category_ids_with_multiple_codes':sum(len(v)>1 for v in category_codes.values()),
                     'codes_with_multiple_category_ids':sum(len(v)>1 for v in code_categories.values()),
                     'category_ids_with_nonempty_code':len(category_codes)},
        'output':{'rows':output_records,'widths':dict(output_widths),'states':dict(output_states),
                  'null_cells_in_original_fields':null_cells,'short_rows_forced_alignment':pending_aligned,'quality':metadata},
        'protected_manifest_sha256':hashlib.sha256(json.dumps(before,sort_keys=True).encode()).hexdigest(),
        'protected_files':len(protected),
    }
    if before!={str(p.relative_to(ROOT)):digest(p) for p in protected}: raise RuntimeError('Archivos protegidos cambiaron')
    result['protected_files_unchanged']=True
    print(json.dumps(result,ensure_ascii=True,indent=2))


if __name__=='__main__': profile()
