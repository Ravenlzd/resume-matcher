# 🚀 JobPulse — AI-Powered Job Matcher

JobPulse is an AI-powered job search platform that fetches live job postings from multiple sources and ranks them against your resume using semantic similarity and skill-based analysis.

👉 **Live Demo:** https://resumematcher3.streamlit.app

---

## ✨ Key Features

- 🔎 Fetch real-time jobs from Remotive & Greenhouse APIs  
- 📄 Upload PDF resume and extract text automatically  
- 🤖 Rank jobs using transformer-based semantic similarity  
- 🧠 Highlight matched skills between resume and job descriptions  
- ⭐ Save favorite jobs for later  
- 🔗 Apply directly via job links  
- 🎯 Search and filter by keyword, company, or location  

---

## 🧠 How It Works

1. Fetches live job postings from multiple APIs (Remotive + Greenhouse)  
2. Parses uploaded PDF resume into structured text  
3. Uses Sentence-Transformers (`all-MiniLM-L6-v2`) to compute semantic similarity  
4. Combines similarity with skill overlap scoring  
5. Ranks and displays the most relevant job opportunities  

---

## 🛠️ Tech Stack

- **Frontend/App**: Streamlit  
- **Backend**: Python  
- **NLP Model**: Sentence-Transformers  
- **Scoring**: Cosine similarity (scikit-learn)  
- **Parsing**: pdfplumber + BeautifulSoup  
- **Data Sources**: Remotive API + Greenhouse job boards  

---

## ▶️ Run Locally

```bash
git clone https://github.com/Ravenlzd/jobpulse.git
cd jobpulse

python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
streamlit run app.py
```

Then open http://localhost:8501 in your browser 🚀

---

## 🌍 Deployment

This project is deployed using **Streamlit Community Cloud**.

---

## 📸 Screenshots

![App Screenshot](screenshots/Screenshot%202025-08-16%20191851.png)  
![App Screenshot](screenshots/Screenshot%202025-08-16%20191930.png)  
![App Screenshot](screenshots/Screenshot%202025-08-16%20192056.png)

---

## 🚀 Future Improvements

- Add missing skills analysis (show gaps between resume and job requirements)  
- Advanced filters (salary, remote-only, experience level)  
- Export matched jobs to PDF/CSV  
- Migrate to FastAPI backend + React frontend  
- Add more job sources (LinkedIn, Indeed, etc.)  

---

## 📄 License

© 2025 Ravan Alizada