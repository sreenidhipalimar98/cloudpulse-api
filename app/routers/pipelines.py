from fastapi import APIRouter, Query
import httpx
import logging
import os

router = APIRouter(tags=["pipelines"])
logger = logging.getLogger(__name__)

GITHUB_OWNER = "sreenidhipalimar98"
CI_REPOS = ["cloudpulse-api", "CloudPulse-Terraform"]
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")

STATUS_MAP = {
    "completed": "healthy",
    "success": "healthy",
    "in_progress": "degraded",
    "queued": "degraded",
    "failure": "critical",
    "cancelled": "unknown",
    "skipped": "unknown",
}


def _github_headers():
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "CloudPulse-API",
    }
    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"
    return headers


@router.get("/")
def list_pipelines(limit: int = Query(default=15, le=30)):
    """Fetch recent GitHub Actions workflow runs across CI/CD repos."""
    all_runs = []

    for repo in CI_REPOS:
        try:
            url = f"https://api.github.com/repos/{GITHUB_OWNER}/{repo}/actions/runs"
            params = {"per_page": limit, "branch": "develop"}
            resp = httpx.get(url, params=params, headers=_github_headers(), timeout=10)

            if resp.status_code == 200:
                for run in resp.json().get("workflow_runs", []):
                    conclusion = run.get("conclusion") or run.get("status", "unknown")
                    all_runs.append({
                        "id": run["id"],
                        "name": f"{repo}: {run['name']}",
                        "repo": repo,
                        "status": STATUS_MAP.get(conclusion, "unknown"),
                        "conclusion": conclusion,
                        "commit": run["head_sha"][:8],
                        "branch": run["head_branch"],
                        "author": run["head_commit"]["author"]["name"] if run.get("head_commit") else "unknown",
                        "message": run["head_commit"]["message"].split("\n")[0] if run.get("head_commit") else "",
                        "started_at": run.get("run_started_at"),
                        "url": run["html_url"],
                        "duration_seconds": _calc_duration(run),
                    })
        except Exception as e:
            logger.warning(f"Could not fetch workflow runs for {repo}: {e}")

    all_runs.sort(key=lambda x: x.get("started_at") or "", reverse=True)
    return {"pipelines": all_runs[:limit]}


def _calc_duration(run):
    try:
        if run.get("updated_at") and run.get("run_started_at"):
            from datetime import datetime
            start = datetime.fromisoformat(run["run_started_at"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
            return int((end - start).total_seconds())
    except Exception:
        pass
    return None
