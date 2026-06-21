from fastapi import APIRouter, Query
import httpx
import logging

router = APIRouter(tags=["github"])
logger = logging.getLogger(__name__)

GITHUB_OWNER = "sreenidhipalimar98"
REPOS = ["cloudpulse-api", "cloudpulse-ui", "CloudPulse-Terraform"]


@router.get("/commits")
def get_recent_commits(branch: str = Query(default="develop"), limit: int = Query(default=10, le=30)):
    """Get recent commits across all CloudPulse repos from GitHub."""
    all_commits = []

    for repo in REPOS:
        try:
            url = f"https://api.github.com/repos/{GITHUB_OWNER}/{repo}/commits"
            params = {"sha": branch, "per_page": limit}
            resp = httpx.get(url, params=params, timeout=10)

            if resp.status_code == 200:
                for commit in resp.json():
                    all_commits.append({
                        "repo": repo,
                        "sha": commit["sha"][:8],
                        "full_sha": commit["sha"],
                        "message": commit["commit"]["message"].split("\n")[0],
                        "author": commit["commit"]["author"]["name"],
                        "date": commit["commit"]["author"]["date"],
                        "url": commit["html_url"],
                    })
        except Exception as e:
            logger.warning(f"Could not fetch commits for {repo}: {e}")

    # Sort all commits by date descending
    all_commits.sort(key=lambda x: x["date"], reverse=True)
    return {"commits": all_commits[:limit]}
