"""Explicit local indexing, retrieval and Codex MCP registration."""
import argparse
import json
import logging
from pathlib import Path
import subprocess
import sys

from .book import Book
from .config import Config, ROOT


def main():
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
    logging.basicConfig(level=logging.INFO, stream=sys.stderr, format='%(levelname)s %(message)s')
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    commands.add_parser('status')
    cloud = commands.add_parser('import-ocr', help='Import a private MinerU cloud JSON export')
    cloud.add_argument('export', type=Path)
    cloud.add_argument('--split-pdf', type=Path, required=True)
    cloud.add_argument('--start', type=int, required=True, help='First page in the original PDF (one-based)')
    ocr = commands.add_parser('ocr', help='Explicit local OCR for selected scanned pages')
    ocr.add_argument('--start', type=int, required=True)
    ocr.add_argument('--end', type=int, required=True)
    ocr.add_argument('--tier', choices=['basic','standard','advanced'], default='basic')
    ocr.add_argument('--reason', default='')
    index = commands.add_parser('index')
    index.add_argument('--keyword-only', action='store_true')
    images = commands.add_parser('index-images')
    images.add_argument('pages', type=int, nargs='+')
    search = commands.add_parser('search')
    search.add_argument('query')
    search.add_argument('--chapter')
    search.add_argument('--mode', choices=['hybrid','keyword','semantic','visual'], default='hybrid')
    search.add_argument('--top-k', type=int, default=5)
    read = commands.add_parser('read')
    read.add_argument('page', type=int)
    read.add_argument('--count', type=int, default=1)
    image = commands.add_parser('image')
    image.add_argument('page', type=int)
    commands.add_parser('install-mcp')
    args = parser.parse_args()
    if args.command == 'install-mcp':
        import os
        config = Path(os.environ.get('TECHCODEX_RAG_CONFIG', ROOT / '.local/rag.json')).resolve()
        subprocess.run(['codex', 'mcp', 'add', 'techcodex_book', '--env', f'TECHCODEX_RAG_CONFIG={config}',
                        '--', sys.executable, str(ROOT / 'scripts/book_mcp.py')], check=True)
        return
    book = Book(Config.load())
    if args.command == 'import-ocr':
        from .import_ocr import import_cloud_ocr
        result = import_cloud_ocr(book, args.export, args.split_pdf, args.start)
    elif args.command == 'ocr':
        from .ocr import ocr_pages
        result = ocr_pages(book,args.start,args.end,args.tier,args.reason)
    elif args.command == 'status':
        result = book.status()
    elif args.command == 'index':
        result = book.index(args.keyword_only)
    elif args.command == 'index-images':
        result = book.index_images(args.pages)
    elif args.command == 'search':
        result = book.search(args.query, args.chapter, args.top_k, args.mode)
    elif args.command == 'read':
        result = book.read_pages(args.page, args.count)
    else:
        result = {'page_image': str(book.page_image(args.page))}
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
