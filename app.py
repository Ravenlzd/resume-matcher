import json
import csv
import re
from io import StringIO
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

SORT_OPTIONS = [
    "Best match",
    "Newest first",
    "Oldest first",
    "Company A-Z",
    "Title A-Z",
]


# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def html_to_text(html: str) -> str:
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")
    lines = []
    for line in text.splitlines():
        cleaned = re.sub(r"\s+", " ", line).strip()
        if cleaned:
            lines.append(cleaned)
    return "\n".join(lines)


def split_description_paragraphs(text: str, sentences_per_paragraph: int = 3) -> List[str]:
    """Convert dense text into readable paragraph chunks."""
    if not text:
        return []

    chunks = [c.strip() for c in text.split("\n") if c.strip()]
    if len(chunks) > 1:
        return chunks

    single = chunks[0] if chunks else ""
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", single) if s.strip()]
    if not sentences:
        return []

    out = []
    for i in range(0, len(sentences), sentences_per_paragraph):
        out.append(" ".join(sentences[i:i + sentences_per_paragraph]))
    return out


def inject_custom_css(mode: str = "light"):
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;700&display=swap');

        :root {
            --jp-bg-1: #fffaf0;
            --jp-bg-2: #eef6ff;
            --jp-card: #ffffff;
            --jp-ink: #112033;
            --jp-muted: #4a6078;
            --jp-border: #d8e4f1;
        }

        html, body, [class*="css"] {
            font-family: 'Space Grotesk', sans-serif;
        }

        .stApp {
            background:
              radial-gradient(circle at 20% 5%, #fff2dc 0%, transparent 35%),
              radial-gradient(circle at 90% 0%, #dff3ff 0%, transparent 38%),
              linear-gradient(180deg, var(--jp-bg-1), var(--jp-bg-2));
            color: var(--jp-ink);
        }

        [data-testid="stMainBlockContainer"] {
            background: rgba(255, 255, 255, 0.62);
            border-radius: 18px;
            padding-top: 1rem;
        }

        [data-testid="stMain"] p,
        [data-testid="stMain"] li,
        [data-testid="stMain"] label,
        [data-testid="stMain"] div,
        [data-testid="stMain"] span {
            color: var(--jp-ink);
        }

        [data-testid="stMain"] [data-testid="stCaptionContainer"] * {
            color: var(--jp-muted) !important;
        }

        [data-testid="stMain"] .stTabs [role="tab"] {
            color: #47617d;
        }
        [data-testid="stMain"] .stTabs [aria-selected="true"] {
            color: #112033 !important;
            font-weight: 700;
        }

        [data-testid="stMain"] strong {
            color: #0e2137;
        }

        h1, h2, h3 {
            letter-spacing: -0.02em;
            color: var(--jp-ink);
        }

        .jp-hero {
            border: 1px solid var(--jp-border);
            border-radius: 16px;
            padding: 14px 16px;
            background: linear-gradient(120deg, #fff9f2, #f5fbff);
            margin-bottom: 8px;
        }

        .jp-kpi {
            border: 1px solid var(--jp-border);
            background: var(--jp-card);
            border-radius: 14px;
            padding: 10px 12px;
        }

        .jp-kpi .label {
            color: var(--jp-muted);
            font-size: 0.85rem;
            margin-bottom: 4px;
        }

        .jp-kpi .value {
            color: var(--jp-ink);
            font-size: 1.15rem;
            font-weight: 700;
        }

        .jp-sep {
            border: 0;
            height: 1px;
            margin: 10px 0 14px 0;
            background: linear-gradient(90deg, transparent, #c6d7ea, transparent);
        }

        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #10253f, #1c3553);
        }
        [data-testid="stSidebar"] * {
            color: #f3f8ff !important;
        }

        /* Sidebar form controls: keep strong contrast */
        [data-testid="stSidebar"] .stTextInput input,
        [data-testid="stSidebar"] .stNumberInput input,
        [data-testid="stSidebar"] .stTextArea textarea {
            color: #f3f8ff !important;
            background: rgba(7, 16, 30, 0.85) !important;
            border: 1px solid #3f5e82 !important;
        }
        [data-testid="stSidebar"] .stTextInput input::placeholder,
        [data-testid="stSidebar"] .stNumberInput input::placeholder,
        [data-testid="stSidebar"] .stTextArea textarea::placeholder {
            color: #c7d7ef !important;
            opacity: 1 !important;
        }

        [data-testid="stSidebar"] [data-baseweb="select"] > div {
            background: rgba(7, 16, 30, 0.85) !important;
            border: 1px solid #3f5e82 !important;
        }
        [data-testid="stSidebar"] [data-baseweb="select"] span,
        [data-testid="stSidebar"] [data-baseweb="select"] div {
            color: #f3f8ff !important;
        }

        [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMin"],
        [data-testid="stSidebar"] .stSlider [data-testid="stTickBarMax"] {
            color: #dbe8fb !important;
        }

        .stButton > button, .stLinkButton > a {
            background: #10253f;
            color: #f7fbff !important;
            border: 1px solid #2e4b6a;
            border-radius: 12px;
        }
        .stButton > button:hover, .stLinkButton > a:hover {
            border-color: #4d6f95;
            background: #163255;
        }

        [data-testid="stVerticalBlock"] [data-testid="stHorizontalBlock"] [data-testid="stVerticalBlockBorderWrapper"] {
            animation: fadeSlide 240ms ease-out;
        }

        [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
            border-width: 1px !important;
            border-color: #c9d9ea !important;
            box-shadow: 0 6px 20px rgba(16, 37, 63, 0.06);
            background: rgba(255, 255, 255, 0.86);
        }

        @keyframes fadeSlide {
            from { opacity: 0; transform: translateY(4px); }
            to { opacity: 1; transform: translateY(0); }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # Dark mode overrides layered on top of the base theme.
    if mode == "dark":
        st.markdown(
            """
            <style>
            :root {
                --jp-bg-1: #0b1220;
                --jp-bg-2: #111827;
                --jp-card: #0f1b2d;
                --jp-ink: #e7eef9;
                --jp-muted: #a8b8d0;
                --jp-border: #2a3b55;
            }

            .stApp {
                background:
                  radial-gradient(circle at 20% 5%, #102038 0%, transparent 35%),
                  radial-gradient(circle at 90% 0%, #182a44 0%, transparent 38%),
                  linear-gradient(180deg, #0b1220, #111827);
            }

            [data-testid="stMainBlockContainer"] {
                background: rgba(9, 16, 28, 0.72);
            }

            .jp-hero {
                background: linear-gradient(120deg, #101b2e, #16243b);
            }

            .jp-sep {
                background: linear-gradient(90deg, transparent, #324867, transparent);
            }

            [data-testid="stMain"] [data-testid="stVerticalBlockBorderWrapper"] {
                border-color: #2a3b55 !important;
                background: rgba(11, 20, 34, 0.8);
            }

            [data-testid="stMain"] .stTabs [role="tab"] {
                color: #9db0cb;
            }
            [data-testid="stMain"] .stTabs [aria-selected="true"] {
                color: #f3f8ff !important;
            }

            [data-testid="stMain"] strong {
                color: #e7eef9;
            }

            .stButton > button, .stLinkButton > a {
                background: #1f3558;
                border-color: #3f5e82;
            }
            .stButton > button:hover, .stLinkButton > a:hover {
                background: #274571;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )


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


def sort_jobs(jobs: List[Dict]) -> List[Dict]:
    sort_by = st.session_state.get("sort_by", "Best match")

    if sort_by == "Best match":
        return sorted(jobs, key=lambda j: float(j.get("score", -1.0)), reverse=True)
    if sort_by == "Newest first":
        return sorted(
            jobs,
            key=lambda j: parse_posted_at(j.get("posted_at") or "") or datetime.min.replace(tzinfo=timezone.utc),
            reverse=True,
        )
    if sort_by == "Oldest first":
        return sorted(
            jobs,
            key=lambda j: parse_posted_at(j.get("posted_at") or "") or datetime.max.replace(tzinfo=timezone.utc),
        )
    if sort_by == "Company A-Z":
        return sorted(jobs, key=lambda j: (j.get("company", "") or "").lower())
    if sort_by == "Title A-Z":
        return sorted(jobs, key=lambda j: (j.get("title", "") or "").lower())
    return jobs


def jobs_to_csv(jobs: List[Dict]) -> str:
    out = StringIO()
    writer = csv.DictWriter(
        out,
        fieldnames=["title", "company", "location", "source", "posted_at", "score", "url", "role_category"],
    )
    writer.writeheader()
    for j in jobs:
        writer.writerow(
            {
                "title": j.get("title", ""),
                "company": j.get("company", ""),
                "location": j.get("location", ""),
                "source": j.get("source", ""),
                "posted_at": j.get("posted_at", ""),
                "score": f"{float(j.get('score', 0.0)):.3f}" if "score" in j else "",
                "url": j.get("url", ""),
                "role_category": j.get("role_category", ""),
            }
        )
    return out.getvalue()


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
    max_results = int(st.session_state.get("max_results", 60) or 60)
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

    filtered = sort_jobs(filtered)
    st.session_state.filtered_jobs = filtered[:max_results]


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
            job["clean_description"] = html_to_text(job.get("description") or "")
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
    "sort_by": "Best match",
    "max_results": 60,
    "ui_mode": "light",
    "fetched_once": False,
    "refresh_now": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

inject_custom_css(st.session_state.get("ui_mode", "light"))
st.markdown(
    '<div class="jp-hero"><strong>Find roles faster.</strong> Live feeds, resume-aware ranking, and clear fit explanations in one view.</div>',
    unsafe_allow_html=True,
)


# ------------------------------------------------------------
# Sidebar (filters + resume)
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## Filters")
    mode_btn = "Switch to Dark Mode" if st.session_state.get("ui_mode", "light") == "light" else "Switch to Light Mode"
    if st.button(mode_btn, use_container_width=True):
        st.session_state.ui_mode = "dark" if st.session_state.get("ui_mode", "light") == "light" else "light"
        st.rerun()

    st.text_input(
        "Search term (title/keywords)",
        key="query",
        placeholder="e.g., python, customer success, salesforce",
    )
    st.checkbox("Remote only", key="remote_only")
    st.checkbox("Saved only", key="saved_only")
    st.selectbox("Posted date", options=list(DATE_FILTER_OPTIONS.keys()), key="posted_window")
    st.selectbox("Sort results", options=SORT_OPTIONS, key="sort_by")
    st.slider("Max results", min_value=10, max_value=150, step=10, key="max_results")

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

all_jobs = st.session_state.jobs
visible_jobs = st.session_state.filtered_jobs
scored_jobs = [j for j in all_jobs if "score" in j]
avg_score = (sum(float(j.get("score", 0.0)) for j in scored_jobs) / len(scored_jobs)) if scored_jobs else 0.0
remote_count = sum(1 for j in visible_jobs if j.get("remote", False))
fresh_cutoff = datetime.now(timezone.utc) - timedelta(days=7)
fresh_count = sum(
    1
    for j in visible_jobs
    if (parse_posted_at(j.get("posted_at")) or datetime.min.replace(tzinfo=timezone.utc)) >= fresh_cutoff
)

kc1, kc2, kc3, kc4 = st.columns(4)
with kc1:
    st.markdown(
        f'<div class="jp-kpi"><div class="label">Visible Jobs</div><div class="value">{len(visible_jobs)}</div></div>',
        unsafe_allow_html=True,
    )
with kc2:
    st.markdown(
        f'<div class="jp-kpi"><div class="label">Saved Jobs</div><div class="value">{len(st.session_state.saved_ids)}</div></div>',
        unsafe_allow_html=True,
    )
with kc3:
    st.markdown(
        f'<div class="jp-kpi"><div class="label">Remote in View</div><div class="value">{remote_count}</div></div>',
        unsafe_allow_html=True,
    )
with kc4:
    score_text = f"{avg_score:.2f}" if scored_jobs else "N/A"
    st.markdown(
        f'<div class="jp-kpi"><div class="label">Avg Match Score</div><div class="value">{score_text}</div></div>',
        unsafe_allow_html=True,
    )

st.caption(f"{len(st.session_state.filtered_jobs)} shown of {len(st.session_state.jobs)} total jobs")
st.caption(f"{fresh_count} role(s) posted in the last 7 days")
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
        for idx, job in enumerate(jobs_to_show):
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
                    desc = job.get("clean_description") or ""
                    if not desc:
                        st.write("_No description provided._")
                    else:
                        desc_key = get_job_key(job)
                        paragraphs = split_description_paragraphs(desc)
                        preview = paragraphs[:6]
                        rest = paragraphs[6:]

                        for p in preview:
                            st.markdown(p)

                        if rest:
                            show_full = st.checkbox(
                                f"Show full description ({len(rest)} more section(s))",
                                key=f"full_desc:{desc_key}",
                            )
                            if show_full:
                                for p in rest:
                                    st.markdown(p)
            if idx < len(jobs_to_show) - 1:
                st.markdown('<hr class="jp-sep" />', unsafe_allow_html=True)

with tab_saved:
    saved_jobs = [j for j in st.session_state.jobs if get_job_key(j) in st.session_state.saved_ids]
    if not saved_jobs:
        st.info("No saved jobs yet. Click Save on any result.")
    else:
        st.download_button(
            "Export saved jobs (CSV)",
            data=jobs_to_csv(saved_jobs),
            file_name="saved_jobs.csv",
            mime="text/csv",
        )
        for idx, job in enumerate(saved_jobs):
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
            if idx < len(saved_jobs) - 1:
                st.markdown('<hr class="jp-sep" />', unsafe_allow_html=True)
