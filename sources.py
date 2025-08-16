# sources.py
import requests
from typing import List, Dict

def fetch_remotive(query: str = "", limit: int = 100) -> List[Dict]:
    """Public JSON feed: https://remotive.com/api/remote-jobs"""
    url = "https://remotive.com/api/remote-jobs"
    params = {}
    if query:
        params["search"] = query
    r = requests.get(url, params=params, timeout=30)
    r.raise_for_status()
    data = r.json().get("jobs", [])
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

def fetch_greenhouse_board(company_token: str) -> List[Dict]:
    """
    Greenhouse boards expose public JSON.
    Example token: 'nordsecurity' -> https://boards-api.greenhouse.io/v1/boards/nordsecurity/jobs
    """
    url = f"https://boards-api.greenhouse.io/v1/boards/{company_token}/jobs"
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    data = r.json().get("jobs", [])
    jobs = []
    for j in data:
        jobs.append({
            "source": f"greenhouse:{company_token}",
            "source_job_id": str(j["id"]),
            "title": j.get("title", ""),
            "company": (j.get("company") or {}).get("name", "") or company_token,
            "location": (j.get("location") or {}).get("name", "") or "—",
            "remote": "remote" in ((j.get("location") or {}).get("name","").lower()),
            "tags": [d["name"] for d in j.get("departments", [])],
            "url": j.get("absolute_url", ""),
            "description": "",
            "posted_at": None,
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
