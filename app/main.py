from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, infrastructure, alerts, pipelines, costs, diagnostics

app = FastAPI(
    title="CloudPulse API",
    description="AWS infrastructure health and deployment monitoring",
    version="0.1.0",
)

# Allow the Amplify-hosted UI (and localhost for dev) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Tighten to your Amplify URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(infrastructure.router, prefix="/infrastructure")
app.include_router(pipelines.router, prefix="/pipelines")
app.include_router(alerts.router, prefix="/alerts")
app.include_router(costs.router, prefix="/costs")
app.include_router(diagnostics.router, prefix="/diagnostics")
