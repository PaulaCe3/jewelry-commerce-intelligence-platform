"""Medición reproducible en procesos nuevos; temporales fuera de salidas oficiales."""
import argparse
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
import time

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
sys.path.insert(0,str(ROOT/'tests'))


def peak_memory():
    if sys.platform=='win32':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_=[('cb',wintypes.DWORD),('PageFaultCount',wintypes.DWORD)] + [
                (name,ctypes.c_size_t) for name in ['PeakWorkingSetSize','WorkingSetSize','QuotaPeakPagedPoolUsage',
                'QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage','QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage']]
        kernel=ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetCurrentProcess.restype=wintypes.HANDLE
        api=ctypes.WinDLL('psapi',use_last_error=True)
        api.GetProcessMemoryInfo.argtypes=[wintypes.HANDLE,ctypes.POINTER(Counters),wintypes.DWORD]
        api.GetProcessMemoryInfo.restype=wintypes.BOOL
        counters=Counters(); counters.cb=ctypes.sizeof(counters)
        if not api.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb):
            raise ctypes.WinError(ctypes.get_last_error())
        return {'metric':'PeakWorkingSetSize','bytes':counters.PeakWorkingSetSize}
    import resource
    value=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return {'metric':'ru_maxrss','bytes':int(value if sys.platform=='darwin' else value*1024)}


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--runs',type=int,default=3)
    parser.add_argument('--worker',type=Path,help=argparse.SUPPRESS)
    args=parser.parse_args()
    source=ROOT/'data/raw/jewelry.csv'
    if args.worker:
        from normalize_jewelry import normalize
        started=time.perf_counter()
        normalize(source,args.worker,check_audit=True)
        elapsed=time.perf_counter()-started
        print(json.dumps({'wall_seconds':elapsed,'peak_process_memory':peak_memory()}))
        return
    if args.runs<1: parser.error('--runs debe ser positivo')
    from independent_checks import validate_output,digest_file
    official=ROOT/'data/processed/normalization-v1'
    protected=[source,official/'records.jsonl',official/'quality.json']
    before={str(p):digest_file(p) for p in protected}
    samples=[]
    with tempfile.TemporaryDirectory(prefix='plathel-benchmark-') as temporary:
        temp_root=Path(temporary)
        for index in range(args.runs):
            dest=temp_root/f'run-{index+1}'
            result=subprocess.run([sys.executable,'-B',str(Path(__file__).resolve()),'--worker',str(dest)],
                                  capture_output=True,text=True,encoding='utf-8',timeout=180,check=True)
            sample=json.loads(result.stdout)
            validate_output(source,dest,audit_checked=True)
            for name in ['records.jsonl','quality.json']:
                if digest_file(dest/name)!=digest_file(official/name):
                    raise AssertionError('Salida distinta del baseline oficial')
            samples.append(sample)
    if before!={str(p):digest_file(p) for p in protected}: raise AssertionError('Archivo protegido alterado')
    print(json.dumps({'python':sys.version,'platform':platform.platform(),'runs':samples,
                      'source_sha256':before[str(source)],'official_records_sha256':before[str(official/'records.jsonl')],
                      'official_quality_sha256':before[str(official/'quality.json')],
                      'independent_validation':'all records and report fields verified for each run',
                      'protected_files_unchanged':True,'temporaries_removed':not temp_root.exists()},indent=2))


if __name__=='__main__': main()
