from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from routers import analytics, anomalies, stats, notifications, composite

# Load environment variables
load_dotenv()

app = FastAPI(
    title="Gaming Analytics API",
    description="API for gaming dashboard analytics and anomaly detection",
    version="1.0.0"
)

# Configure CORS
origins = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins[0] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(analytics.router, prefix="/api/analytics", tags=["analytics"])
app.include_router(anomalies.router, prefix="/api/anomalies", tags=["anomalies"])
app.include_router(stats.router, prefix="/api/stats", tags=["stats"])
app.include_router(notifications.router, prefix="/api/notifications", tags=["notifications"])
app.include_router(composite.router, prefix="/api/composite", tags=["composite"])

@app.get("/")
async def root():
    return {
        "message": "Gaming Analytics API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    uvicorn.run("main:app", host=host, port=port, reload=True)
