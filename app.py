import streamlit as st
from bs4 import BeautifulSoup

from sources import fetch_remotive, fetch_greenhouse_board, merge_dedupe
from resume_parser import extract_text_from_pdf
from matching import score_resume_to_jobs, extract_matched_skills

# ------------------------------------------------------------
# Page setup
# ------------------------------------------------------------
st.set_page_config(page_title="JobPulse — Live Job Finder", layout="wide")
st.title("JobPulse — Live Job Finder")

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------
def html_to_text(html: str) -> str:
    """Strip HTML tags to clean text."""
    if not html:
        return ""
    soup = BeautifulSoup(html, "html.parser")
    return " ".join(soup.stripped_strings)

def apply_search():
    """Filter st.session_state.jobs into st.session_state.filtered_jobs using the search query."""
    q = (st.session_state.get("query", "") or "").strip().lower()
    jobs = st.session_state.jobs or []
    if not q:
        st.session_state.filtered_jobs = list(jobs)
        return

    def text_of(j):
        parts = [
            j.get("title", ""),
            j.get("company", ""),
            j.get("location", ""),
            " ".join(j.get("tags", [])),
            j.get("clean_description", "") or "",
        ]
        return " ".join(parts).lower()

    st.session_state.filtered_jobs = [j for j in jobs if q in text_of(j)]

def rank_jobs_to_resume():
    """Score all jobs vs resume once, store score in each job, and reorder."""
    ranked = score_resume_to_jobs(
        st.session_state.resume_text,
        st.session_state.jobs,
        top_n=max(50, len(st.session_state.jobs)),
    )
    ordered = []
    for j, s in ranked:
        j["score"] = float(s)  # 0..1
        ordered.append(j)
    st.session_state.jobs = ordered
    # ensure clean_description exists for all jobs
    for j in st.session_state.jobs:
        if "clean_description" not in j:
            j["clean_description"] = html_to_text(j.get("description"))
    apply_search()

def initial_fetch_if_needed():
    """Fetch live jobs once on first load (or when user presses refresh)."""
    if st.session_state.get("fetched_once", False) and not st.session_state.get("refresh_now", False):
        return

    with st.spinner("Fetching live jobs..."):
        rem = fetch_remotive(st.session_state.get("query", ""), limit=150)
        boards = []
        for token in st.session_state.selected_companies:
            try:
                boards.extend(fetch_greenhouse_board(token))
            except Exception as e:
                st.sidebar.warning(f"Greenhouse fetch failed for {token}: {e}")

        st.session_state.jobs = merge_dedupe([rem, boards])

        # Precompute clean descriptions once; clear any old score
        for j in st.session_state.jobs:
            j["clean_description"] = html_to_text(j.get("description"))
            j.pop("score", None)

        st.session_state.fetched_once = True
        st.session_state.refresh_now = False
        apply_search()

# ------------------------------------------------------------
# Session state defaults
# ------------------------------------------------------------
defaults = {
    "resume_text": "",
    "jobs": [],
    "filtered_jobs": [],
    "saved_ids": set(),
    "query": "",
    "companies": ["stripe", "airbnb", "openai"],   # example public Greenhouse boards
    "selected_companies": [],
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
    st.markdown("## 🔍 Filters")

    st.text_input(
        "Search term (title/keywords)",
        key="query",
        placeholder="e.g., python, data, backend",
    )
    if st.button("🔎 Search / Apply Filters", use_container_width=True):
        apply_search()
        st.success(f"Showing {len(st.session_state.filtered_jobs)} result(s) for '{st.session_state.query or 'all'}'.")

    st.markdown("### Company boards (Greenhouse)")
    st.session_state.selected_companies = st.multiselect(
        "Add specific companies (optional)",
        options=st.session_state.companies,
        default=st.session_state.selected_companies,
        help="Try companies that use Greenhouse, e.g., stripe, airbnb, openai.",
    )

    if st.button("🔄 Refresh live jobs now", use_container_width=True):
        st.session_state.refresh_now = True

    st.markdown("---")
    st.markdown("### 📄 Resume")
    up = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
    if up:
        with st.spinner("Extracting resume text..."):
            st.session_state.resume_text = extract_text_from_pdf(up)
        st.success("Resume loaded!")

    if st.session_state.resume_text:
        with st.expander("Preview resume text", expanded=False):
            st.text_area("Content", st.session_state.resume_text, height=220, label_visibility="collapsed")

        # Rank button placed UNDER the preview
        if st.button("🧠 Rank to My Resume", use_container_width=True):
            if not st.session_state.jobs:
                st.warning("No jobs yet. Fetching them now…")
                st.session_state.refresh_now = True
                initial_fetch_if_needed()
            if st.session_state.jobs:
                with st.spinner("Scoring jobs with transformers..."):
                    rank_jobs_to_resume()
                st.success("Ranked jobs by relevance.")

# ------------------------------------------------------------
# Auto-fetch on first load (or when user clicks refresh)
# ------------------------------------------------------------
initial_fetch_if_needed()

st.markdown("---")

# ------------------------------------------------------------
# Results / Saved tabs
# ------------------------------------------------------------
tab_results, tab_saved = st.tabs(["🔎 Results", "⭐ Saved"])

with tab_results:
    jobs_to_show = st.session_state.filtered_jobs or st.session_state.jobs
    if not jobs_to_show:
        st.info("No jobs to show yet. Adjust your filters or click **Refresh live jobs now** in the sidebar.")
    else:
        for j in jobs_to_show:
            with st.container(border=True):
                tcol1, tcol2 = st.columns([3, 1])

                with tcol1:
                    st.markdown(f"**{j.get('title','')}** · *{j.get('company','')}*")
                    st.caption(f"{j.get('location','—')} · Source: {j.get('source','—')}")

                    if st.session_state.resume_text:
                        score = float(j.get("score", 0.0))     # 0..1
                        percent = int(score * 100)             # show as XX%
                        st.progress(min(1.0, score), text=f"Match score: {percent}%")

                        matched = extract_matched_skills(
                            st.session_state.resume_text,
                            (j.get("clean_description") or "") + " " + j.get("title", ""),
                        )
                        if matched:
                            st.caption("Matched skills: " + ", ".join(matched))

                with tcol2:
                    st.link_button("Apply", j.get("url", "#"), use_container_width=True)
                    job_key = f"{j.get('source','')}:{j.get('source_job_id','')}"
                    saved = job_key in st.session_state.saved_ids
                    if st.button("⭐ Save" if not saved else "✅ Saved", key=job_key):
                        st.session_state.saved_ids.add(job_key)

                with st.expander("Description"):
                    st.write(j.get("clean_description") or "_No description provided._")

with tab_saved:
    saved = [
        j for j in (st.session_state.filtered_jobs or st.session_state.jobs)
        if f"{j.get('source','')}:{j.get('source_job_id','')}" in st.session_state.saved_ids
    ]
    if not saved:
        st.info("No saved jobs yet. Click **Save** on any job.")
    else:
        for j in saved:
            with st.container(border=True):
                st.markdown(
                    f"**{j.get('title','')}** · *{j.get('company','')}* — "
                    f"[Apply link]({j.get('url','#')})"
                )
                st.caption(f"{j.get('location','—')} · Source: {j.get('source','—')}")
