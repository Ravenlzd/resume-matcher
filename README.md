# JobPulse - Resume Matcher

JobPulse is a Streamlit app that fetches live jobs, compares them with your resume, and explains why each role matches (or does not).

## Features

- Live job aggregation from:
  - Remotive API
  - Greenhouse boards (with job-detail fallback for missing descriptions)
- Resume upload and parsing from PDF
  - Primary extractor: `pdfplumber`
  - Fallback extractor: `pdfminer.six`
- Hybrid ranking
  - Semantic similarity (Sentence-Transformers)
  - Weighted skill coverage (required vs nice-to-have)
- Explainable matching per job
  - Matched skills
  - Missing required skills
  - Missing optional skills
  - Supporting text snippets
- Advanced filtering
  - Keyword search
  - Remote-only
  - Saved-only
  - Source filter
  - Role-category filter
  - Posted-date window
  - Minimum match score
- Save/unsave jobs with local persistence in `.saved_jobs.json`
- Reliability improvements
  - HTTP retries/backoff for source APIs
  - Graceful partial-failure handling in UI
  - Short-term caching of job fetches

## How Ranking Works

Job score is a hybrid:

- `75%` semantic similarity between resume text and job text
- `25%` weighted skill coverage

Skill coverage gives higher weight to skills found near requirement-style language (`required`, `must have`, etc.) and lower weight to nice-to-have language (`preferred`, `bonus`, etc.).

## Tech Stack

- App/UI: Streamlit
- Language: Python
- NLP: `sentence-transformers` (`all-MiniLM-L6-v2`)
- Similarity: `scikit-learn` cosine similarity
- Parsing: `pdfplumber`, `pdfminer.six`, `beautifulsoup4`
- HTTP: `requests` + retry adapter
- Testing: `pytest`
- CI: GitHub Actions

## Local Setup

```bash
git clone https://github.com/Ravenlzd/resume-matcher.git
cd resume-matcher

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Open `http://localhost:8501`.

## Running Tests

```bash
source venv/bin/activate
pytest -q
```

## Continuous Integration

This repo includes a GitHub Actions workflow:

- `.github/workflows/tests.yml`

It runs tests on push and pull requests across Python `3.9` and `3.11`.

## Notes

- On older macOS Python builds you may see:
  - `urllib3 NotOpenSSLWarning` (LibreSSL vs OpenSSL)
- The app still works, but using a newer Python build (3.11+) is recommended for best compatibility.

## Project Structure (Core Files)

- `app.py`: Streamlit UI, filters, state, persistence
- `matching.py`: skill extraction, explainability, hybrid ranking
- `sources.py`: Remotive/Greenhouse fetchers + retry/backoff
- `resume_parser.py`: PDF text extraction with fallback
- `tests/`: unit tests for matching and sources

