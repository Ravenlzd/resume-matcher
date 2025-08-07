import json
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

model = SentenceTransformer('all-MiniLM-L6-v2')

def load_jobs(filepath="job_descriptions.json"):
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)

def embed_text(text):
    return model.encode([text])[0]

def find_best_matches(resume_text, jobs, top_n=3):
    resume_embedding = embed_text(resume_text)
    job_scores = []

    for job in jobs:
        job_embedding = embed_text(job["description"])
        similarity = cosine_similarity([resume_embedding], [job_embedding])[0][0]
        job_scores.append((job, similarity))

    job_scores.sort(key=lambda x: x[1], reverse=True)
    return job_scores[:top_n]
