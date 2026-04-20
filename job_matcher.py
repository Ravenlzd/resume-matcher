import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer("all-MiniLM-L6-v2")

COMMON_SKILLS = [
    "python", "java", "c++", "javascript", "typescript",
    "sql", "mysql", "postgresql", "mongodb",
    "docker", "kubernetes", "aws", "gcp", "azure",
    "streamlit", "fastapi", "flask", "django", "react", "node",
    "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
    "nlp", "transformers", "machine learning", "deep learning",
    "git", "github", "html", "css", "rest", "api"
]

def load_jobs(filepath="job_descriptions.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def embed_text(text):
    return model.encode([text])[0]

def extract_skills(text, skills=None):
    if not text:
        return set()

    if skills is None:
        skills = COMMON_SKILLS

    text_lower = text.lower()
    found = set()

    for skill in skills:
        if skill.lower() in text_lower:
            found.add(skill)

    return found

def get_skill_analysis(resume_text, job_text, skills=None):
    resume_skills = extract_skills(resume_text, skills)
    job_skills = extract_skills(job_text, skills)

    matched = sorted(resume_skills & job_skills)
    missing = sorted(job_skills - resume_skills)

    return matched, missing

def find_best_matches(resume_text, jobs, top_n=3):
    resume_embedding = embed_text(resume_text)
    resume_skills = extract_skills(resume_text)

    job_scores = []

    for job in jobs:
        job_text = f"{job.get('title', '')} {job.get('description', '')}"
        job_embedding = embed_text(job_text)

        semantic_score = cosine_similarity([resume_embedding], [job_embedding])[0][0]

        matched_skills, missing_skills = get_skill_analysis(resume_text, job_text)
        job_skills = extract_skills(job_text)

        skill_score = len(matched_skills) / len(job_skills) if job_skills else 0

        final_score = (0.7 * semantic_score) + (0.3 * skill_score)

        enriched_job = {
            **job,
            "matched_skills": matched_skills,
            "missing_skills": missing_skills,
            "semantic_score": float(semantic_score),
            "final_score": float(final_score),
        }

        job_scores.append((enriched_job, final_score))

    job_scores.sort(key=lambda x: x[1], reverse=True)
    return job_scores[:top_n]