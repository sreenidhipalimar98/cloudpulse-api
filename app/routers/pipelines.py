from fastapi import APIRouter

router = APIRouter(tags=["pipelines"])

@router.get("/")
def list_pipelines():
    # TODO: integrate with CodePipeline / GitHub Actions API
    return {"pipelines": []}
