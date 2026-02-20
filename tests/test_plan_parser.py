"""Unit tests for plan_parser utilities."""

from vibraphone.utils.plan_parser import (
    detect_new_components,
    extract_frontmatter,
    extract_tasks_from_xml,
    sanitize_xml_content,
)


class TestExtractFrontmatter:
    """Tests for extract_frontmatter function."""

    def test_extracts_valid_frontmatter(self):
        """Should extract YAML frontmatter from between --- fences."""
        content = """---
phase: 06-bridge-stack-tools
plan: 01
---
<tasks>
</tasks>
"""
        result = extract_frontmatter(content)
        assert result["phase"] == "06-bridge-stack-tools"
        # YAML parses 01 as integer 1
        assert result["plan"] == 1

    def test_returns_empty_dict_for_no_frontmatter(self):
        """Should return empty dict if no frontmatter found."""
        content = "<tasks></tasks>"
        result = extract_frontmatter(content)
        assert result == {}

    def test_handles_empty_frontmatter(self):
        """Should handle empty frontmatter block."""
        content = "---\n---\n<tasks></tasks>"
        result = extract_frontmatter(content)
        assert result == {}

    def test_parses_depends_on_list(self):
        """Should parse depends_on as list."""
        content = '---\ndepends_on: ["05-01", "05-02"]\n---\n'
        result = extract_frontmatter(content)
        assert result["depends_on"] == ["05-01", "05-02"]

    def test_handles_malformed_yaml(self):
        """Should return empty dict for malformed YAML."""
        content = "---\nphase: [broken\n---\n"
        result = extract_frontmatter(content)
        assert result == {}

    def test_handles_null_yaml(self):
        """Should handle null YAML content."""
        content = "---\nnull\n---\n"
        result = extract_frontmatter(content)
        assert result == {}


class TestSanitizeXmlContent:
    """Tests for sanitize_xml_content function."""

    def test_escapes_bare_ampersand(self):
        """Should escape bare & as &amp;."""
        result = sanitize_xml_content("Tom & Jerry")
        assert result == "Tom &amp; Jerry"

    def test_preserves_xml_entities(self):
        """Should preserve existing XML entities."""
        result = sanitize_xml_content("&amp; &lt; &gt;")
        assert result == "&amp; &lt; &gt;"

    def test_escapes_bare_less_than(self):
        """Should escape < not part of known tags."""
        result = sanitize_xml_content("5 < 10")
        assert "5 &lt; 10" in result

    def test_preserves_structural_tags(self):
        """Should preserve known structural XML tags."""
        result = sanitize_xml_content("<task><title>Test</title></task>")
        assert "<task>" in result
        assert "<title>" in result

    def test_preserves_closing_tags(self):
        """Should preserve closing tags for known elements."""
        result = sanitize_xml_content("<task><title>Test</title></task>")
        assert "</task>" in result
        assert "</title>" in result

    def test_escapes_less_than_in_text(self):
        """Should escape < in regular text content."""
        result = sanitize_xml_content("<task>5 < 10</task>")
        assert "&lt;" in result

    def test_handles_empty_string(self):
        """Should handle empty input."""
        result = sanitize_xml_content("")
        assert result == ""

    def test_preserves_amp_in_entity(self):
        """Should not double-escape existing &amp;."""
        result = sanitize_xml_content("Tom &amp; Jerry")
        assert result == "Tom &amp; Jerry"


class TestExtractTasksFromXml:
    """Tests for extract_tasks_from_xml function."""

    def test_extracts_single_task(self):
        """Should extract a single task element."""
        body = """<tasks>
<task>
  <name>Task 1</name>
  <description>Description here</description>
</task>
</tasks>"""
        tasks = extract_tasks_from_xml(body)
        assert len(tasks) == 1
        assert tasks[0]["name"] == "Task 1"
        assert tasks[0]["description"] == "Description here"

    def test_extracts_multiple_tasks(self):
        """Should extract multiple task elements."""
        body = """<tasks>
<task><name>Task 1</name></task>
<task><name>Task 2</name></task>
</tasks>"""
        tasks = extract_tasks_from_xml(body)
        assert len(tasks) == 2

    def test_extracts_blocked_by_field(self):
        """Should extract optional blocked_by field."""
        body = """<tasks>
<task><name>Task 1</name></task>
<task>
  <name>Task 2</name>
  <blocked_by>Task 1</blocked_by>
</task>
</tasks>"""
        tasks = extract_tasks_from_xml(body)
        assert tasks[1]["blocked_by"] == "Task 1"

    def test_returns_empty_list_for_no_tasks(self):
        """Should return empty list if no tasks block found."""
        body = "No tasks here"
        tasks = extract_tasks_from_xml(body)
        assert tasks == []

    def test_handles_all_task_fields(self):
        """Should extract all standard task fields."""
        body = """<tasks>
<task>
  <name>Title</name>
  <description>Desc</description>
  <files>file.py</files>
  <action>Do something</action>
  <verify>Check result</verify>
  <done>Complete</done>
  <labels>plan:01-01</labels>
  <type>auto</type>
</task>
</tasks>"""
        tasks = extract_tasks_from_xml(body)
        task = tasks[0]
        assert task["name"] == "Title"
        assert task["description"] == "Desc"
        assert task["files"] == "file.py"
        assert task["action"] == "Do something"
        assert task["verify"] == "Check result"
        assert task["done"] == "Complete"
        assert task["labels"] == "plan:01-01"
        assert task["type"] == "auto"

    def test_handles_task_with_empty_elements(self):
        """Should handle task with empty element content."""
        body = """<tasks>
<task>
  <name>Task</name>
  <description></description>
</task>
</tasks>"""
        tasks = extract_tasks_from_xml(body)
        assert len(tasks) == 1
        assert tasks[0]["name"] == "Task"
        assert tasks[0]["description"] == ""

    def test_sanitizes_ampersand_in_content(self):
        """Should sanitize bare ampersands in task content."""
        body = """<tasks>
<task><name>Tom & Jerry</name></task>
</tasks>"""
        tasks = extract_tasks_from_xml(body)
        assert len(tasks) == 1
        assert tasks[0]["name"] == "Tom & Jerry"

    def test_handles_malformed_xml(self):
        """Should return empty list for unparseable XML."""
        body = "<tasks><task><name>Unclosed"
        tasks = extract_tasks_from_xml(body)
        assert tasks == []


class TestDetectNewComponents:
    """Tests for detect_new_components function."""

    def test_detects_new_service(self):
        """Should detect 'new service' keyword."""
        body = "Create a new service for auth"
        assert detect_new_components(body) is True

    def test_detects_create_endpoint(self):
        """Should detect 'create endpoint' keyword."""
        body = "Create endpoint for user API"
        assert detect_new_components(body) is True

    def test_detects_add_component(self):
        """Should detect 'add component' keyword."""
        body = "Add component for logging"
        assert detect_new_components(body) is True

    def test_returns_false_for_no_keywords(self):
        """Should return False when no keywords found."""
        body = "Fix the bug in existing code"
        assert detect_new_components(body) is False

    def test_case_insensitive(self):
        """Should be case insensitive."""
        body = "NEW SERVICE for auth"
        assert detect_new_components(body) is True

    def test_detects_implement(self):
        """Should detect 'implement' keyword."""
        body = "Implement new handler for requests"
        assert detect_new_components(body) is True

    def test_detects_define(self):
        """Should detect 'define' keyword."""
        body = "Define new module for utilities"
        assert detect_new_components(body) is True

    def test_detects_in_action_block(self):
        """Should detect keywords in <action> block."""
        body = """<tasks>
<task>
<action>Create a new API endpoint</action>
</task>
</tasks>"""
        assert detect_new_components(body) is True

    def test_false_for_docs_only(self):
        """Should return False for docs-only content."""
        body = "Update the README with installation instructions"
        assert detect_new_components(body) is False

    def test_detects_class_keyword(self):
        """Should detect 'class' keyword."""
        body = "Add a new class for user management"
        assert detect_new_components(body) is True

    def test_detects_function_keyword(self):
        """Should detect 'function' keyword."""
        body = "Create a new function for validation"
        assert detect_new_components(body) is True
