from app.agent.output_constraints import enforce_bullet_count


def count_top_level_bullets(answer: str) -> int:
    return sum(
        1 for line in answer.splitlines()
        if line.startswith(("- ", "* ", "+ "))
    )


def test_merges_six_bullets_into_exactly_five():
    answer = "\n".join([
        "- ai-services: AI services",
        "- backend: Server code",
        "- cli: Command-line interface",
        "- docker: Container configuration",
        "- docs: Documentation",
        "- frontend: Web interface",
    ])

    result = enforce_bullet_count(
        "List folders in exactly 5 bullet points.",
        answer,
    )

    assert count_top_level_bullets(result) == 5
    assert "docker: Container configuration; docs: Documentation" in result
    assert "\n- frontend: Web interface" in result


def test_merges_seven_bullets_into_exactly_five():
    answer = "\n".join(f"- Item {i}" for i in range(1, 8))

    result = enforce_bullet_count(
        "Use exactly 5 bullet points.",
        answer,
    )

    assert count_top_level_bullets(result) == 5
    assert "Item 4; Item 5; Item 6" in result
    assert "Item 7" in result


def test_does_not_change_answer_without_exact_count():
    answer = "- One\n- Two"
    assert enforce_bullet_count("List the folders.", answer) == answer


def test_leaves_shorter_list_unchanged():
    answer = "- One\n- Two"
    assert enforce_bullet_count(
        "Use exactly 3 bullet points.", answer
    ) == answer


def test_nested_bullets_do_not_count_as_top_level():
    answer = "- One\n- Two\n  - Nested detail\n- Three"
    result = enforce_bullet_count("Use exactly 3 bullet points.", answer)
    assert result == answer


def test_merges_extra_bullet_with_readable_separator():
    answer = "\n".join([
        "- ai-services: AI services",
        "- backend: Server code",
        "- cli: Command-line interface",
        "- docker: Container configuration",
        "- docs: Documentation",
        "- frontend: Web interface",
    ])

    result = enforce_bullet_count(
        "List folders in exactly 5 bullet points.",
        answer,
    )

    assert "- docker: Container configuration; docs: Documentation" in result
    assert count_top_level_bullets(result) == 5
    assert "\n- frontend: Web interface" in result
