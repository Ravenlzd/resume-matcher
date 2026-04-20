# 🚀 JobPulse — Resume Matcher

Find better jobs faster with live job feeds, resume-aware ranking, and clean match explanations.

## 🌐 Live Demo

👉 https://resume-matcher-uvrrrmieyeunynrew4vbgi.streamlit.app

## ✨ What This App Does

- 🔎 Pulls live jobs from:
  - Remotive
  - Greenhouse boards
- 📄 Parses your uploaded PDF resume
- 🧠 Ranks jobs with hybrid scoring:
  - semantic similarity
  - weighted skill coverage
- ✅ Explains each match with:
  - matched skills
  - missing required skills
  - missing optional skills
  - snippet-based reasoning
- 🎛️ Lets you filter and sort by:
  - keyword
  - remote-only
  - saved-only
  - source
  - role category
  - posted date
  - minimum score
  - max results
- ⭐ Save/unsave jobs and export saved jobs as CSV
- 🌗 Toggle Light/Dark mode in-app

## 🧪 Reliability & Quality

- 🔁 API retries + backoff for transient failures
- 🧱 Graceful partial-failure handling (one source can fail without breaking app)
- ⚡ Cached fetches for faster reloads
- ✅ Automated tests with `pytest`
- 🤖 GitHub Actions CI on push/PR

## 🛠️ Tech Stack

- **Frontend/App:** Streamlit
- **Language:** Python
- **NLP:** sentence-transformers (`all-MiniLM-L6-v2`)
- **Similarity:** scikit-learn cosine similarity
- **Parsing:** pdfplumber + pdfminer.six + BeautifulSoup
- **HTTP:** requests + urllib3 retry adapter
- **Testing:** pytest

## 📦 Local Setup

```bash
git clone https://github.com/Ravenlzd/resume-matcher.git
cd resume-matcher

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Then open: `http://localhost:8501`

## ✅ Run Tests

```bash
source venv/bin/activate
pytest -q
```

## 🗂️ Core Files

- `app.py` — UI, filters, layout, mode toggle, persistence
- `matching.py` — skill extraction + ranking logic + explainability
- `sources.py` — Remotive/Greenhouse fetchers + retry logic
- `resume_parser.py` — PDF text extraction with fallback
- `tests/` — unit tests for matching and source behavior
- `.github/workflows/tests.yml` — CI pipeline

## ⚠️ Note for macOS Users

If you see `NotOpenSSLWarning` from `urllib3` on older macOS Python builds, the app can still run.  
For best compatibility, prefer a newer Python build (3.11+).

## 👤 Author

Built by **Ravan Alizada**.
