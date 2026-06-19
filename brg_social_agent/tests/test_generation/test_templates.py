def test_render_content_prompt_includes_topic():
    from engines.generation.templates import render_content_prompt
    prompt = render_content_prompt(
        topic="Executive Presence",
        context="How leaders build trust in high-stakes situations",
        source="Harvard Business Review",
    )
    assert "Executive Presence" in prompt
    assert "How leaders build trust in high-stakes situations" in prompt
    assert "Harvard Business Review" in prompt


def test_render_content_prompt_includes_json_structure():
    from engines.generation.templates import render_content_prompt
    prompt = render_content_prompt(topic="T", context="C", source="S")
    for key in ('"carousel"', '"post"', '"script"', '"quote"', '"story"', '"hashtags"', '"keywords"'):
        assert key in prompt, f"Missing key: {key}"


def test_render_content_prompt_includes_mood_constraint():
    from engines.generation.templates import render_content_prompt
    prompt = render_content_prompt(topic="T", context="C", source="S")
    assert '"light"' in prompt
    assert '"dark"' in prompt


def test_brg_system_prompt_forbids_cliches():
    from engines.generation.templates import BRG_SYSTEM_PROMPT
    for cliche in ("game changer", "level up", "crush it", "hustle", "grind"):
        assert cliche in BRG_SYSTEM_PROMPT, f"Missing forbidden word: {cliche}"


def test_brg_system_prompt_requires_json_only():
    from engines.generation.templates import BRG_SYSTEM_PROMPT
    assert "JSON" in BRG_SYSTEM_PROMPT
    assert "no markdown" in BRG_SYSTEM_PROMPT.lower() or "no preamble" in BRG_SYSTEM_PROMPT.lower()


def test_render_quality_prompt_includes_all_content():
    from engines.generation.templates import render_quality_prompt
    prompt = render_quality_prompt(
        post_body="Leadership is about execution.",
        carousel_hook_title="The Truth About Leadership",
        carousel_hook_body="Most leaders never execute.",
    )
    assert "Leadership is about execution." in prompt
    assert "The Truth About Leadership" in prompt
    assert "Most leaders never execute." in prompt


def test_render_quality_prompt_lists_forbidden_cliches():
    from engines.generation.templates import render_quality_prompt
    prompt = render_quality_prompt(post_body="B", carousel_hook_title="T", carousel_hook_body="H")
    for cliche in ("game changer", "crush it", "level up"):
        assert cliche in prompt, f"Missing cliché check: {cliche}"


def test_render_quality_prompt_requests_json_output():
    from engines.generation.templates import render_quality_prompt
    prompt = render_quality_prompt(post_body="B", carousel_hook_title="T", carousel_hook_body="H")
    assert '"passes"' in prompt
    assert '"reason"' in prompt
