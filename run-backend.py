import os
import sys
from pathlib import Path

# Set PYTHONPATH to 'backend' directory so uvicorn reloader child processes inherit it
backend_dir = Path(__file__).resolve().parent / "backend"
os.environ["PYTHONPATH"] = str(backend_dir)
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        reload_dirs=[str(backend_dir)],
    )
