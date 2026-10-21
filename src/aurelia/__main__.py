"""CLI de simulación sintética Aurelia; no procesa REES46 ni Olist."""
import argparse
from pathlib import Path
import sqlite3

from .contracts import encode
from .generator import generate
from .warehouse import build, inspect


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    gen = commands.add_parser('generate')
    gen.add_argument('--output', type=Path, required=True)
    gen.add_argument('--seed', type=int, default=42)
    gen.add_argument('--orders', type=int, default=30)
    gen.add_argument('--adverse', action='store_true')
    load = commands.add_parser('build')
    load.add_argument('--input', type=Path, required=True)
    load.add_argument('--database', type=Path, required=True)
    query = commands.add_parser('query')
    query.add_argument('--database', type=Path, required=True)
    query.add_argument('--query', choices=['summary','reconciliation','rejections'], default='summary')
    args = parser.parse_args()
    try:
        if args.command == 'generate':
            result = generate(args.output, args.seed, args.orders, args.adverse)
        elif args.command == 'build':
            result = build(args.input, args.database)
        else:
            result = inspect(args.database, args.query)
        print(encode(result))
        return 1 if result.get('status') == 'REJECTED' and args.command == 'build' else 0
    except (ValueError, OSError, UnicodeError, sqlite3.Error):
        parser.exit(1, 'Error: ejecución rechazada; revisar contrato, manifiesto, destino y permisos.\n')


if __name__ == '__main__':
    raise SystemExit(main())
