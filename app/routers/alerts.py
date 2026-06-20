from fastapi import APIRouter

router = APIRouter(tags=["alerts"])

@router.get("/")
def list_alerts():
    # TODO: integrate with CloudWatch alarms
    return {"alerts": []}
