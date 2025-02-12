from typing import Union

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
from logging.handlers import RotatingFileHandler
import uvicorn
import gc
import psutil
import os

from fin_advisor_llm_api.app.api.routes import router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Add rotating file handler to prevent large log files
handler = RotatingFileHandler(
    'app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5
)
logger.addHandler(handler)

app = FastAPI()

# Add middleware to track request counts
@app.middleware("http")
async def log_and_monitor_requests(request, call_next):
    try:
        response = await call_next(request)
        # Log memory usage periodically
        process = psutil.Process(os.getpid())
        logger.info(f"Memory usage: {process.memory_info().rss / 1024 / 1024} MB")
        return response
    except Exception as e:
        logger.error(f"Request failed: {str(e)}")
        raise

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"Hello": "World"}

app.include_router(router)

# Health check endpoint
@app.get("/health")
def health_check():
    return {"status": "healthy"}

# This is only used when running with `python main.py`
if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8002)
