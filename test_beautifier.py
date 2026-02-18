"""
Unit tests for beautifier node
Tests markdown parsing, font sizing, alignment, and node integration.

Run: pytest test_beautifier.py -v
"""
import pytest
from src.nodes.pipeline_2_generation.beautifier import (
    parse_markdown,
    _safe_int,
    _determine_font_size,
    _alignment_for_role,
    beautifier_node,
    FONT_SIZE_TITLE_LARGE,
    FONT_SIZE_TITLE_SMALL,
    FONT_SIZE_BODY_LARGE,
    FONT_SIZE_BODY_DEFAULT,
    FONT_SIZE_FOOTER,
)


# --- Markdown Parsing Tests ---

def test_parse_markdown_plain_text():
    """Plain text should return a single plain run"""
    assert parse_markdown("Hello World") == [
        {"text": "Hello World", "bold": False, "italic": False}
    ]


def test_parse_markdown_bold():
    """Bold markers should be parsed correctly"""
    assert parse_markdown("**Bold**") == [
        {"text": "Bold", "bold": True, "italic": False}
    ]


def test_parse_markdown_italic():
    """Italic markers should be parsed correctly"""
    assert parse_markdown("*Italic*") == [
        {"text": "Italic", "bold": False, "italic": True}
    ]


def test_parse_markdown_mixed():
    """Mixed plain, bold, and italic text"""
    runs = parse_markdown("Plain **bold** and *italic* text")
    assert runs == [
        {"text": "Plain ", "bold": False, "italic": False},
        {"text": "bold", "bold": True, "italic": False},
        {"text": " and ", "bold": False, "italic": False},
        {"text": "italic", "bold": False, "italic": True},
        {"text": " text", "bold": False, "italic": False},
    ]


def test_parse_markdown_escaped_asterisks():
    """Escaped asterisks should be treated as literals"""
    runs = parse_markdown(r"literal \*star\* and \**double**")
    # All escaped, so should be plain text
    assert runs == [
        {"text": "literal *star* and **double**", "bold": False, "italic": False}
    ]


def test_parse_markdown_unbalanced_markers():
    """Unbalanced markers should fall back to plain text"""
    runs = parse_markdown("Start **bold only")
    # Unbalanced, return as plain text
    assert runs == [
        {"text": "Start **bold only", "bold": False, "italic": False}
    ]


def test_parse_markdown_unbalanced_italic():
    """Unbalanced italic should fall back to plain text"""
    runs = parse_markdown("Start *italic only")
    assert runs == [
        {"text": "Start *italic only", "bold": False, "italic": False}
    ]


def test_parse_markdown_inside_words_ignored():
    """Markers inside words should not format (word boundary check)"""
    runs = parse_markdown("fi*sh*ing and un**der**score")
    # Should treat as plain text because markers are inside words
    assert runs == [
        {"text": "fi*sh*ing and un**der**score", "bold": False, "italic": False}
    ]


def test_parse_markdown_none_input():
    """None input should return empty string run"""
    assert parse_markdown(None) == [
        {"text": "", "bold": False, "italic": False}
    ]


def test_parse_markdown_empty_string():
    """Empty string should return empty run"""
    assert parse_markdown("") == [
        {"text": "", "bold": False, "italic": False}
    ]


def test_parse_markdown_nested_emphasis():
    """Nested emphasis should be handled (toggles on/off)"""
    # **bold *italic* inside** → bold-on, italic-on, italic-off, bold-off
    runs = parse_markdown("**bold *nested* inside**")
    # This is a complex case; the parser toggles states
    # Expected: plain(**) → "bold " → plain(*) → "nested" → plain(*) → " inside" → plain(**)
    # Since both markers close properly, should work
    assert len(runs) > 1  # Should have multiple runs


def test_parse_markdown_multiple_bold_runs():
    """Multiple bold runs in same text"""
    runs = parse_markdown("**First** and **Second**")
    assert runs == [
        {"text": "First", "bold": True, "italic": False},
        {"text": " and ", "bold": False, "italic": False},
        {"text": "Second", "bold": True, "italic": False},
    ]


def test_parse_markdown_adjacent_markers():
    """Adjacent markers (bold then italic)"""
    runs = parse_markdown("**bold***italic*")
    # **bold** followed by *italic*
    # This should parse as bold then italic
    assert len(runs) == 2
    assert runs[0] == {"text": "bold", "bold": True, "italic": False}
    assert runs[1] == {"text": "italic", "bold": False, "italic": True}


# --- Safe Int Tests ---

def test_safe_int_valid_string():
    """Valid numeric string should convert"""
    assert _safe_int("42") == 42


def test_safe_int_valid_int():
    """Int should pass through"""
    assert _safe_int(42) == 42


def test_safe_int_invalid_string():
    """Non-numeric string should return None"""
    assert _safe_int("abc") is None


def test_safe_int_none():
    """None should return None"""
    assert _safe_int(None) is None


def test_safe_int_float():
    """Float should convert to int"""
    assert _safe_int(42.7) == 42


# --- Font Size Determination Tests ---

def test_font_size_title_large():
    """Large title area should get large font"""
    assert _determine_font_size("title", 0.1) == FONT_SIZE_TITLE_LARGE


def test_font_size_title_small():
    """Small title area should get small font"""
    assert _determine_font_size("title", 0.04) == FONT_SIZE_TITLE_SMALL


def test_font_size_header_large():
    """Header treated as title"""
    assert _determine_font_size("header", 0.1) == FONT_SIZE_TITLE_LARGE


def test_font_size_body_large():
    """Large body area should get large body font"""
    assert _determine_font_size("body", 0.4) == FONT_SIZE_BODY_LARGE


def test_font_size_body_default():
    """Medium body area should get default body font"""
    assert _determine_font_size("body", 0.2) == FONT_SIZE_BODY_DEFAULT


def test_font_size_footer():
    """Footer should get small font"""
    assert _determine_font_size("footer", 0.05) == FONT_SIZE_FOOTER


def test_font_size_unknown_role():
    """Unknown role should get fallback font"""
    assert _determine_font_size("unknown", 0.2) == 16  # FONT_SIZE_FALLBACK


def test_font_size_content():
    """Content role should scale with area"""
    # Content large (>0.15)
    assert _determine_font_size("content", 0.2) == 16
    # Content small (<0.15)
    assert _determine_font_size("content", 0.1) == 14


# --- Alignment Tests ---

def test_alignment_title():
    """Title should be centered"""
    assert _alignment_for_role("title") == "CENTER"


def test_alignment_header():
    """Header should be centered"""
    assert _alignment_for_role("header") == "CENTER"


def test_alignment_headline():
    """Headline should be centered"""
    assert _alignment_for_role("headline") == "CENTER"


def test_alignment_caption():
    """Caption should be centered"""
    assert _alignment_for_role("caption") == "CENTER"


def test_alignment_number():
    """Number should be right-aligned"""
    assert _alignment_for_role("number") == "RIGHT"


def test_alignment_metric():
    """Metric should be right-aligned"""
    assert _alignment_for_role("metric") == "RIGHT"


def test_alignment_body():
    """Body should be left-aligned"""
    assert _alignment_for_role("body") == "LEFT"


def test_alignment_default():
    """Unknown role should be left-aligned"""
    assert _alignment_for_role("unknown") == "LEFT"


def test_alignment_case_insensitive():
    """Alignment should be case-insensitive"""
    assert _alignment_for_role("TITLE") == "CENTER"
    assert _alignment_for_role("Header") == "CENTER"


# --- Beautifier Node Integration Tests ---

def test_beautifier_node_basic():
    """Basic beautifier node functionality"""
    state = {
        "manifest": [
            {
                "layout_index": 0,
                "content": {"1": "**Title** Text"}
            }
        ],
        "registry": {
            "layouts": [
                {
                    "layout_index": 0,
                    "layout_name": "Title Slide",
                    "slots": [
                        {
                            "slot_id": 1,
                            "role_hint": "title",
                            "geometry": {"area_ratio": 0.1},
                            "max_chars": 100
                        }
                    ]
                }
            ]
        }
    }
    
    result = beautifier_node(state)
    manifest = result["manifest"]
    
    assert len(manifest) == 1
    assert manifest[0]["layout_index"] == 0
    assert "1" in manifest[0]["content"]
    
    styled = manifest[0]["content"]["1"]
    assert "runs" in styled
    assert styled["runs"][0]["text"] == "Title"
    assert styled["runs"][0]["bold"] is True
    assert styled["font_size"] == FONT_SIZE_TITLE_LARGE
    assert styled["alignment"] == "CENTER"


def test_beautifier_node_unknown_layout_fallback():
    """Unknown layout should fallback to first layout"""
    state = {
        "manifest": [
            {
                "layout_index": 999,  # Non-existent
                "content": {"1": "Title"}
            }
        ],
        "registry": {
            "layouts": [
                {
                    "layout_index": 0,
                    "layout_name": "Default",
                    "slots": [{"slot_id": 1, "role_hint": "title", "geometry": {"area_ratio": 0.1}}]
                }
            ]
        }
    }
    
    result = beautifier_node(state)
    # Should fallback to layout_index 0
    assert result["manifest"][0]["layout_index"] == 0


def test_beautifier_node_max_chars_warning(capsys):
    """Content exceeding max_chars should warn"""
    long_text = "x" * 150
    state = {
        "manifest": [
            {
                "layout_index": 0,
                "content": {"1": long_text}
            }
        ],
        "registry": {
            "layouts": [
                {
                    "layout_index": 0,
                    "slots": [
                        {
                            "slot_id": 1,
                            "role_hint": "title",
                            "geometry": {"area_ratio": 0.1},
                            "max_chars": 50  # Content is 150 chars
                        }
                    ]
                }
            ]
        }
    }
    
    beautifier_node(state)
    captured = capsys.readouterr()
    assert "⚠️" in captured.out
    assert "exceeds max_chars" in captured.out


def test_beautifier_node_none_text_handling():
    """None text should convert to empty string, not 'None'"""
    state = {
        "manifest": [
            {
                "layout_index": 0,
                "content": {"1": None}
            }
        ],
        "registry": {
            "layouts": [
                {
                    "layout_index": 0,
                    "slots": [{"slot_id": 1, "role_hint": "title", "geometry": {"area_ratio": 0.1}}]
                }
            ]
        }
    }
    
    result = beautifier_node(state)
    runs = result["manifest"][0]["content"]["1"]["runs"]
    assert runs[0]["text"] == ""


def test_beautifier_node_string_and_int_slot_ids():
    """Should handle both string and int slot_ids"""
    state = {
        "manifest": [
            {
                "layout_index": 0,
                "content": {"1": "Text 1", "2": "Text 2"}  # String keys
            }
        ],
        "registry": {
            "layouts": [
                {
                    "layout_index": 0,
                    "slots": [
                        {"slot_id": 1, "role_hint": "title", "geometry": {"area_ratio": 0.1}},  # Int in registry
                        {"slot_id": 2, "role_hint": "body", "geometry": {"area_ratio": 0.3}}
                    ]
                }
            ]
        }
    }
    
    result = beautifier_node(state)
    content = result["manifest"][0]["content"]
    
    # Both slots should be processed
    assert "1" in content
    assert "2" in content
    assert content["1"]["alignment"] == "CENTER"  # Title
    assert content["2"]["alignment"] == "LEFT"    # Body


def test_beautifier_node_missing_registry():
    """Missing registry should raise ValueError"""
    state = {"manifest": []}
    
    with pytest.raises(ValueError, match="State must contain"):
        beautifier_node(state)


def test_beautifier_node_empty_layouts():
    """Empty layouts should raise ValueError"""
    state = {
        "manifest": [],
        "registry": {"layouts": []}
    }
    
    with pytest.raises(ValueError, match="Registry contains no layouts"):
        beautifier_node(state)


def test_beautifier_node_invalid_content_dict(capsys):
    """Invalid content (not dict) should warn and coerce"""
    state = {
        "manifest": [
            {
                "layout_index": 0,
                "content": "not a dict"  # Invalid
            }
        ],
        "registry": {
            "layouts": [
                {
                    "layout_index": 0,
                    "slots": []
                }
            ]
        }
    }
    
    result = beautifier_node(state)
    captured = capsys.readouterr()
    
    assert "⚠️" in captured.out
    assert "content is not a dict" in captured.out
    assert result["manifest"][0]["content"] == {}


def test_beautifier_node_multiple_slides():
    """Should process multiple slides correctly"""
    state = {
        "manifest": [
            {"layout_index": 0, "content": {"1": "Slide 1"}},
            {"layout_index": 1, "content": {"1": "Slide 2"}},
            {"layout_index": 0, "content": {"1": "Slide 3"}},
        ],
        "registry": {
            "layouts": [
                {
                    "layout_index": 0,
                    "slots": [{"slot_id": 1, "role_hint": "title", "geometry": {"area_ratio": 0.1}}]
                },
                {
                    "layout_index": 1,
                    "slots": [{"slot_id": 1, "role_hint": "body", "geometry": {"area_ratio": 0.3}}]
                }
            ]
        }
    }
    
    result = beautifier_node(state)
    assert len(result["manifest"]) == 3
    assert result["manifest"][0]["layout_index"] == 0
    assert result["manifest"][1]["layout_index"] == 1
    assert result["manifest"][2]["layout_index"] == 0
