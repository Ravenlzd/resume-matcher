import sources


def test_fetch_remotive_normalizes_fields(monkeypatch):
    def fake_request_json(url, params=None, timeout=30):
        assert "remotive.com" in url
        return {
            "jobs": [
                {
                    "id": 123,
                    "title": "Backend Engineer",
                    "company_name": "Acme",
                    "candidate_required_location": "",
                    "tags": ["python"],
                    "url": "https://example.com/job/123",
                    "description": "<p>Build APIs</p>",
                    "publication_date": "2026-03-01T00:00:00",
                }
            ]
        }

    monkeypatch.setattr(sources, "_request_json", fake_request_json)
    jobs = sources.fetch_remotive(limit=5)

    assert len(jobs) == 1
    j = jobs[0]
    assert j["source"] == "remotive"
    assert j["source_job_id"] == "123"
    assert j["location"] == "Remote"
    assert j["remote"] is True


def test_fetch_greenhouse_uses_detail_fallback(monkeypatch):
    def fake_request_json(url, params=None, timeout=30):
        if url.endswith("/jobs"):
            return {
                "jobs": [
                    {
                        "id": 999,
                        "title": "Customer Success Manager",
                        "company": {"name": "Beta"},
                        "location": {"name": "Remote - USA"},
                        "departments": [{"name": "Support"}],
                        "absolute_url": "https://boards.example/jobs/999",
                        "content": "",
                        "updated_at": "2026-03-01T00:00:00Z",
                    }
                ]
            }
        if url.endswith("/jobs/999"):
            return {"content": "<p>Full detail description</p>"}
        raise AssertionError(f"unexpected url {url}")

    monkeypatch.setattr(sources, "_request_json", fake_request_json)
    jobs = sources.fetch_greenhouse_board("beta")

    assert len(jobs) == 1
    j = jobs[0]
    assert j["source"] == "greenhouse:beta"
    assert j["remote"] is True
    assert "Full detail" in j["description"]
    assert j["posted_at"] == "2026-03-01T00:00:00Z"


def test_merge_dedupe_keeps_first_seen():
    a = [{"source": "x", "source_job_id": "1", "title": "A"}]
    b = [{"source": "x", "source_job_id": "1", "title": "B"}]
    out = sources.merge_dedupe([a, b])
    assert len(out) == 1
    assert out[0]["title"] == "A"
