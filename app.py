import streamlit as st
from resume_parser import extract_text_from_pdf
from job_matcher import load_jobs, find_best_matches
from cover_letter import generate_template_letter

st.set_page_config(page_title="AI Resume Matcher", layout="centered")
st.title("🎯 AI-Powered Resume Matcher")

uploaded_file = st.file_uploader("Upload your resume (PDF only)", type=["pdf"])

# ✅ Initialize session state
if "resume_text" not in st.session_state:
    st.session_state.resume_text = ""

if "matches" not in st.session_state:
    st.session_state.matches = []

# ✅ Extract and store resume text
if uploaded_file:
    with st.spinner("Extracting text..."):
        st.session_state.resume_text = extract_text_from_pdf(uploaded_file)

# ✅ Show resume preview if available
if st.session_state.resume_text:
    st.success("Resume text extracted successfully!")
    st.subheader("Resume Preview")
    st.text_area("Resume Content", st.session_state.resume_text, height=300)

# ✅ Match jobs
if st.session_state.resume_text and st.button("Find Job Matches"):
    with st.spinner("Matching jobs..."):
        jobs = load_jobs()
        st.session_state.matches = find_best_matches(st.session_state.resume_text, jobs)

# ✅ Show matches if they exist
if st.session_state.matches:
    st.subheader("🔍 Top Job Matches:")

    for job, score in st.session_state.matches:
        st.markdown(f"**{job['title']}** at *{job['company']}*")
        st.markdown(f"**Match Score:** {round(score * 100, 2)}%")
        with st.expander("Job Description"):
            st.write(job['description'])
        st.markdown("---")

    # ✅ Generate cover letter for top match
    top_match = st.session_state.matches[0][0]
    if st.button("✉️ Generate Cover Letter for Top Match"):
        cover_letter = generate_template_letter(
            st.session_state.resume_text,
            top_match['title'],
            top_match['company'],
            top_match['description']
        )
        st.subheader("📄 Generated Cover Letter")
        st.text_area("Cover Letter", cover_letter, height=300)
