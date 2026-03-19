import re
from typing import Dict, List, Set, Tuple

_model = None
_embedding_cache: Dict[str, List[float]] = {}

COMMON_SKILLS = [
    # Engineering / data
    "python", "java", "c++", "javascript", "typescript",
    "sql", "mysql", "postgresql", "mongodb",
    "docker", "kubernetes", "aws", "gcp", "azure",
    "streamlit", "fastapi", "flask", "django", "react", "node",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    "nlp", "transformers", "machine learning", "deep learning",
    "git", "github", "html", "css", "rest api", "api",
    # Customer success / support / ops
    "customer success", "customer support", "customer service",
    "account management", "client onboarding", "retention",
    "crm", "salesforce", "zendesk", "hubspot", "intercom",
    "email support", "chat support", "phone support",
    "troubleshooting", "ticketing", "sla",
    "excel", "google sheets", "reporting", "data analysis",
    "communication", "written communication", "verbal communication",
    "presentation", "cross-functional collaboration", "project management",
    "stakeholder management", "time management", "problem solving",
]

SKILL_ALIASES = {
    "customer success": ["customer success", "customer retention", "client success"],
    "customer support": ["customer support", "technical support"],
    "customer service": ["customer service"],
    "account management": ["account management", "account manager"],
    "client onboarding": ["onboarding", "client onboarding"],
    "cross-functional collaboration": ["cross-functional", "cross functional"],
    "project management": ["project management", "project manager"],
    "stakeholder management": ["stakeholder management", "stakeholders"],
    "problem solving": ["problem solving", "analytical thinking"],
    "rest api": ["rest api", "restful api"],
    "crm": ["crm", "customer relationship management"],
    "javascript": ["javascript", "js"],
    "typescript": ["typescript", "ts"],
}

REQUIRED_HINTS = [
    "required",
    "requirements",
    "must have",
    "must",
    "you have",
    "minimum qualifications",
]

NICE_HINTS = [
    "preferred",
    "nice to have",
    "plus",
    "bonus",
    "would be a plus",
]


def get_model():
    global _model
    if _model is None:
        # Lazy import keeps lightweight tooling (e.g., CI tests) fast.
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
    return _model


def get_job_text(job: dict) -> str:
    return f'{job.get("title", "")} {job.get("description", "")}'.strip()


def _normalize_space(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()


def _split_sentences(text: str) -> List[str]:
    text = _normalize_space(text)
    if not text:
        return []
    return [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]


def _contains_phrase(text_lower: str, phrase: str) -> bool:
    pattern = r"\b" + re.escape(phrase.lower()) + r"\b"
    return re.search(pattern, text_lower) is not None


def extract_skills(text: str, skills=None) -> Set[str]:
    """Extract canonical skills found in text based on aliases."""
    if not text:
        return set()

    if skills is None:
        skills = COMMON_SKILLS

    text_lower = text.lower()
    found = set()

    for skill in skills:
        variants = SKILL_ALIASES.get(skill, [skill])
        if any(_contains_phrase(text_lower, variant) for variant in variants):
            found.add(skill)

    return found


def _extract_weighted_job_skills(job_text: str, skills=None) -> Dict[str, float]:
    """
    Extract skill weights from job text.
    Base skill weight is 1.0, boosted if appears in requirement language,
    reduced if appears only in nice-to-have language.
    """
    if skills is None:
        skills = COMMON_SKILLS

    sentences = _split_sentences(job_text)
    if not sentences:
        return {}

    weights: Dict[str, float] = {}
    for sentence in sentences:
        sent_lower = sentence.lower()
        required = any(h in sent_lower for h in REQUIRED_HINTS)
        nice = any(h in sent_lower for h in NICE_HINTS)

        for skill in skills:
            variants = SKILL_ALIASES.get(skill, [skill])
            if not any(_contains_phrase(sent_lower, variant) for variant in variants):
                continue

            w = 1.0
            if required:
                w = 1.6
            elif nice:
                w = 0.7
            weights[skill] = max(weights.get(skill, 0.0), w)

    return weights


def get_skill_analysis(resume_text: str, job_text: str, skills=None) -> Tuple[List[str], List[str]]:
    """
    Returns matched and missing skills.
    Missing skills are ordered by importance (required first).
    """
    resume_skills = extract_skills(resume_text, skills)
    job_weights = _extract_weighted_job_skills(job_text, skills)
    job_skills = set(job_weights.keys()) if job_weights else extract_skills(job_text, skills)

    matched = sorted(resume_skills & job_skills)
    missing = sorted(
        job_skills - resume_skills,
        key=lambda s: job_weights.get(s, 1.0),
        reverse=True,
    )
    return matched, missing


def get_match_explanation(resume_text: str, job_text: str, max_snippets: int = 2) -> Dict[str, List[str]]:
    """Explain why a job matches with weighted gaps and supporting snippets."""
    resume_skills = extract_skills(resume_text)
    job_weights = _extract_weighted_job_skills(job_text)
    job_skills = set(job_weights.keys()) if job_weights else extract_skills(job_text)

    matched = sorted(resume_skills & job_skills)
    missing_required = sorted([s for s in (job_skills - resume_skills) if job_weights.get(s, 1.0) >= 1.5])
    missing_optional = sorted([s for s in (job_skills - resume_skills) if job_weights.get(s, 1.0) < 1.5])

    snippets = []
    if job_text:
        for sentence in _split_sentences(job_text):
            sl = sentence.lower()
            if any(_contains_phrase(sl, v) for skill in matched[:6] for v in SKILL_ALIASES.get(skill, [skill])):
                snippets.append(sentence[:220])
            if len(snippets) >= max_snippets:
                break

    return {
        "matched": matched,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "snippets": snippets,
    }


def _encode_texts(texts: List[str]):
    """Encode texts with a tiny in-memory cache to avoid repeated work across reruns."""
    m = get_model()
    to_compute = [t for t in texts if t not in _embedding_cache]
    if to_compute:
        computed = m.encode(to_compute)
        for text, emb in zip(to_compute, computed):
            _embedding_cache[text] = emb
    return [_embedding_cache[t] for t in texts]


def score_resume_to_jobs(resume_text: str, jobs: list, top_n: int = 20):
    """
    Rank jobs using a hybrid score:
    75% semantic similarity + 25% weighted skill coverage.
    Output: list of tuples (job_dict, score_float)
    """
    if not resume_text or not jobs:
        return []

    texts = [get_job_text(j) for j in jobs]
    r_emb = _encode_texts([resume_text])[0]
    j_embs = _encode_texts(texts)

    # Lazy import keeps module import cheap for tests that don't score embeddings.
    from sklearn.metrics.pairwise import cosine_similarity
    semantic = cosine_similarity([r_emb], j_embs)[0]

    resume_skills = extract_skills(resume_text)
    hybrid_scores = []

    for i, job in enumerate(jobs):
        job_text = texts[i]
        weighted = _extract_weighted_job_skills(job_text)
        if not weighted:
            weighted = {s: 1.0 for s in extract_skills(job_text)}

        total_w = sum(weighted.values()) or 1.0
        matched_w = sum(w for s, w in weighted.items() if s in resume_skills)
        skill_score = matched_w / total_w

        score = 0.75 * float(semantic[i]) + 0.25 * float(skill_score)
        hybrid_scores.append((job, score))

    ranked = sorted(hybrid_scores, key=lambda x: x[1], reverse=True)
    return ranked[:top_n]


def extract_matched_skills(resume_text: str, job_text: str, skills=None):
    """Backward-compatible helper for existing code."""
    matched, _ = get_skill_analysis(resume_text, job_text, skills)
    return matched
