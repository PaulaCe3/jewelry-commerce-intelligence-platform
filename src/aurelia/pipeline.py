"""Orquestación local atómica de Aurelia v2 + contrato de consumo v1."""
import argparse
from contextlib import closing
import csv
import os
from pathlib import Path
import sqlite3
import tempfile

from . import analytics,v2,warehouse
from .contracts import ROOT,encode,parse_json,safe_destination,sha256

VERSION='aurelia-local-pipeline-v1'


def inventory(directory):
    directory=Path(directory)
    files={}
    for p in sorted(directory.rglob('*')):
        if p.is_symlink():raise ValueError('No se admiten symlinks en artefactos.')
        if p.is_file() and p.relative_to(directory).as_posix()!='run_manifest.json':
            files[p.relative_to(directory).as_posix()]=sha256(p)
    return files


def verify(directory):
    if Path(directory).is_symlink():raise ValueError('Destino symlink no admitido.')
    directory=Path(directory).resolve()
    manifest=parse_json((directory/'run_manifest.json').read_text(encoding='utf-8'))
    if type(manifest) is not dict or set(manifest)!={'pipeline_version','status','synthetic','seed','orders','validation','exports','files'}:
        raise ValueError('Manifiesto de ejecución incompatible.')
    if manifest['pipeline_version']!=VERSION or manifest['status']!='COMPLETE' or manifest['synthetic'] is not True:
        raise ValueError('Ejecución no aceptada.')
    if any(type(manifest[k]) is not dict for k in ('files','exports','validation')):
        raise ValueError('Estructuras de manifiesto incompatibles.')
    if type(manifest['seed']) is not int or type(manifest['orders']) is not int:
        raise ValueError('Configuración de manifiesto incompatible.')
    expected_files={'warehouse.sqlite','inputs/manifest.json','inputs/returns.jsonl','inputs/refunds.jsonl',
                    'inputs/base/manifest.json','inputs/base/orders.jsonl','inputs/base/items.jsonl','inputs/base/payments.jsonl'}
    expected_files.update('exports/'+name+'.csv' for name in analytics.VIEWS)
    if set(manifest['files'])!=expected_files:raise ValueError('Inventario del paquete incompatible.')
    if manifest['files']!=inventory(directory):raise ValueError('Artefactos incompletos o alterados.')
    source_manifest,_,_=v2.inputs(directory/'inputs')
    if source_manifest['seed']!=manifest['seed']:
        raise ValueError('Semilla no coincide con entradas.')
    base_manifest=parse_json((directory/'inputs/base/manifest.json').read_text(encoding='utf-8'))
    if base_manifest['order_count_requested']!=manifest['orders']:
        raise ValueError('Cantidad solicitada incompatible.')
    with closing(warehouse.read_only(directory/'warehouse.sqlite')) as db:
        if db.execute('SELECT status FROM batch').fetchone()!=('ACCEPTED',) or db.execute('SELECT status FROM adjustment_batch').fetchone()!=('ACCEPTED',):
            raise ValueError('Fuente o ajustes no aceptados.')
    validation=analytics.validate(directory/'warehouse.sqlite',directory/'inputs')
    if validation!=manifest['validation']:raise ValueError('Resultados de aceptación incompatibles.')
    analytics.validate_exports(directory/'warehouse.sqlite',directory/'exports')
    for name,(_,columns) in analytics.VIEWS.items():
        spec=manifest['exports'].get(name)
        expected={'file':name+'.csv','rows':validation['row_counts'][name],
                  'columns':list(columns),'key':analytics.VIEWS[name][0].split(','),
                  'sha256':sha256(directory/'exports'/(name+'.csv'))}
        if spec!=expected:raise ValueError('Contrato de exportación incompatible.')
    if set(manifest['exports'])!=set(analytics.VIEWS):raise ValueError('Inventario de exportaciones incompatible.')
    return {'status':'PASSED','synthetic':True,'row_counts':validation['row_counts']}


def _construct(staging,seed,orders):
    v2.generate(staging/'inputs',seed,orders)
    result=v2.build(staging/'inputs',staging/'warehouse.sqlite')
    if result['status']!='ACCEPTED':raise ValueError('Lote rechazado: no publicar consumo.')
    analytics.install(staging/'warehouse.sqlite')
    validation=analytics.validate(staging/'warehouse.sqlite',staging/'inputs')
    exports=analytics.export(staging/'warehouse.sqlite',staging/'exports')
    analytics.validate_exports(staging/'warehouse.sqlite',staging/'exports')
    manifest={'pipeline_version':VERSION,'status':'COMPLETE','synthetic':True,'seed':seed,'orders':orders,
              'validation':validation,'exports':exports,'files':inventory(staging)}
    with (staging/'run_manifest.json').open('x',encoding='utf-8',newline='\n') as f:
        f.write(encode(manifest)+'\n');f.flush();os.fsync(f.fileno())
    verify(staging)


def run(output,seed=42,orders=30):
    original=Path(output)
    if original.is_symlink():raise ValueError('Destino symlink no admitido.')
    output=safe_destination(original)
    if ROOT in output.parents and ROOT/'data/aurelia' not in output.parents:
        raise ValueError('Dentro del repositorio, generar únicamente bajo data/aurelia para conservar exclusiones.')
    if type(seed) is not int or not 0<=seed<2**32 or type(orders) is not int or not 6<=orders<=10000:
        raise ValueError('Semilla uint32 y pedidos 6..10000 requeridos.')
    output.parent.mkdir(parents=True,exist_ok=True)
    lock=output.parent/('.aurelia-'+output.name+'.lock')
    # No se espera ni elimina un bloqueo ajeno: resolver explícitamente una ejecución interrumpida.
    descriptor=os.open(lock,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    os.close(descriptor)
    try:
        existed=output.exists()
        if existed:verify(output)
        with tempfile.TemporaryDirectory(prefix='.aurelia-',dir=output.parent) as work:
            staging=Path(work)/'bundle';staging.mkdir()
            _construct(staging,seed,orders)
            if existed:
                a=parse_json((staging/'run_manifest.json').read_text(encoding='utf-8'))
                b=parse_json((output/'run_manifest.json').read_text(encoding='utf-8'))
                # Incluye todos los hashes, configuración, contratos y conteos: no confiar en solo seed.
                if a!=b:raise ValueError('Destino existente distinto: elegir otra ruta.')
                status='unchanged'
            else:
                if output.exists():raise FileExistsError('Destino apareció durante ejecución.')
                os.rename(staging,output)
                status='success'
        return {'status':status,'synthetic':True,'pipeline_version':VERSION,
                'seed':seed,'orders':orders,'row_counts':verify(output)['row_counts']}
    finally:
        lock.unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    execute=commands.add_parser('run');execute.add_argument('--output',type=Path,required=True);execute.add_argument('--seed',type=int,default=42);execute.add_argument('--orders',type=int,default=30)
    check=commands.add_parser('verify');check.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    try:
        result=run(args.output,args.seed,args.orders) if args.command=='run' else verify(args.output)
        print(encode(result));return 0
    except (ValueError,OSError,UnicodeError,sqlite3.Error,KeyError,TypeError,csv.Error):
        parser.exit(1,'Error: ejecución no aceptada; comprobar contrato, integridad, destino, bloqueo y permisos.\n')


if __name__=='__main__':raise SystemExit(main())
