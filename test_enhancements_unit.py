"""
Unit Tests for Enhanced Pipeline 2 Components  
Tests individual functions without requiring LLM initialization

Run: python test_enhancements_unit.py
"""
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.dirname(__file__))


def test_markdown_spacing():
    """Test that markdown parsing preserves spaces around emphasis."""
    print("\n=== TEST 1: Markdown Spacing ===")
    
    # Import directly from file to avoid __init__.py chain
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "beautifier",
        os.path.join(os.path.dirname(__file__), "src", "nodes", "pipeline_2_generation", "beautifier.py")
    )
    beautifier = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(beautifier)
    parse_markdown = beautifier.parse_markdown
    
    test_cases = [
        # (input, expected_output_without_markers, should_have_bold, should_have_italic)
        ("This is **bold text** in sentence", "This is bold text in sentence", True, False),
        ("Text with *italic* words here", "Text with italic words here", False, True),
        ("Multiple **bold** and *italic* runs", "Multiple bold and italic runs", True, True),
        ("No emphasis here", "No emphasis here", False, False),
        ("Spaces **preserved** correctly", "Spaces preserved correctly", True, False),
        ("End with **bold**", "End with bold", True, False),
    ]
    
    for text, expected_clean, should_bold, should_italic in test_cases:
        runs = parse_markdown(text)
        
        # Reconstruct text
        reconstructed = "".join(r["text"] for r in runs)
        
        assert reconstructed == expected_clean, f"Text mismatch: '{reconstructed}' != '{expected_clean}'"
        
        # Check emphasis applied correctly
        has_bold = any(r.get("bold") for r in runs)
        has_italic = any(r.get("italic") for r in runs)
        
        assert has_bold == should_bold, f"Bold mismatch for '{text}': expected {should_bold}, got {has_bold}"
        assert has_italic == should_italic, f"Italic mismatch for '{text}': expected {should_italic}, got {has_italic}"
    
    print("✅ PASS: Markdown spacing preserved correctly")
    print("   Tested 6 scenarios with bold/italic combinations")


def test_header_text_filtering():
    """Test that header text patterns are detected correctly."""
    print("\n=== TEST 2: Header Text Filtering ===")
    
    from src.nodes.pipeline_2_generation.injector import _is_template_header
    
    test_cases = [
        # Headers that should be filtered
        ("Presentation title Page 1", True),
        ("Presentation title Page 10", True),
        ("16 February 2026", True),
        ("Page 5 16 February 2026", True),
        ("  Presentation title Page 3  ", True),  # With whitespace
        
        # Normal content that should NOT be filtered
        ("Normal slide content", False),
        ("My Presentation Title", False),
        ("Introduction to AI", False),
        ("", False),
        ("   ", False),
    ]
    
    for text, expected in test_cases:
        result = _is_template_header(text)
        assert result == expected, f"Header detection failed for '{text}': expected {expected}, got {result}"
    
    print("✅ PASS: Header text filtering works correctly")
    print("   Tested 10 patterns (5 headers, 5 normal)")


def test_role_aware_font_sizing():
    """Test that font sizes are role-aware."""
    print("\n=== TEST 3: Role-Aware Font Sizing ===")
    
    from src.nodes.pipeline_2_generation.beautifier import (
        _determine_font_size,
        FONT_SIZE_TITLE_SLIDE_MAIN,
        FONT_SIZE_TITLE_SLIDE_SUBTITLE,
        FONT_SIZE_TITLE_LARGE,
        FONT_SIZE_CONTENT_DEFAULT
    )
    
    # Test TITLE slide gets larger fonts
    title_main = _determine_font_size("title", 0.1, "TITLE")
    title_subtitle = _determine_font_size("subtitle", 0.1, "TITLE")
    
    # Test CONTENT slide gets standard fonts
    content_title = _determine_font_size("title", 0.1, "CONTENT")
    content_body = _determine_font_size("content", 0.1, "CONTENT")
    
    # Assertions
    assert title_main == FONT_SIZE_TITLE_SLIDE_MAIN, f"Title slide main should be {FONT_SIZE_TITLE_SLIDE_MAIN}pt"
    assert title_subtitle == FONT_SIZE_TITLE_SLIDE_SUBTITLE, f"Title slide subtitle should be {FONT_SIZE_TITLE_SLIDE_SUBTITLE}pt"
    assert content_title == FONT_SIZE_TITLE_LARGE, f"Content slide title should be {FONT_SIZE_TITLE_LARGE}pt"
    assert content_body == FONT_SIZE_CONTENT_DEFAULT, f"Content slide body should be {FONT_SIZE_CONTENT_DEFAULT}pt"
    
    # Title slide should be more impactful
    assert title_main > content_title, "Title slide fonts should be larger than content slides"
    
    print("✅ PASS: Role-aware font sizing works correctly")
    print(f"   TITLE slide: main={title_main}pt, subtitle={title_subtitle}pt")
    print(f"   CONTENT slide: title={content_title}pt, body={content_body}pt")


def test_registry_schema_backward_compat():
    """Test that registry schema is backward compatible."""
    print("\n=== TEST 4: Registry Schema Backward Compatibility ===")
    
    from src.nodes.pipeline_1_indexing.layout_validator import LayoutMetadata
    
    # Old registry format (without new fields)
    old_layout = {
        "layout_index": 0,
        "layout_name": "Title",
        "layout_purpose": "TITLE_SLIDE",
        "description": "Main title slide",
        "slots": []
    }
    
    # Should work with defaults
    layout = LayoutMetadata(**old_layout)
    
    assert layout.layout_role is None, "layout_role should default to None"
    assert layout.supports_background_image == False, "supports_background_image should default to False"
    assert layout.density == "medium", "density should default to 'medium'"
    
    # New format should also work
    new_layout = {
        **old_layout,
        "layout_role": "TITLE",
        "supports_background_image": True,
        "density": "low"
    }
    
    layout2 = LayoutMetadata(**new_layout)
    assert layout2.layout_role == "TITLE"
    assert layout2.supports_background_image == True
    assert layout2.density == "low"
    
    print("✅ PASS: Backward compatibility maintained")
    print("   Old format: uses defaults (None, False, 'medium')")
    print("   New format: preserves custom values")


def test_image_director_helpers():
    """Test image director helper functions without LLM."""
    print("\n=== TEST 5: Image Director Helpers ===")
    
    from src.nodes.pipeline_2_generation.image_director import (
        _should_have_background,
        _generate_image_keywords,
        _get_image_mood,
        _get_composition,
        _get_overlay_opacity,
        ROLE_TITLE,
        ROLE_CONTENT,
        ROLE_CLOSING
    )
    
    # Test background enabling logic
    assert _should_have_background(ROLE_TITLE, True) == True, "TITLE with support should have background"
    assert _should_have_background(ROLE_TITLE, False) == False, "TITLE without support should not have background"
    assert _should_have_background(ROLE_CONTENT, True) == False, "CONTENT should not have background"
    assert _should_have_background(ROLE_CLOSING, True) == True, "CLOSING with support should have background"
    
    # Test keyword generation
    keywords = _generate_image_keywords(ROLE_TITLE, "Introduction to AI systems")
    assert len(keywords) > 0, "Should generate keywords"
    assert "professional" in keywords.lower() or "business" in keywords.lower(), "Should include base keywords"
    
    # Test mood
    mood = _get_image_mood(ROLE_TITLE)
    assert len(mood) > 0, "Should generate mood"
    
    # Test composition
    comp = _get_composition(ROLE_TITLE)
    assert len(comp) > 0, "Should generate composition"
    
    # Test opacity
    title_opacity = _get_overlay_opacity(ROLE_TITLE)
    content_opacity = _get_overlay_opacity(ROLE_CONTENT)
    assert 0.0 <= title_opacity <= 1.0, "Opacity should be in valid range"
    assert 0.0 <= content_opacity <= 1.0, "Opacity should be in valid range"
    assert title_opacity < content_opacity, "TITLE should have lower opacity (more image visible)"
    
    print("✅ PASS: Image director helpers work correctly")
    print(f"   TITLE opacity: {title_opacity:.0%}")
    print(f"   CONTENT opacity: {content_opacity:.0%}")


def test_ellipse_axes_fix():
    """Test that ellipse_axes accepts List[float] correctly."""
    print("\n=== TEST 6: Ellipse Axes Schema Fix ===")
    
    from src.nodes.pipeline_1_indexing.layout_validator import GeometryMetadata
    from pydantic import ValidationError
    
    # Should accept List[float] with exactly 2 elements
    valid_geom = GeometryMetadata(
        area_ratio=0.5,
        norm_top=0.2,
        norm_left=0.1,
        norm_width=0.8,
        norm_height=0.6,
        ellipse_axes=[0.4, 0.3]  # List of 2 floats
    )
    
    assert valid_geom.ellipse_axes == [0.4, 0.3], "Should accept 2-element list"
    
    # Should reject list with wrong number of elements
    try:
        invalid_geom = GeometryMetadata(
            area_ratio=0.5,
            norm_top=0.2,
            norm_left=0.1,
            norm_width=0.8,
            norm_height=0.6,
            ellipse_axes=[0.4]  # Only 1 element
        )
        assert False, "Should have raised ValidationError for 1-element list"
    except ValidationError:
        pass  # Expected
    
    # Should accept None
    none_geom = GeometryMetadata(
        area_ratio=0.5,
        norm_top=0.2,
        norm_left=0.1,
        norm_width=0.8,
        norm_height=0.6,
        ellipse_axes=None
    )
    
    assert none_geom.ellipse_axes is None, "Should accept None"
    
    print("✅ PASS: Ellipse axes schema fix works correctly")
    print("   Accepts: List[float] with 2 elements or None")
    print("   Rejects: Lists with != 2 elements")


def run_all_tests():
    """Run all unit tests."""
    print("\n" + "="*60)
    print("ENHANCED PIPELINE 2 UNIT TESTS")
    print("="*60)
    
    try:
        test_markdown_spacing()
        test_header_text_filtering()
        test_role_aware_font_sizing()
        test_registry_schema_backward_compat()
        test_image_director_helpers()
        test_ellipse_axes_fix()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED (6/6)")
        print("="*60)
        return True
        
    except AssertionError as e:
        print("\n" + "="*60)
        print(f"❌ TEST FAILED: {e}")
        print("="*60)
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print("\n" + "="*60)
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        print("="*60)
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
