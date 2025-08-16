# matching.py
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

_model = None

def get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model

def score_resume_to_jobs(resume_text: str, jobs: list, top_n: int = 20):
    """
    Returns top_n jobs with scores, sorted desc.
    Output: list of tuples (job_dict, score_float)
    """
    if not resume_text or not jobs:
        return []
    m = get_model()
    r_emb = m.encode([resume_text])[0]
    texts = [(i, (j["title"] + " " + (j.get("description") or ""))) for i, j in enumerate(jobs)]
    j_embs = m.encode([t[1] for t in texts])
    sims = cosine_similarity([r_emb], j_embs)[0]
    ranked = sorted([(jobs[i], float(s)) for (i, _), s in zip(texts, sims)], key=lambda x: x[1], reverse=True)
    return ranked[:top_n]

def extract_matched_skills(resume_text: str, job_text: str, skills=None):
    """Simple overlap highlighter. Extend with a real skills list if you want."""
    if skills is None:
        skills = ["python","sql","docker","streamlit","fastapi","flask","pandas","numpy",
                  "nlp","transformers","scikit-learn","javascript","html","css","git","github"]
    rset = set(w.lower() for w in resume_text.split())
    found = [s for s in skills if s in rset and s in job_text.lower()]
    return sorted(set(found))
