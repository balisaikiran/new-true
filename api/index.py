"""
Vercel Serverless Function for FastAPI Backend
This file serves as the entry point for all /api/* routes
"""
from mangum import Mangum
import sys
import os
from pathlib import Path

# Determine paths
current_file = Path(__file__).resolve()
api_dir = current_file.parent
project_root = api_dir.parent
backend_dir = project_root / "backend"

# Add backend to Python path
backend_path_str = str(backend_dir)
if backend_path_str not in sys.path:
    sys.path.insert(0, backend_path_str)

# Try to import the FastAPI app
try:
    from server import app
except ImportError as e:
    # If import fails, try alternative import method
    import importlib.util
    
    server_file = backend_dir / "server.py"
    if server_file.exists():
        spec = importlib.util.spec_from_file_location("server", server_file)
        if spec and spec.loader:
            server_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(server_module)
            app = server_module.app
        else:
            raise ImportError(f"Could not load server.py: {e}")
    else:
        raise ImportError(f"server.py not found at {server_file}: {e}")

# Create Mangum handler for Vercel
# Mangum converts ASGI (FastAPI) to AWS Lambda/Vercel format
handler = Mangum(app, lifespan="off")
