"""Auditoría local de solo lectura; biblioteca estándar; no exporta registros."""
import csv, hashlib, json, collections, datetime, decimal
from pathlib import Path

def audit():
    p = Path('data/raw/jewelry.csv')
    def digest():
        h = hashlib.sha256()
        with p.open('rb') as f:
            for b in iter(lambda: f.read(1024*1024), b''): h.update(b)
        return h.hexdigest()
    before = digest()
    widths = collections.Counter(); months = collections.Counter(); days=set()
    columns = [collections.Counter() for _ in range(13)]
    duplicate = collections.Counter(); keys=collections.Counter(); issues=collections.Counter()
    orders=collections.defaultdict(lambda: [set(),set()]); products=collections.defaultdict(lambda:[set() for _ in range(7)])
    users=collections.defaultdict(set); prices=[]; dates=[]; blocks={}; previous=None
    with p.open(encoding='utf-8-sig',newline='') as f:
        for line,r in enumerate(csv.reader(f,strict=True),1):
            widths[len(r)]+=1
            if not r: continue
            duplicate[hashlib.sha256(json.dumps(r).encode()).digest()]+=1
            blocks.setdefault(len(r),[line,line]); blocks[len(r)][1]=line
            if len(r)!=13: continue
            for i,v in enumerate(r): columns[i][v]+=1
            try:
                dt=datetime.datetime.strptime(r[0],'%Y-%m-%d %H:%M:%S UTC')
                dates.append(dt); months[dt.strftime('%Y-%m')]+=1; days.add(dt.date())
                if previous and dt<previous: issues['out_of_order_13']+=1
                previous=dt
            except ValueError: issues['invalid_date_13']+=1
            for i in [1,2,3,4,6,8]:
                if r[i] and (not r[i].isdigit()): issues[f'noninteger_col_{i+1}']+=1
            try:
                v=decimal.Decimal(r[7]); assert v.is_finite(); prices.append(v)
                if v<=0: issues['nonpositive_price_13']+=1
                if v.as_tuple().exponent < -2: issues['price_more_than_2_decimals']+=1
            except Exception: issues['invalid_price_13']+=1
            keys[(r[1],r[2])]+=1
            orders[r[1]][0].add(r[8]); orders[r[1]][1].add(r[0])
            users[r[8]].add(r[1])
            for j,i in enumerate([4,5,6,9,10,11,12]):
                if r[i]: products[r[2]][j].add(r[i])
    # Separate positional audit for short records; no automatic repair.
    short_dates=[]; short_prices=[]; short_numeric=collections.Counter(); short_keys=collections.Counter()
    with p.open(encoding='utf-8-sig',newline='') as f:
        for r in csv.reader(f,strict=True):
            if len(r)!=11: continue
            try: short_dates.append(datetime.datetime.strptime(r[0],'%Y-%m-%d %H:%M:%S UTC'))
            except ValueError: issues['invalid_date_11']+=1
            try: short_prices.append(decimal.Decimal(r[5]))
            except decimal.InvalidOperation: issues['invalid_numeric_col6_11']+=1
            for i in [1,2,3,6]:
                if not r[i].isdigit(): short_numeric[str(i+1)]+=1
            short_keys[(r[1],r[2])]+=1
    prices.sort(); dmin=min(dates); dmax=max(dates)
    result={'sha256_before':before,'sha256_after':digest(),'size_bytes':p.stat().st_size,'widths':dict(widths),'blocks_csv_record_numbers':blocks,
      'columns_13':[{'position':i+1,'empty':x[''],'distinct_nonempty':len(x)-int('' in x),'numeric_nonempty':sum(n for v,n in x.items() if v and v.isdigit()),'top_categorical':x.most_common(10) if i in [3,5,9,10,11,12] else None} for i,x in enumerate(columns)],
      'exact_duplicate_excess':sum(v-1 for v in duplicate.values()),'duplicate_groups':sum(v>1 for v in duplicate.values()),
      'dates_13':[str(dmin),str(dmax)],'months_13':dict(sorted(months.items())),'missing_days_13':(dmax.date()-dmin.date()).days+1-len(days),
      'issues':dict(issues),'price_13':{'min':str(prices[0]),'max':str(prices[-1]),'median':str(prices[len(prices)//2]),'sum':str(sum(prices)),'p99_nearest_rank':str(prices[(99*len(prices)+99)//100-1])},
      'candidate_orders_13':len(orders),'candidate_products_13':len(products),'candidate_users_13':len(users),'repeat_candidate_users_13':sum(len(x)>1 for x in users.values()),
      'order_product_duplicate_excess_13':sum(v-1 for v in keys.values()),'orders_multiple_users_13':sum(len(x[0])>1 for x in orders.values()),'orders_multiple_times_13':sum(len(x[1])>1 for x in orders.values()),
      'products_multiple_nonempty_attributes_13':{str(i+1):sum(len(v[i])>1 for v in products.values()) for i in range(7)},
      'short_date_range':[str(min(short_dates)),str(max(short_dates))],'short_col6_numeric_minmax':[str(min(short_prices)),str(max(short_prices))],'short_col6_zero':sum(x==0 for x in short_prices),'short_noninteger':dict(short_numeric),'short_key_duplicate_excess':sum(v-1 for v in short_keys.values())}
    print(json.dumps(result,ensure_ascii=False,indent=2))

if __name__=='__main__': audit()
