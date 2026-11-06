"""
Launcher for Chamba AI - Community Edition Web Server.
"""

import sys
import os

# Ensure safe UTF-8 output on Windows consoles
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

import uvicorn
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    print("=" * 65)
    print("  [+] CHAMBA AI - COMMUNITY EDITION (Open Source)")
    print("  Scraping en LinkedIn, Matching con IA & CV ATS Harvard")
    print(f"  Servidor web listo en: http://localhost:{port}")
    print("=" * 65)
    uvicorn.run("web.server:app", host="0.0.0.0", port=port, reload=True)
