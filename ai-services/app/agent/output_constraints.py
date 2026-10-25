import re


TOP_LEVEL_BULLET_PATTERN = re.compile(r"^[-*+]\s+")


def enforce_bullet_count(message: str, answer: str) -> str:
    """Merge excess top-level bullets until the requested count is reached."""

    match = re.search(
        r"\bexactly\s+(\d+)\s+(?:bullet\s+points?|bullets?)\b",
        message,
        flags=re.IGNORECASE,
    )

    if not match:
        return answer

    target = int(match.group(1))

    if target < 2:
        return answer

    lines = answer.splitlines()

    while True:
        bullet_indexes = [
            i for i, line in enumerate(lines)
            if TOP_LEVEL_BULLET_PATTERN.match(line)
        ]

        if len(bullet_indexes) <= target:
            break

        # Merge adjacent bullets near the end of the requested list.
        first_index = bullet_indexes[target - 2]
        second_index = bullet_indexes[target - 1]

        first_text = lines[first_index].strip()
        second_text = re.sub(
            r"^[-*+]\s+", "", lines[second_index].strip()
        )

        lines[first_index] = first_text + "; " + second_text
        del lines[second_index]

    return "\n".join(lines)
