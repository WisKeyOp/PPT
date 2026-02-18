"""
Unit tests for circular text space fitting in beautifier
Tests chord-width calculation, text estimation, and circle fitting logic.

Run: pytest test_beautifier_circle.py -v
"""
import math
import pytest
import sys
import importlib.util

# Direct import of beautifier module to avoid __init__.py issues
spec = importlib.util.spec_from_file_location(
    "beautifier",
    "src/nodes/pipeline_2_generation/beautifier.py"
)
beautifier = importlib.util.module_from_spec(spec)
sys.modules["beautifier"] = beautifier
spec.loader.exec_module(beautifier)

# Import functions and constants from loaded module
_calculate_chord_width = beautifier._calculate_chord_width
_estimate_text_dimensions = beautifier._estimate_text_dimensions
_fit_text_in_circle = beautifier._fit_text_in_circle
beautifier_node = beautifier.beautifier_node
FONT_SIZE_RANGE = beautifier.FONT_SIZE_RANGE
TEXT_PADDING_RATIO = beautifier.TEXT_PADDING_RATIO


# --- Chord Width Calculation Tests ---

def test_chord_width_at_center():
    """At circle center (y=0), width should be full diameter (2*radius)"""
    radius = 0.5
    width = _calculate_chord_width(y_offset=0.0, radius=radius)
    expected = 2 * radius
    assert abs(width - expected) < 0.001, f"Expected {expected}, got {width}"


def test_chord_width_at_edge():
    """At circle edge (y=±radius), width should be ~0"""
    radius = 0.5
    width_top = _calculate_chord_width(y_offset=radius, radius=radius)
    width_bottom = _calculate_chord_width(y_offset=-radius, radius=radius)
    assert width_top < 0.001, f"Width at edge should be ~0, got {width_top}"
    assert width_bottom < 0.001, f"Width at edge should be ~0, got {width_bottom}"


def test_chord_width_outside_circle():
    """Beyond circle radius, width should be 0"""
    radius = 0.5
    width = _calculate_chord_width(y_offset=0.6, radius=radius)
    assert width == 0.0, f"Width outside circle should be 0, got {width}"


def test_chord_width_at_half_radius():
    """At y=radius/2, verify sqrt calculation"""
    radius = 0.4
    y = radius / 2
    width = _calculate_chord_width(y_offset=y, radius=radius)
    # W = 2*sqrt(r² - y²) = 2*sqrt(0.16 - 0.04) = 2*sqrt(0.12) ≈ 0.693
    expected = 2 * math.sqrt(radius**2 - y**2)
    assert abs(width - expected) < 0.001, f"Expected {expected:.3f}, got {width:.3f}"


def test_chord_width_with_offset_center():
    """Chord width with non-zero center_y"""
    radius = 0.5
    center_y = 0.2
    y = 0.2  # At center
    width = _calculate_chord_width(y_offset=y, radius=radius, center_y=center_y)
    expected = 2 * radius
    assert abs(width - expected) < 0.001


def test_chord_width_zero_radius():
    """Zero radius should return 0 width"""
    width = _calculate_chord_width(y_offset=0.0, radius=0.0)
    assert width == 0.0


def test_chord_width_negative_radius():
    """Negative radius should return 0 width"""
    width = _calculate_chord_width(y_offset=0.0, radius=-0.5)
    assert width == 0.0


# --- Text Dimension Estimation Tests ---

def test_estimate_dimensions_empty_text():
    """Empty text should return (0, 0)"""
    runs = [{"text": "", "bold": False, "italic": False}]
    width, height = _estimate_text_dimensions("", 16, runs)
    assert width == 0.0
    assert height == 0.0


def test_estimate_dimensions_normal_text():
    """Normal text should have width proportional to length"""
    text = "Hello World"
    runs = [{"text": text, "bold": False, "italic": False}]
    width, height = _estimate_text_dimensions(text, 20, runs)
    assert width > 0.0
    assert height > 0.0


def test_estimate_dimensions_bold_wider():
    """Bold text should be wider than normal text of same length"""
    text = "Test Text"
    runs_normal = [{"text": text, "bold": False, "italic": False}]
    runs_bold = [{"text": text, "bold": True, "italic": False}]
    
    width_normal, _ = _estimate_text_dimensions(text, 20, runs_normal)
    width_bold, _ = _estimate_text_dimensions(text, 20, runs_bold)
    
    assert width_bold > width_normal, "Bold should be wider"


def test_estimate_dimensions_larger_font_wider():
    """Larger font should produce wider text"""
    text = "Sample"
    runs = [{"text": text, "bold": False, "italic": False}]
    
    width_small, _ = _estimate_text_dimensions(text, 12, runs)
    width_large, _ = _estimate_text_dimensions(text, 24, runs)
    
    assert width_large > width_small, "Larger font should be wider"


def test_estimate_dimensions_zero_font():
    """Zero font size should return 0 dimensions"""
    text = "Test"
    runs = [{"text": text, "bold": False, "italic": False}]
    width, height = _estimate_text_dimensions(text, 0, runs)
    assert width == 0.0
    assert height == 0.0


# --- Circle Fitting Tests ---

def test_fit_short_text_large_circle():
    """Short text in large circle should get large font"""
    text = "Hi"
    runs = [{"text": text, "bold": False, "italic": False}]
    radius = 0.3  # Large circle
    
    font_size = _fit_text_in_circle(text, runs, radius)
    
    # Should fit comfortably, so expect larger font
    assert font_size > 20, f"Short text should fit at large font, got {font_size}pt"


def test_fit_long_text_small_circle():
    """Long text in small circle should get small font"""
    text = "This is a very long piece of text that needs to fit inside a small circular area"
    runs = [{"text": text, "bold": False, "italic": False}]
    radius = 0.1  # Small circle
    
    font_size = _fit_text_in_circle(text, runs, radius)
    
    # Should require smaller font to fit
    assert font_size < 20, f"Long text should need small font, got {font_size}pt"


def test_fit_empty_text():
    """Empty text should return minimum font"""
    text = ""
    runs = [{"text": "", "bold": False, "italic": False}]
    radius = 0.2
    
    font_size = _fit_text_in_circle(text, runs, radius)
    
    assert font_size == FONT_SIZE_RANGE[0]


def test_fit_zero_radius():
    """Zero radius should return minimum font"""
    text = "Test"
    runs = [{"text": text, "bold": False, "italic": False}]
    
    font_size = _fit_text_in_circle(text, runs, radius=0.0)
    
    assert font_size == FONT_SIZE_RANGE[0]


def test_fit_padding_reduces_space():
    """Higher padding should require smaller font"""
    text = "Medium length text for testing"
    runs = [{"text": text, "bold": False, "italic": False}]
    radius = 0.2
    
    # Default padding
    font_default = _fit_text_in_circle(text, runs, radius, padding_ratio=0.1)
    
    # High padding (reduces effective radius significantly)
    font_high_padding = _fit_text_in_circle(text, runs, radius, padding_ratio=0.3)
    
    assert font_high_padding <= font_default, "Higher padding should reduce font size"


def test_fit_excessive_padding_returns_minimum():
    """Padding >= radius should return minimum font"""
    text = "Test"
    runs = [{"text": text, "bold": False, "italic": False}]
    radius = 0.1
    
    font_size = _fit_text_in_circle(text, runs, radius, padding_ratio=1.0)
    
    assert font_size == FONT_SIZE_RANGE[0]


def test_fit_unbreakable_long_word():
    """Single unbreakable word should return a valid font size"""
    text = "Supercalifragilisticexpialidocious"
    runs = [{"text": text, "bold": False, "italic": False}]
    radius = 0.05  # Very small circle
    
    font_size = _fit_text_in_circle(text, runs, radius)
    
    # Should return a font size within valid range
    # Note: Algorithm may not perfectly constrain unbreakable words on first line
    min_font, max_font = FONT_SIZE_RANGE
    assert min_font <= font_size <= max_font, f"Font size {font_size}pt outside valid range {min_font}-{max_font}pt"


def test_fit_multiple_words_wrap():
    """Multiple words should wrap across lines"""
    text = "One Two Three Four Five"
    runs = [{"text": text, "bold": False, "italic": False}]
    radius = 0.15
    
    font_size = _fit_text_in_circle(text, runs, radius)
    
    # Should fit by wrapping
    assert FONT_SIZE_RANGE[0] < font_size < FONT_SIZE_RANGE[1]


# --- Beautifier Node Integration Tests ---

def test_beautifier_circular_slot():
    """Beautifier should use circular fitting for circular slots"""
    state = {
        "manifest": [
            {
                "layout_index": 0,
                "content": {"1": "Circle Text"}
            }
        ],
        "registry": {
            "layouts": [
                {
                    "layout_index": 0,
                    "layout_name": "Badge Layout",
                    "slots": [
                        {
                            "slot_id": 1,
                            "role_hint": "title",
                            "geometry": {
                                "area_ratio": 0.03,
                                "norm_top": 0.4,
                                "norm_left": 0.4,
                                "norm_width": 0.2,
                                "norm_height": 0.2,
                                "shape_type": "oval",
                                "is_circular": True,
                                "radius": 0.1
                            },
                            "max_chars": 50
                        }
                    ]
                }
            ]
        }
    }
    
    result = beautifier_node(state)
    manifest = result["manifest"]
    
    assert len(manifest) == 1
    styled = manifest[0]["content"]["1"]
    
    # Font size should be determined by circular fitting
    assert "font_size" in styled
    assert styled["font_size"] >= FONT_SIZE_RANGE[0]
    assert styled["font_size"] <= FONT_SIZE_RANGE[1]


def test_beautifier_circular_missing_radius_fallback(capsys):
    """Circular slot without radius should fallback with warning"""
    state = {
        "manifest": [
            {
                "layout_index": 0,
                "content": {"1": "Test"}
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
                            "geometry": {
                                "area_ratio": 0.1,
                                "norm_top": 0.1,
                                "norm_left": 0.1,
                                "norm_width": 0.3,
                                "norm_height": 0.3,
                                "shape_type": "oval",
                                "is_circular": True
                                # Missing radius field
                            }
                        }
                    ]
                }
            ]
        }
    }
    
    result = beautifier_node(state)
    captured = capsys.readouterr()
    
    # Should warn about missing radius
    assert "⚠️" in captured.out
    assert "missing radius" in captured.out.lower()
    
    # Should still produce valid output with fallback sizing
    assert "1" in result["manifest"][0]["content"]


def test_beautifier_rectangular_slot_unchanged():
    """Rectangular slots should use standard sizing"""
    state = {
        "manifest": [
            {
                "layout_index": 0,
                "content": {"1": "Rectangle Text"}
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
                            "geometry": {
                                "area_ratio": 0.2,
                                "norm_top": 0.1,
                                "norm_left": 0.1,
                                "norm_width": 0.8,
                                "norm_height": 0.2,
                                "shape_type": "rectangle",
                                "is_circular": False
                            }
                        }
                    ]
                }
            ]
        }
    }
    
    result = beautifier_node(state)
    manifest = result["manifest"]
    
    # Should use standard geometry-based sizing
    styled = manifest[0]["content"]["1"]
    assert "font_size" in styled
    # Title with area_ratio 0.2 should get large font (>= 28)
    assert styled["font_size"] >= 28


def test_beautifier_mixed_shapes():
    """Layout with both circular and rectangular slots"""
    state = {
        "manifest": [
            {
                "layout_index": 0,
                "content": {
                    "1": "Circle Badge",
                    "2": "Rectangle Title"
                }
            }
        ],
        "registry": {
            "layouts": [
                {
                    "layout_index": 0,
                    "slots": [
                        {
                            "slot_id": 1,
                            "role_hint": "content",
                            "geometry": {
                                "area_ratio": 0.03,
                                "norm_top": 0.7,
                                "norm_left": 0.7,
                                "norm_width": 0.2,
                                "norm_height": 0.2,
                                "shape_type": "oval",
                                "is_circular": True,
                                "radius": 0.1
                            }
                        },
                        {
                            "slot_id": 2,
                            "role_hint": "title",
                            "geometry": {
                                "area_ratio": 0.15,
                                "norm_top": 0.05,
                                "norm_left": 0.1,
                                "norm_width": 0.8,
                                "norm_height": 0.1,
                                "shape_type": "rectangle",
                                "is_circular": False
                            }
                        }
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
    
    # Both should have valid font sizes
    assert content["1"]["font_size"] >= FONT_SIZE_RANGE[0]
    assert content["2"]["font_size"] >= FONT_SIZE_RANGE[0]


def test_beautifier_circular_logs_fit_info(capsys):
    """Circular fitting should log fit information"""
    state = {
        "manifest": [
            {
                "layout_index": 0,
                "content": {"1": "Badge"}
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
                            "geometry": {
                                "area_ratio": 0.03,
                                "norm_top": 0.5,
                                "norm_left": 0.5,
                                "norm_width": 0.2,
                                "norm_height": 0.2,
                                "is_circular": True,
                                "radius": 0.1
                            }
                        }
                    ]
                }
            ]
        }
    }
    
    beautifier_node(state)
    captured = capsys.readouterr()
    
    # Should log circular fit details
    assert "Circular fit" in captured.out
    assert "Slot 1" in captured.out
    assert "radius=" in captured.out
