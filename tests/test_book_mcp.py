"""Exercise the actual stdio protocol and image blocks using a synthetic PDF."""
import asyncio
import base64
import json
import os
from pathlib import Path
import sys

from mcp import Client
from mcp.client.stdio import StdioServerParameters

from test_book_rag import book


def test_stdio_tools_and_images(book, tmp_path):
    book.index(keyword_only=True)
    config = tmp_path / 'rag.json'
    config.write_text(json.dumps({'pdf': str(book.config.pdf), 'model': str(book.config.model),
                                 'index': str(book.config.index), 'cache': str(book.config.cache)}))
    launcher = Path(__file__).resolve().parents[1] / 'scripts/book_mcp.py'

    async def exercise():
        params = StdioServerParameters(command=sys.executable, args=[str(launcher)], cwd=tmp_path,
                                       env={**os.environ, 'TECHCODEX_RAG_CONFIG': str(config)})
        async with Client(params) as client:
            tools = await client.list_tools()
            assert {t.name for t in tools.tools} == {'search_book','read_book_pages','get_page_image','book_status'}
            status = await client.call_tool('book_status', {})
            assert not status.is_error
            assert status.structured_content['text_device']['loaded'] is False
            result = await client.call_tool('search_book', {'query':'Fig. 6.14', 'mode':'keyword'})
            assert not result.is_error and result.structured_content['hits'][0]['pdf_page'] == 1
            original = await client.call_tool('read_book_pages', {'start_page':1,'count':2})
            assert len(original.structured_content['pages']) == 2
            image = await client.call_tool('get_page_image', {'pdf_page':1})
            assert not image.is_error
            blocks = [b for b in image.content if b.type == 'image']
            assert len(blocks) == 1 and base64.b64decode(blocks[0].data).startswith(b'\x89PNG')
            too_many = await client.call_tool('read_book_pages', {'start_page':1,'count':4})
            assert too_many.is_error
    asyncio.run(exercise())
