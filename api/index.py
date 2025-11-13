"""
Vercel Serverless Function for FastAPI Backend
This file serves as the entry point for all /api/* routes
"""
import sys
import os
from pathlib import Path

# Determine paths first (before any imports that might fail)
current_file = Path(__file__).resolve()
api_dir = current_file.parent
project_root = api_dir.parent
backend_dir = project_root / "backend"

# Add paths to sys.path before importing
backend_path_str = str(backend_dir)
project_root_str = str(project_root)
if backend_path_str not in sys.path:
    sys.path.insert(0, backend_path_str)
if project_root_str not in sys.path:
    sys.path.insert(0, project_root_str)

# Now try to import
app = None
import_error = None

try:
    # Try direct import first
    from server import app
except ImportError:
    try:
        # Try using importlib as fallback
        import importlib.util
        server_file = backend_dir / "server.py"
        
        if server_file.exists():
            spec = importlib.util.spec_from_file_location("server", server_file)
            if spec and spec.loader:
                server_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(server_module)
                app = server_module.app
        else:
            import_error = f"server.py not found at {server_file}"
    except Exception as e:
        import_error = str(e)

# If import failed, create a minimal error app
if app is None:
    from fastapi import FastAPI
    app = FastAPI()
    
    @app.get("/")
    async def root():
        return {
            "error": "Failed to import backend server",
            "message": import_error or "Unknown import error",
            "backend_path": str(backend_dir),
            "backend_exists": backend_dir.exists(),
            "current_file": str(current_file),
            "api_dir": str(api_dir),
            "project_root": str(project_root)
        }
    
    @app.get("/test-db")
    async def test_db():
        return {
            "error": "Backend server not loaded",
            "import_error": import_error
        }

# Create Mangum handler
try:
    from mangum import Mangum
    handler = Mangum(app, lifespan="off")
except Exception as e:
    # If Mangum fails, create a minimal handler
    from fastapi import FastAPI
    from mangum import Mangum
    fallback_app = FastAPI()
    
    @fallback_app.get("/")
    async def root():
        return {
            "error": "Mangum initialization failed",
            "message": str(e),
            "app_loaded": app is not None
        }
    
    handler = Mangum(fallback_app, lifespan="off")

# Export handler for Vercel
__all__ = ["handler"]
