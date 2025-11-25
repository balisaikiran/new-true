"""
Netlify Serverless Function for FastAPI Backend
This file serves as the entry point for all /api/* routes on Netlify
"""
import sys
import os
import traceback
from pathlib import Path

# Initialize handler to None - will be set below
mangum_handler = None

# Determine paths for Netlify
try:
    current_file = Path(__file__).resolve()
    function_dir = current_file.parent
    netlify_dir = function_dir.parent.parent
    project_root = netlify_dir.parent
    backend_dir = project_root / "backend"
    
    # Debug: Print paths (will show in Netlify logs)
    print(f"Current file: {current_file}")
    print(f"Function dir: {function_dir}")
    print(f"Netlify dir: {netlify_dir}")
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

# Wrap everything in try-except to prevent crashes
try:
    # Add error handling for imports
    try:
        from mangum import Mangum
    except ImportError as e:
        print(f"ERROR: Failed to import mangum: {e}")
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

    # Create Mangum handler for Netlify
    # Mangum converts ASGI (FastAPI) to AWS Lambda/Netlify format
    try:
        print("Creating Mangum handler...")
        mangum_handler = Mangum(app, lifespan="off", log_level="info")
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
        mangum_handler = handler
        print("Created fallback Mangum handler")

    # Handler is ready - Mangum will handle async execution
    # Global exception handler in FastAPI will catch all errors
    print("✅ Netlify function handler ready")

except Exception as e:
    # If ANYTHING fails during initialization, create a minimal error handler
    print(f"CRITICAL ERROR during initialization: {e}")
    print(traceback.format_exc())
    
    # Create minimal error handler (try to import mangum, but don't fail if it doesn't work)
    try:
        from fastapi import FastAPI
        from mangum import Mangum
        
        error_app = FastAPI()
        
        @error_app.get("/")
        @error_app.post("/")
        @error_app.get("/{path:path}")
        @error_app.post("/{path:path}")
        async def error_handler(path: str = ""):
            return {
                "error": {
                    "code": "500",
                    "message": f"Initialization error: {str(e)}",
                    "type": type(e).__name__
                }
            }
        
        handler = Mangum(error_app, lifespan="off")
        mangum_handler = handler
        print("Created error handler app")
    except Exception as e2:
        # Even error handler failed - create a simple lambda-compatible handler
        print(f"ERROR: Failed to create error handler: {e2}")
        def simple_handler(event, context):
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": '{"error": {"code": "500", "message": "Initialization failed"}}'
            }
        mangum_handler = simple_handler
        print("Created simple error handler")

# Ensure handler is always defined
if mangum_handler is None:
    print("WARNING: Handler is None, creating emergency handler")
    def emergency_handler(event, context):
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": {"code": "500", "message": "Handler not initialized"}}'
        }
    mangum_handler = emergency_handler

# Netlify Functions handler
# This is the entry point that Netlify will call
def handler(event, context):
    """Netlify Functions entry point"""
    try:
        # Call the Mangum handler
        if mangum_handler is None:
            return {
                "statusCode": 500,
                "headers": {"Content-Type": "application/json"},
                "body": '{"error": {"code": "500", "message": "Handler not initialized"}}'
            }
        
        # Mangum handler handles async internally - just call it
        return mangum_handler(event, context)
    except Exception as e:
        print(f"ERROR in handler: {e}")
        print(traceback.format_exc())
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": f'{{"error": {{"code": "500", "message": "{str(e)}"}}}}'
        }

