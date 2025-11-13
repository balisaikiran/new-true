"""
Simple test handler to verify Vercel Python functions work
This doesn't import server.py - just returns a simple response
"""
from fastapi import FastAPI
from mangum import Mangum

app = FastAPI()

@app.get("/")
async def root():
    return {
        "message": "Simple test handler works!",
        "status": "ok"
    }

handler = Mangum(app, lifespan="off")

