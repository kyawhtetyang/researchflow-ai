from app.services.citations import score_source_quality


def test_quality_score_prefers_authoritative_research_like_sources():
    authoritative = {
        "title": "NIH Research Report on Domestic Animal Behavior",
        "url": "https://www.nih.gov/news-events/research-report",
        "content": "This research report summarizes study findings, data, methodology, and evidence from multiple surveys.",
        "score": 0.82,
    }
    blog_like = {
        "title": "My Pet Thoughts",
        "url": "https://example.medium.com/my-pet-thoughts",
        "content": "Subscribe for more pet tips and buy now from our sponsored links.",
        "score": 0.82,
    }

    assert score_source_quality(authoritative) > score_source_quality(blog_like)


def test_quality_score_is_bounded_below_one():
    saturated_candidate = {
        "title": "Comprehensive Research Analysis Report on AI Systems",
        "url": "https://www.nature.com/articles/example",
        "content": (
            "This study presents research findings, evidence, methodology, statistics, data, "
            "analysis, and report details across multiple sections."
        )
        * 20,
        "score": 0.99,
    }

    assert score_source_quality(saturated_candidate) < 1.0
