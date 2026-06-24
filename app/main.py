import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, infrastructure, alerts, pipelines, costs, diagnostics, github, history

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — starts the metrics collector background job."""
    # Start background scheduler for metrics collection
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from app.jobs.metrics_collector import collect_and_store_metrics

        scheduler = BackgroundScheduler()
        scheduler.add_job(collect_and_store_metrics, "interval", minutes=5, id="metrics_collector")
        scheduler.start()
        logger.info("Background metrics collector started (every 5 minutes)")
    except Exception as e:
        # Don't crash the app if DB isn't available — degrade gracefully
        logger.warning(f"Could not start metrics collector: {e}")
        scheduler = None

    yield

    # Shutdown
    if scheduler:
        scheduler.shutdown(wait=False)


app = FastAPI(
    title="CloudPulse API",
    description="AWS infrastructure health and deployment monitoring",
    version="0.2.0",
    lifespan=lifespan,
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
app.include_router(github.router, prefix="/github")
app.include_router(history.router, prefix="/history")
