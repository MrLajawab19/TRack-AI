"""
Main entry point for AI-Powered Train Traffic Control System
"""

import uvicorn
from api.main import app

if __name__ == "__main__":
    print("🚂 Starting AI-Powered Train Traffic Control System...")
    print("📊 Dashboard will be available at: http://localhost:8000")
    print("📖 API Documentation at: http://localhost:8000/docs")
    print("🔧 Health Check at: http://localhost:8000/api/health")
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        reload=True,
        log_level="info"
    )
