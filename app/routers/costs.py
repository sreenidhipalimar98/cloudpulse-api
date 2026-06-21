from fastapi import APIRouter
from datetime import datetime, timedelta
import boto3
import logging
from app.core.config import settings

router = APIRouter(tags=["costs"])
logger = logging.getLogger(__name__)


@router.get("/summary")
def get_cost_summary():
    """Get current month's total spend."""
    try:
        client = boto3.client("ce", region_name="us-east-1")  # CE API is only in us-east-1
        today = datetime.utcnow().date()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()

        response = client.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
        )

        total = 0.0
        for result in response.get("ResultsByTime", []):
            total += float(result["Total"]["UnblendedCost"]["Amount"])

        return {
            "total_cost": round(total, 2),
            "currency": "USD",
            "period": f"{start} to {end}",
            "status": "healthy" if total < 50 else "degraded" if total < 100 else "critical",
        }
    except Exception as e:
        logger.error(f"Cost summary failed: {e}")
        return {"total_cost": 0, "currency": "USD", "period": "unknown", "status": "unknown", "error": str(e)}


@router.get("/by-service")
def get_cost_by_service():
    """Get current month's cost breakdown by AWS service."""
    try:
        client = boto3.client("ce", region_name="us-east-1")
        today = datetime.utcnow().date()
        start = today.replace(day=1).isoformat()
        end = today.isoformat()

        response = client.get_cost_and_usage(
            TimePeriod={"Start": start, "End": end},
            Granularity="MONTHLY",
            Metrics=["UnblendedCost"],
            GroupBy=[{"Type": "DIMENSION", "Key": "SERVICE"}],
        )

        services = []
        for result in response.get("ResultsByTime", []):
            for group in result.get("Groups", []):
                service_name = group["Keys"][0]
                amount = float(group["Metrics"]["UnblendedCost"]["Amount"])
                if amount > 0.001:  # skip near-zero services
                    services.append({
                        "name": service_name,
                        "cost": round(amount, 2),
                        "currency": "USD",
                    })

        services.sort(key=lambda x: x["cost"], reverse=True)
        return {"services": services, "period": f"{start} to {end}"}
    except Exception as e:
        logger.error(f"Cost by service failed: {e}")
        return {"services": [], "period": "unknown", "error": str(e)}
