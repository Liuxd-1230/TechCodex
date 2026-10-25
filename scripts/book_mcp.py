"""Launch from a uv-managed RAG interpreter; no sync or model load at startup."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from rag.mcp_server import main

if __name__ == '__main__':
    main()
