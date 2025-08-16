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


## 🛠️ Tech Stack

- **Frontend & App**: [Streamlit](https://streamlit.io/)  
- **Job Sources**: Remotive API + Greenhouse job boards  
- **NLP & Matching**: [Sentence-Transformers](https://www.sbert.net/)  
- **Scoring**: Cosine similarity (`scikit-learn`)  
- **PDF Parsing**: `pdfplumber`  
- **HTML Parsing**: `BeautifulSoup`  

---

## ▶️ Run Locally

bash
# Clone repo
git clone https://github.com/Ravenlzd/jobpulse.git
cd jobpulse

# Install dependencies
pip install -r requirements.txt

# Start app
streamlit run app.py
Then open http://localhost:8501 in your browser 🚀

---

## 🌍 Deployment

You can deploy JobPulse on:

Streamlit Community Cloud (free, easiest)

Railway / Render for broader hosting

## 📌 Roadmap

 Add support for LinkedIn / Indeed APIs

 Advanced filtering (salary, remote-only, etc.)

 Export matched jobs to PDF/CSV

 Deploy as a standalone web app (beyond Streamlit)

$$🤝 Contributing

Pull requests are welcome! Open an issue for suggestions or bugs.

## 📄 License

 © 2025 Ravan Alizada

---

## 📸 Screenshots

![Screenshot 1](screenshots/Screenshot%202025-08-16%20191851.png)
![Screenshot 2](screenshots/Screenshot%202025-08-16%20191930.png)
![Screenshot 3](screenshots/Screenshot%202025-08-16%20192056.png)
![Screenshot 4](screenshots/Screenshot%202025-08-16%20192115.png)
![Screenshot 5](screenshots/Screenshot%202025-08-16%20192132.png)
![Screenshot 6](screenshots/Screenshot%202025-08-16%20192231.png)




