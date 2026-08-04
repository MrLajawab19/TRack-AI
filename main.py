"""
Main entry point for AI-Powered Train Traffic Control System
"""

import uvicorn

if __name__ == "__main__":
    print("Starting AI-Powered Train Traffic Control System...")
    print("Dashboard:         http://localhost:8000")
    print("API Documentation: http://localhost:8000/docs")
    print("Health Check:      http://localhost:8000/api/health")

    # Pass the app as an import string so that --reload works correctly.
    uvicorn.run(
        "api.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


