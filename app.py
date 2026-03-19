import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Dict, List

import streamlit as st
from bs4 import BeautifulSoup

from sources import fetch_greenhouse_board, fetch_remotive, merge_dedupe
from resume_parser import extract_text_from_pdf
from matching import get_match_explanation, score_resume_to_jobs

# ------------------------------------------------------------
# Page setup
# ------------------------------------------------------------
st.set_page_config(page_title="JobPulse — Live Job Finder", layout="wide")
st.title("JobPulse — Live Job Finder")

SAVED_FILE = Path(__file__).with_name(".saved_jobs.json")

ROLE_KEYWORDS = {
    "Engineering": ["engineer", "developer", "software", "backend", "frontend", "full-stack", "full stack", "devops"],
    "Data / AI": ["data", "machine learning", "ai", "ml", "scientist", "analytics", "nlp"],
    "Customer Success": ["customer success", "support", "retention", "onboarding", "account manager", "customer service"],
    "Sales": ["sales", "business development", "account executive", "bdr", "sdr"],
    "Design": ["designer", "ux", "ui", "product design", "visual design"],
    "Marketing": ["marketing", "growth", "seo", "content", "brand"],
    "Operations": ["operations", "ops", "program manager", "project manager", "coordinator"],
}

DATE_FILTER_OPTIONS = {
    "Any time": 0,
    "Last 7 days": 7,
    "Last 30 days": 30,
    "Last 90 days": 90,
}


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def html_to_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return " ".join(soup.stripped_strings)


def get_job_key(job: Dict) -> str:
    return f"{job.get('source', '')}:{job.get('source_job_id', '')}"


def parse_posted_at(value: str):
    if not value:
        return None
    try:
        normalized = value.replace("Z", "+00:00")
        dt = datetime.fromisoformat(normalized)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def posted_label(value: str) -> str:
    dt = parse_posted_at(value)
    if not dt:
        return "Posted date unavailable"
    now = datetime.now(timezone.utc)
    days = (now - dt).days
    if days <= 0:
        return "Posted today"
    if days == 1:
        return "Posted 1 day ago"
    return f"Posted {days} days ago"


def infer_role_category(job: Dict) -> str:
    text = " ".join(
        [
            job.get("title", ""),
            " ".join(job.get("tags", [])),
            job.get("clean_description", ""),
        ]
    ).lower()
    best = ("Other", 0)
    for category, terms in ROLE_KEYWORDS.items():
        score = sum(1 for term in terms if term in text)
        if score > best[1]:
            best = (category, score)
    return best[0]


def load_saved_ids() -> set:
    if not SAVED_FILE.exists():
        return set()
    try:
        data = json.loads(SAVED_FILE.read_text(encoding="utf-8"))
        if isinstance(data, list):
            return set(str(x) for x in data)
    except Exception:
        pass
    return set()


def persist_saved_ids():
    SAVED_FILE.write_text(
        json.dumps(sorted(st.session_state.saved_ids), indent=2),
        encoding="utf-8",
    )


@st.cache_data(ttl=900, show_spinner=False)
def fetch_remotive_cached(query: str, limit: int = 150) -> List[Dict]:
    return fetch_remotive(query, limit=limit)


@st.cache_data(ttl=900, show_spinner=False)
def fetch_greenhouse_cached(company_token: str) -> List[Dict]:
    return fetch_greenhouse_board(company_token)


def apply_filters():
    """Filter jobs into session-state filtered_jobs based on all active controls."""
    q = (st.session_state.get("query", "") or "").strip().lower()
    jobs = st.session_state.jobs or []
    min_score = float(st.session_state.get("min_score", 0.0) or 0.0)
    remote_only = bool(st.session_state.get("remote_only", False))
    saved_only = bool(st.session_state.get("saved_only", False))
    selected_sources = set(st.session_state.get("selected_sources", []))
    selected_categories = set(st.session_state.get("selected_categories", []))
    days_window = DATE_FILTER_OPTIONS.get(st.session_state.get("posted_window", "Any time"), 0)
    now = datetime.now(timezone.utc)

    def text_of(job: Dict) -> str:
        return " ".join(
            [
                job.get("title", ""),
                job.get("company", ""),
                job.get("location", ""),
                " ".join(job.get("tags", [])),
                job.get("clean_description", ""),
            ]
        ).lower()

    filtered = []
    for job in jobs:
        key = get_job_key(job)

        if q and q not in text_of(job):
            continue
        if remote_only and not job.get("remote", False):
            continue
        if saved_only and key not in st.session_state.saved_ids:
            continue
        if selected_sources and job.get("source", "") not in selected_sources:
            continue
        if selected_categories and job.get("role_category", "Other") not in selected_categories:
            continue
        if days_window > 0:
            dt = parse_posted_at(job.get("posted_at"))
            if not dt:
                continue
            if dt < (now - timedelta(days=days_window)):
                continue
        if min_score > 0:
            score = float(job.get("score", 0.0) or 0.0)
            if score < min_score:
                continue

        filtered.append(job)

    st.session_state.filtered_jobs = filtered


def rank_jobs_to_resume():
    ranked = score_resume_to_jobs(
        st.session_state.resume_text,
        st.session_state.jobs,
        top_n=max(50, len(st.session_state.jobs)),
    )
    ordered = []
    for job, score in ranked:
        job["score"] = float(score)
        ordered.append(job)
    st.session_state.jobs = ordered
    apply_filters()


def initial_fetch_if_needed():
    if st.session_state.get("fetched_once", False) and not st.session_state.get("refresh_now", False):
        return

    with st.spinner("Fetching live jobs..."):
        rem = []
        try:
            rem = fetch_remotive_cached(st.session_state.get("query", ""), limit=150)
        except Exception as e:
            st.sidebar.warning(f"Remotive fetch failed: {e}")

        boards = []
        for token in st.session_state.selected_companies:
            try:
                boards.extend(fetch_greenhouse_cached(token))
            except Exception as e:
                st.sidebar.warning(f"Greenhouse fetch failed for {token}: {e}")

        st.session_state.jobs = merge_dedupe([rem, boards])

        for job in st.session_state.jobs:
            job["clean_description"] = html_to_text(job.get("description"))
            job["role_category"] = infer_role_category(job)
            job.pop("score", None)

        st.session_state.fetched_once = True
        st.session_state.refresh_now = False
        apply_filters()


# ------------------------------------------------------------
# Session state defaults
# ------------------------------------------------------------
defaults = {
    "resume_text": "",
    "jobs": [],
    "filtered_jobs": [],
    "saved_ids": load_saved_ids(),
    "query": "",
    "companies": ["stripe", "airbnb", "openai"],
    "selected_companies": [],
    "selected_sources": [],
    "selected_categories": [],
    "saved_only": False,
    "remote_only": False,
    "posted_window": "Any time",
    "min_score": 0.0,
    "fetched_once": False,
    "refresh_now": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ------------------------------------------------------------
# Sidebar (filters + resume)
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## Filters")

    st.text_input(
        "Search term (title/keywords)",
        key="query",
        placeholder="e.g., python, customer success, salesforce",
    )
    st.checkbox("Remote only", key="remote_only")
    st.checkbox("Saved only", key="saved_only")
    st.selectbox("Posted date", options=list(DATE_FILTER_OPTIONS.keys()), key="posted_window")

    if st.session_state.resume_text:
        st.slider("Minimum match score", 0.0, 1.0, key="min_score", step=0.05)

    source_options = sorted({j.get("source", "—") for j in st.session_state.jobs})
    st.multiselect("Sources", options=source_options, key="selected_sources")

    category_options = sorted({j.get("role_category", "Other") for j in st.session_state.jobs})
    st.multiselect("Role categories", options=category_options, key="selected_categories")

    if st.button("Apply filters", use_container_width=True):
        apply_filters()
        st.success(f"Showing {len(st.session_state.filtered_jobs)} job(s).")

    st.markdown("### Company boards (Greenhouse)")
    st.session_state.selected_companies = st.multiselect(
        "Add specific companies (optional)",
        options=st.session_state.companies,
        default=st.session_state.selected_companies,
        help="Try companies that use Greenhouse, e.g., stripe, airbnb, openai.",
    )

    if st.button("Refresh live jobs now", use_container_width=True):
        st.session_state.refresh_now = True

    st.markdown("---")
    st.markdown("### Resume")
    up = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    if up:
        with st.spinner("Extracting resume text..."):
            st.session_state.resume_text = extract_text_from_pdf(up)
        st.success("Resume loaded.")
        if len(st.session_state.resume_text) < 200:
            st.warning("The extracted text is very short. This PDF may be scanned/image-based, so matching may be less accurate.")

    if st.session_state.resume_text:
        with st.expander("Preview resume text", expanded=False):
            st.text_area("Content", st.session_state.resume_text, height=220, label_visibility="collapsed")

        if st.button("Rank to My Resume", use_container_width=True):
            if not st.session_state.jobs:
                st.warning("No jobs yet. Fetching now...")
                st.session_state.refresh_now = True
                initial_fetch_if_needed()
            if st.session_state.jobs:
                with st.spinner("Scoring jobs with transformers..."):
                    rank_jobs_to_resume()
                st.success("Ranked jobs by relevance.")

    if st.session_state.saved_ids and st.button("Clear all saved", use_container_width=True):
        st.session_state.saved_ids.clear()
        persist_saved_ids()
        st.rerun()


# ------------------------------------------------------------
# Auto-fetch + apply filters
# ------------------------------------------------------------
initial_fetch_if_needed()
apply_filters()

st.caption(f"{len(st.session_state.filtered_jobs)} shown of {len(st.session_state.jobs)} total jobs")
st.markdown("---")


# ------------------------------------------------------------
# Results / Saved tabs
# ------------------------------------------------------------
saved_count = len(st.session_state.saved_ids)
tab_results, tab_saved = st.tabs(
    [f"Results ({len(st.session_state.filtered_jobs)})", f"Saved ({saved_count})"]
)

with tab_results:
    jobs_to_show = st.session_state.filtered_jobs
    if not jobs_to_show:
        st.info("No jobs to show. Adjust filters, refresh jobs, or upload a resume and rank.")
    else:
        for job in jobs_to_show:
            with st.container(border=True):
                tcol1, tcol2 = st.columns([3, 1])

                with tcol1:
                    st.markdown(f"**{job.get('title', '')}** · *{job.get('company', '')}*")
                    st.caption(
                        f"{job.get('location', '—')} · {posted_label(job.get('posted_at'))} · "
                        f"Source: {job.get('source', '—')} · Category: {job.get('role_category', 'Other')}"
                    )

                    if "score" in job:
                        st.markdown(f"**Match Score:** {job['score']:.2f}")

                    if st.session_state.resume_text:
                        job_text = f"{job.get('title', '')} {job.get('clean_description', '')}"
                        why = get_match_explanation(st.session_state.resume_text, job_text)

                        st.markdown("Matched skills")
                        st.write(", ".join(why["matched"][:10]) if why["matched"] else "None detected")

                        st.markdown("Missing required skills")
                        st.write(", ".join(why["missing_required"][:8]) if why["missing_required"] else "None detected")

                        if why["missing_optional"]:
                            st.markdown("Missing optional skills")
                            st.write(", ".join(why["missing_optional"][:8]))

                        with st.expander("Why this match?"):
                            if why["snippets"]:
                                for s in why["snippets"]:
                                    st.write(f"- {s}")
                            else:
                                st.write("No snippet highlights found.")

                with tcol2:
                    st.link_button("Apply", job.get("url", "#"), use_container_width=True)
                    job_key = get_job_key(job)
                    is_saved = job_key in st.session_state.saved_ids
                    if st.button(
                        "Unsave" if is_saved else "Save",
                        key=f"save:{job_key}",
                        use_container_width=True,
                    ):
                        if is_saved:
                            st.session_state.saved_ids.discard(job_key)
                        else:
                            st.session_state.saved_ids.add(job_key)
                        persist_saved_ids()
                        st.rerun()

                with st.expander("Description"):
                    st.write(job.get("clean_description") or "_No description provided._")

with tab_saved:
    saved_jobs = [j for j in st.session_state.jobs if get_job_key(j) in st.session_state.saved_ids]
    if not saved_jobs:
        st.info("No saved jobs yet. Click Save on any result.")
    else:
        for job in saved_jobs:
            with st.container(border=True):
                scol1, scol2 = st.columns([4, 1])
                with scol1:
                    st.markdown(
                        f"**{job.get('title', '')}** · *{job.get('company', '')}* — "
                        f"[Apply link]({job.get('url', '#')})"
                    )
                    st.caption(
                        f"{job.get('location', '—')} · {posted_label(job.get('posted_at'))} · "
                        f"Source: {job.get('source', '—')} · Category: {job.get('role_category', 'Other')}"
                    )
                with scol2:
                    if st.button("Unsave", key=f"unsave:{get_job_key(job)}", use_container_width=True):
                        st.session_state.saved_ids.discard(get_job_key(job))
                        persist_saved_ids()
                        st.rerun()
