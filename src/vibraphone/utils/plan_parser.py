"""GSD PLAN.md parsing utilities.

Provides pure parsing functions for extracting YAML frontmatter and XML task blocks
from GSD PLAN.md files. Uses defusedxml for safe XML parsing (prevents XXE attacks).

All functions are pure (no I/O) - callers handle file reading.
"""

import re

import yaml
from defusedxml.ElementTree import ParseError
from defusedxml.ElementTree import fromstring as parse_xml

# Regex pattern for YAML frontmatter between --- fences
_FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

# Regex pattern for <tasks>...</tasks> XML blocks
_TASKS_RE = re.compile(r"<tasks>(.*?)</tasks>", re.DOTALL)

# Regex pattern for bare & not part of XML entities
_BARE_AMP_RE = re.compile(r"&(?!(?:amp|lt|gt|apos|quot);)")

# Known structural XML tags in GSD plan files
_KNOWN_TAGS = [
    "tasks",
    "task",
    "name",
    "files",
    "action",
    "verify",
    "done",
    "title",
    "description",
    "labels",
    "type",
    "blocked_by",
]

# Regex pattern for < followed by known structural tags
_STRUCTURAL_TAG_RE = re.compile(r"<(?=" + "|".join(_KNOWN_TAGS) + r")")


def extract_frontmatter(content: str) -> dict:
    """Extract YAML frontmatter from between --- fences.

    Args:
        content: Raw file content (may or may not have frontmatter)

    Returns:
        Parsed YAML dict, or {} if no frontmatter found or parsing fails.
    """
    match = _FRONTMATTER_RE.match(content)
    if not match:
        return {}
    try:
        result = yaml.safe_load(match.group(1))
    except yaml.YAMLError:
        return {}
    else:
        return result if result is not None else {}


def sanitize_xml_content(raw: str) -> str:
    """Escape bare & and < not part of known XML structure.

    GSD plan files may contain unescaped characters in action/description blocks.
    This sanitizes them before XML parsing.

    Args:
        raw: Raw XML content (inside <tasks>...</tasks>)

    Returns:
        Sanitized XML string safe for parsing.
    """
    # First escape bare & that aren't part of XML entities
    result = _BARE_AMP_RE.sub("&amp;", raw)

    # Then escape < that aren't part of known structural tags
    # This is a simple approach - we replace < not followed by known tags
    parts = []
    last_end = 0
    for match in _STRUCTURAL_TAG_RE.finditer(result):
        parts.append(result[last_end : match.start()])
        parts.append("<")
        last_end = match.start() + 1
    parts.append(result[last_end:])

    # For simplicity, we need to escape < that aren't part of our known tags
    # Rebuild by checking each <
    result2 = ""
    i = 0
    while i < len(result):
        if result[i] == "<":
            # Check if this is a known tag
            found = False
            for tag in _KNOWN_TAGS:
                # Check for opening tag
                if result[i + 1 : i + 1 + len(tag)] == tag:
                    next_char_idx = i + 1 + len(tag)
                    if next_char_idx >= len(result) or result[next_char_idx] in " >/\n\t":
                        found = True
                        break
                # Check for closing tag
                if result[i + 1 : i + 2] == "/" and result[i + 2 : i + 2 + len(tag)] == tag:
                    next_char_idx = i + 2 + len(tag)
                    if next_char_idx >= len(result) or result[next_char_idx] in " >\n\t":
                        found = True
                        break
            if found:
                result2 += "<"
            else:
                result2 += "&lt;"
            i += 1
        else:
            result2 += result[i]
            i += 1

    return result2


def extract_tasks_from_xml(body: str) -> list[dict]:
    """Find <tasks>...</tasks> block and parse each <task> element.

    Args:
        body: Full file content (may or may not contain <tasks> block)

    Returns:
        List of task dicts with keys from child elements (title, description,
        labels, type, blocked_by, etc.). Empty list if no tasks found.
    """
    match = _TASKS_RE.search(body)
    if not match:
        return []

    # Sanitize XML content for safe parsing
    inner = sanitize_xml_content(match.group(1))
    xml_str = f"<tasks>{inner}</tasks>"

    try:
        root = parse_xml(xml_str)
    except ParseError:
        return []

    tasks = []
    for task_el in root.findall("task"):
        task_data = {}
        for child in task_el:
            task_data[child.tag] = (child.text or "").strip()
        tasks.append(task_data)

    return tasks


def detect_new_components(body: str) -> bool:
    """Heuristic check for new service/endpoint/component creation keywords.

    Used to identify plans that create new code components (as opposed to
    docs-only or configuration-only plans).

    Args:
        body: Full file content to analyze

    Returns:
        True if component creation keywords are detected, False otherwise.
    """
    keywords = [
        "create",
        "implement",
        "add",
        "new",
        "define",
        "endpoint",
        "service",
        "component",
        "module",
        "class",
        "function",
        "api",
        "handler",
        "route",
    ]

    body_lower = body.lower()

    # Look for task/action sections which contain actual work
    action_match = re.search(r"<action>(.*?)</action>", body, re.DOTALL | re.IGNORECASE)
    if action_match:
        action_text = action_match.group(1).lower()
        return any(kw in action_text for kw in keywords)

    return any(kw in body_lower for kw in keywords)
