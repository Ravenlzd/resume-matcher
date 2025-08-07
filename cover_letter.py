def generate_template_letter(resume_text, job_title, company, job_description):
    name = "Your Name"  # Optionally, extract from resume_text in the future

    intro = f"Dear {company} Team,\n\n"

    body = (
        f"I am writing to express my interest in the {job_title} position at {company}. "
        "As an AI Systems student with hands-on experience in Python, backend development, and multilingual communication, "
        "I believe I can bring value to your team."
    )

    highlights = (
        "\n\nFrom my resume, you'll see that I've:\n"
        "- Built microservice-based applications with Docker & SQLAlchemy\n"
        "- Handled multilingual AI tools\n"
        "- Worked with REST APIs, data pipelines, and scalable code\n"
    )

    connection = (
        "\nYour job description caught my attention because it highlights key areas I enjoy working in, such as:\n"
        f"{job_description[:150]}..."  # Clip long text
    )

    close = (
        "\n\nI would welcome the opportunity to discuss how my background aligns with your goals. "
        "Thank you for considering my application.\n\n"
        f"Sincerely,\n{name}"
    )

    return intro + body + highlights + connection + close
