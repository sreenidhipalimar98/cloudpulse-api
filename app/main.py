from fastapi import FastAPI
from app.routers import health, infrastructure, alerts, pipelines

app = FastAPI(
    title="CloudPulse API",
    description="AWS infrastructure health and deployment monitoring",
    version="0.1.0",
)

app.include_router(health.router)
app.include_router(infrastructure.router, prefix="/infrastructure")
app.include_router(pipelines.router, prefix="/pipelines")
app.include_router(alerts.router, prefix="/alerts")
