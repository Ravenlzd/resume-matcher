from matching import extract_skills, get_match_explanation, get_skill_analysis


def test_extract_skills_alias_and_word_boundary():
    text = "Strong customer retention and CRM experience. Built in JavaScript."
    found = extract_skills(text)
    assert "customer success" in found  # alias from customer retention
    assert "crm" in found
    assert "javascript" in found
    assert "java" not in found  # should not match inside javascript


def test_get_skill_analysis_prioritizes_required_missing():
    resume = "Experience with customer success and communication."
    job = (
        "Required: customer success, salesforce, account management, communication. "
        "Nice to have: sql."
    )
    matched, missing = get_skill_analysis(resume, job)

    assert "customer success" in matched
    assert "communication" in matched
    assert "salesforce" in missing
    assert "account management" in missing
    assert "sql" in missing
    # Required gaps should come before optional gap.
    assert missing.index("salesforce") < missing.index("sql")


def test_get_match_explanation_contains_expected_sections():
    resume = "Customer success manager with onboarding and salesforce."
    job = "Required: customer success, salesforce, communication. Nice to have: sql."
    out = get_match_explanation(resume, job)

    assert "matched" in out
    assert "missing_required" in out
    assert "missing_optional" in out
    assert "snippets" in out
    assert "customer success" in out["matched"]
    assert "communication" in out["missing_required"]
    assert "sql" in out["missing_optional"]
