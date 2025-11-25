"""
Vercel Serverless Function for FastAPI Backend
This file serves as the entry point for all /api/* routes
"""
import sys
import os
import traceback
from pathlib import Path

# Print to stderr so it shows up in Vercel logs
def log_error(msg):
    try:
        print(f"ERROR: {msg}", file=sys.stderr, flush=True)
    except:
        pass

def log_info(msg):
    try:
        print(f"INFO: {msg}", file=sys.stderr, flush=True)
    except:
        pass

# Initialize handler to None - will be set below
handler = None
app = None

# Wrap everything in try-except to catch initialization errors
try:
    log_info("=== Starting API initialization ===")
    
    # Determine paths first (before any imports that might fail)
    try:
        current_file = Path(__file__).resolve()
        api_dir = current_file.parent
        project_root = api_dir.parent
        backend_dir = project_root / "backend"
        
        log_info(f"Current file: {current_file}")
        log_info(f"API dir: {api_dir}")
        log_info(f"Project root: {project_root}")
        log_info(f"Backend dir: {backend_dir}")
        log_info(f"Backend dir exists: {backend_dir.exists()}")
    except Exception as e:
        log_error(f"Path resolution failed: {e}")
        raise
    
    # Add paths to sys.path before importing
    try:
        backend_path_str = str(backend_dir)
        project_root_str = str(project_root)
        if backend_path_str not in sys.path:
            sys.path.insert(0, backend_path_str)
        if project_root_str not in sys.path:
            sys.path.insert(0, project_root_str)
        
        log_info(f"Python path (first 3): {sys.path[:3]}")
    except Exception as e:
        log_error(f"Path setup failed: {e}")
        raise
    
    # Now try to import server
    import_error = None
    
    try:
        log_info("Attempting to import server module...")
        # Try direct import first
        from server import app
        log_info("✅ Successfully imported server module")
    except ImportError as e:
        log_error(f"❌ Direct import failed: {e}")
        log_error(traceback.format_exc())
        try:
            # Try using importlib as fallback
            import importlib.util
            server_file = backend_dir / "server.py"
            
            log_info(f"Trying importlib fallback, server.py exists: {server_file.exists()}")
            
            if server_file.exists():
                spec = importlib.util.spec_from_file_location("server", server_file)
                if spec and spec.loader:
                    log_info("Loading server module via importlib...")
                    server_module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(server_module)
                    app = server_module.app
                    log_info("✅ Successfully loaded server module via importlib")
                else:
                    import_error = f"Failed to create spec from {server_file}"
                    log_error(import_error)
            else:
                import_error = f"server.py not found at {server_file}"
                log_error(import_error)
        except Exception as e2:
            import_error = f"Import error: {str(e)}, Fallback error: {str(e2)}"
            log_error(import_error)
            log_error(traceback.format_exc())
    except Exception as e:
        import_error = f"Unexpected error during import: {str(e)}"
        log_error(import_error)
        log_error(traceback.format_exc())
    
    # If import failed, create a minimal error app
    if app is None:
        log_error("⚠️ Creating fallback error app")
        try:
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
                    "project_root": str(project_root),
                    "python_path": sys.path[:5]
                }
            
            @app.get("/test-db")
            async def test_db():
                return {
                    "error": "Backend server not loaded",
                    "import_error": import_error
                }
            
            log_info("✅ Fallback error app created")
        except Exception as e:
            log_error(f"Failed to create fallback app: {e}")
            log_error(traceback.format_exc())
            raise
    
    # Create Mangum handler
    try:
        log_info("Creating Mangum handler...")
        from mangum import Mangum
        handler = Mangum(app, lifespan="off")
        log_info("✅ Mangum handler created successfully")
    except Exception as e:
        log_error(f"❌ Mangum initialization failed: {e}")
        log_error(traceback.format_exc())
        # If Mangum fails, create a minimal handler
        try:
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
            log_info("✅ Created fallback Mangum handler")
        except Exception as e2:
            log_error(f"Failed to create fallback handler: {e2}")
            log_error(traceback.format_exc())
            raise
    
    log_info("=== API initialization complete ===")
    
except Exception as e:
    # Ultimate fallback - if everything fails, create a minimal handler
    log_error(f"🔥 CRITICAL ERROR during initialization: {e}")
    log_error(traceback.format_exc())
    
    try:
        from fastapi import FastAPI
        from mangum import Mangum
        
        error_app = FastAPI()
        
        @error_app.get("/")
        async def root():
            return {
                "error": "Critical initialization error",
                "message": str(e),
                "traceback": traceback.format_exc()
            }
        
        handler = Mangum(error_app, lifespan="off")
        log_info("✅ Created critical error handler")
    except Exception as e2:
        log_error(f"🔥 Even critical error handler failed: {e2}")
        # Last resort - create absolute minimal handler
        # This should never fail unless FastAPI/Mangum aren't installed
        try:
            from fastapi import FastAPI
            from mangum import Mangum
            minimal_app = FastAPI()
            minimal_app.get("/")(lambda: {"error": "Handler initialization completely failed"})
            handler = Mangum(minimal_app, lifespan="off")
        except:
            # If this fails, Vercel will show the error
            pass

# CRITICAL: Ensure handler is always defined
if handler is None:
    log_error("🔥 Handler is None! Creating emergency handler...")
    try:
        from fastapi import FastAPI
        from mangum import Mangum
        emergency_app = FastAPI()
        
        @emergency_app.get("/")
        async def emergency():
            return {
                "error": "Handler was not initialized",
                "check_logs": "See Vercel function logs for details"
            }
        
        handler = Mangum(emergency_app, lifespan="off")
        log_info("✅ Emergency handler created")
    except Exception as e:
        log_error(f"🔥 Emergency handler creation failed: {e}")
        # This is the absolute last resort
        # Vercel will show an error if handler doesn't exist
        raise RuntimeError(f"Failed to create handler: {e}")

# Export handler for Vercel
# Vercel looks for 'handler' variable at module level
__all__ = ["handler"]
