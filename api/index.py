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
            # Create minimal app if import fails
            from fastapi import FastAPI
            app = FastAPI()
            @app.get("/")
            async def root():
                return {
                    "error": "Failed to import server",
                    "message": str(e),
                    "backend_path": str(backend_dir)
                }
    else:
        # Create minimal app if server.py not found
        from fastapi import FastAPI
        app = FastAPI()
        @app.get("/")
        async def root():
            return {
                "error": "server.py not found",
                "backend_path": str(backend_dir),
                "exists": server_file.exists()
            }

# Create Mangum handler for Vercel
# Mangum converts ASGI (FastAPI) to AWS Lambda/Vercel format
try:
    handler = Mangum(app, lifespan="off")
except Exception as e:
    # Fallback handler if Mangum fails
    from fastapi import FastAPI
    fallback_app = FastAPI()
    @fallback_app.get("/")
    async def root():
        return {"error": "Mangum initialization failed", "message": str(e)}
    handler = Mangum(fallback_app, lifespan="off")
