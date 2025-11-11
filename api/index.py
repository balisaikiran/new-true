"""
Vercel Serverless Function for FastAPI Backend
This file serves as the entry point for all /api/* routes
"""
import sys
import os
import traceback
from pathlib import Path

# Add error handling for imports
try:
    from mangum import Mangum
except ImportError as e:
    print(f"ERROR: Failed to import mangum: {e}")
    raise

# Determine paths - handle both local and Vercel environments
try:
    current_file = Path(__file__).resolve()
    api_dir = current_file.parent
    project_root = api_dir.parent
    backend_dir = project_root / "backend"
    
    # Debug: Print paths (will show in Vercel logs)
    print(f"Current file: {current_file}")
    print(f"API dir: {api_dir}")
    print(f"Project root: {project_root}")
    print(f"Backend dir: {backend_dir}")
    print(f"Backend dir exists: {backend_dir.exists()}")
    
    # Add backend to Python path
    backend_path_str = str(backend_dir)
    if backend_path_str not in sys.path:
        sys.path.insert(0, backend_path_str)
        print(f"Added to sys.path: {backend_path_str}")
    
    print(f"Python path: {sys.path[:3]}")
    
except Exception as e:
    print(f"ERROR: Path resolution failed: {e}")
    print(traceback.format_exc())
    raise

# Try to import the FastAPI app
app = None
try:
    print("Attempting to import server module...")
    from server import app
    print("✅ Successfully imported server module")
except ImportError as e:
    print(f"ERROR: Failed to import server: {e}")
    print(traceback.format_exc())
    
    # Try alternative import method
    try:
        import importlib.util
        server_file = backend_dir / "server.py"
        print(f"Trying alternative import from: {server_file}")
        print(f"File exists: {server_file.exists()}")
        
        if server_file.exists():
            spec = importlib.util.spec_from_file_location("server", server_file)
            if spec and spec.loader:
                server_module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(server_module)
                app = server_module.app
                print("✅ Successfully imported via importlib")
            else:
                raise Exception("Failed to create module spec")
        else:
            raise Exception(f"server.py not found at {server_file}")
    except Exception as e2:
        print(f"ERROR: Alternative import also failed: {e2}")
        print(traceback.format_exc())
        # Create minimal app for debugging
        from fastapi import FastAPI
        app = FastAPI()
        @app.get("/")
        async def root():
            return {
                "error": "Failed to import server",
                "import_error": str(e),
                "alternative_error": str(e2),
                "backend_path": str(backend_dir),
                "backend_exists": backend_dir.exists() if backend_dir else False
            }
        print("Created fallback FastAPI app")

if app is None:
    raise Exception("Failed to create FastAPI app")

# Create Mangum handler for Vercel
# Mangum converts ASGI (FastAPI) to AWS Lambda/Vercel format
try:
    print("Creating Mangum handler...")
    handler = Mangum(app, lifespan="off")
    print("✅ Mangum handler created successfully")
except Exception as e:
    print(f"ERROR: Mangum initialization failed: {e}")
    print(traceback.format_exc())
    # Fallback handler if Mangum fails
    from fastapi import FastAPI
    fallback_app = FastAPI()
    @fallback_app.get("/")
    async def root():
        return {"error": "Mangum initialization failed", "message": str(e)}
    handler = Mangum(fallback_app, lifespan="off")
    print("Created fallback Mangum handler")
