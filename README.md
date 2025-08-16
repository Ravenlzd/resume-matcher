# 🌐 JobPulse — Live Job Finder

A real-time job search and resume matcher that fetches live job postings from multiple sources (Remotive + Greenhouse boards), lets you search/filter them, and ranks jobs against your resume using semantic similarity.  

Built with **Streamlit**, **Sentence-Transformers**, and **BeautifulSoup**.

---

## 🚀 Features

✅ Fetch live jobs automatically on page load  
✅ Search and filter jobs by keywords, company, or location  
✅ Upload your resume (PDF) and preview the extracted text  
✅ Rank jobs by match score (semantic similarity with transformers)  
✅ Highlight matched skills between your resume and job descriptions  
✅ Save favorite jobs for later  
✅ Apply directly via job links  
✅ Clean, interactive UI  

---

## 🧠 How It Works

1. On load, JobPulse fetches the latest jobs from:
   - [Remotive.io](https://remotive.io)
   - Greenhouse boards (you can add company tokens like `stripe`, `airbnb`, `openai`)
2. Upload your resume (PDF) — text is extracted and stored.
3. Jobs are scored against your resume using a transformer model (`all-MiniLM-L6-v2`).
4. You can search/filter, rank by relevance, and save jobs you like.
5. Apply directly from the app.

---

## 📸 Screenshots

[(screenshots/Screenshot 2025-08-16 191851.png)    (screenshots/Screenshot 2025-08-16 191930.png)   (screenshots/Screenshot 2025-08-16 192056.png)]

[(screenshots/Screenshot 2025-08-16 192115.png)    (screenshots/Screenshot 2025-08-16 192132.png)   (screenshots/Screenshot 2025-08-16 192231.png)]

## 🛠️ Tech Stack

- **Frontend & App**: [Streamlit](https://streamlit.io/)  
- **Job Sources**: Remotive API + Greenhouse job boards  
- **NLP & Matching**: [Sentence-Transformers](https://www.sbert.net/)  
- **Scoring**: Cosine similarity (`scikit-learn`)  
- **PDF Parsing**: `pdfplumber`  
- **HTML Parsing**: `BeautifulSoup`  

---

## 📂 File Structure



