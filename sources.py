import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from typing import List, Dict, Optional, Any

_SESSION = None


def _get_session() -> requests.Session:
    """Shared session with retry/backoff for transient failures."""
    global _SESSION
    if _SESSION is None:
        retry = Retry(
            total=3,
            connect=3,
            read=3,
            backoff_factor=0.6,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"],
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry)
        s = requests.Session()
        s.mount("https://", adapter)
        s.mount("http://", adapter)
        _SESSION = s
    return _SESSION


def _request_json(url: str, params: Optional[Dict] = None, timeout: int = 30) -> Dict[str, Any]:
    """GET JSON with centralized network handling."""
    r = _get_session().get(url, params=params, timeout=timeout)
    r.raise_for_status()
    return r.json()

def fetch_remotive(query: str = "", limit: int = 100) -> List[Dict]:
    """Public JSON feed: https://remotive.com/api/remote-jobs"""
    url = "https://remotive.com/api/remote-jobs"
    params = {}
    if query:
        params["search"] = query
    data = _request_json(url, params=params, timeout=30).get("jobs", [])
    jobs = []
    for j in data[:limit]:
        jobs.append({
            "source": "remotive",
            "source_job_id": str(j["id"]),
            "title": j.get("title", ""),
            "company": j.get("company_name", ""),
            "location": j.get("candidate_required_location", "") or "Remote",
            "remote": True,
            "tags": j.get("tags", []),
            "url": j.get("url", ""),
            "description": j.get("description", ""),
            "posted_at": j.get("publication_date", ""),
        })
    return jobs

def _fetch_greenhouse_job_detail(company_token: str, job_id: str) -> Dict:
    """Fetch full Greenhouse job detail with description/content."""
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_token}/jobs/{job_id}"
    return _request_json(url, timeout=30)

def fetch_greenhouse_board(company_token: str) -> List[Dict]:
    """
    Greenhouse boards expose public JSON.
    Example token: 'nordsecurity' -> https://boards-api.greenhouse.io/v1/boards/nordsecurity/jobs
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_token}/jobs"
    # content=true often provides full HTML description directly in listing.
    data = _request_json(url, params={"content": "true"}, timeout=30).get("jobs", [])
    jobs = []
    for j in data:
        desc = j.get("content") or j.get("description") or ""
        # Some boards still omit content in listing; fetch detail lazily.
        if not desc:
            try:
                detail = _fetch_greenhouse_job_detail(company_token, str(j["id"]))
                desc = detail.get("content") or detail.get("description") or ""
            except Exception:
                desc = ""

        jobs.append({
            "source": f"greenhouse:{company_token}",
            "source_job_id": str(j["id"]),
            "title": j.get("title", ""),
            "company": (j.get("company") or {}).get("name", "") or company_token,
            "location": (j.get("location") or {}).get("name", "") or "—",
            "remote": "remote" in ((j.get("location") or {}).get("name","").lower()),
            "tags": [d["name"] for d in j.get("departments", [])],
            "url": j.get("absolute_url", ""),
            "description": desc,
            "posted_at": j.get("updated_at") or j.get("created_at"),
        })
    return jobs

def merge_dedupe(job_lists: List[List[Dict]]) -> List[Dict]:
    seen = set()
    out = []
    for lst in job_lists:
        for j in lst:
            key = (j["source"], j["source_job_id"])
            if key in seen: 
                continue
            seen.add(key)
            out.append(j)
    return out
