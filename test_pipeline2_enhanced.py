"""
Smoke Test for Enhanced Pipeline 2 with Slide Roles
Tests the full pipeline with role enforcement, text density, and background images

Run: python test_pipeline2_enhanced.py
"""
import sys
import os

# Ensure src is in path
sys.path.insert(0, os.path.dirname(__file__))

def test_slide_roles():
    """Test that architect enforces slide roles correctly."""
    print("\n=== TEST 1: Slide Roles Enforcement ===")
    
    from src.nodes.pipeline_2_generation.architect import (
        architect_slides_node, ROLE_TITLE, ROLE_AGENDA
    )
    
    # Mock state
    state = {
        "content_map": "Test content about AI innovation",
        "registry": {
            "layouts": [
                {
                    "layout_index": 0,
                    "layout_name": "Title Slide",
                    "layout_purpose": "TITLE_SLIDE",
                    "layout_role": "TITLE",
                    "slots": [],
                    "supports_background_image": True,
                    "density": "low"
                },
                {
                    "layout_index": 1,
                    "layout_name": "Content",
                    "layout_purpose": "CONTENT_SLIDE",
                    "layout_role": "CONTENT",
                    "slots": [],
                    "supports_background_image": False,
                    "density": "medium"
                }
            ]
        }
    }
    
    result = architect_slides_node(state)
    slide_plans = result["slide_plans"]
    
    # Verify first slide is TITLE
    assert len(slide_plans) > 0, "Should generate at least one slide"
    assert slide_plans[0]["slide_role"] == ROLE_TITLE, f"First slide should be TITLE, got {slide_plans[0]['slide_role']}"
    
    # Verify second slide is AGENDA
    if len(slide_plans) > 1:
        assert slide_plans[1]["slide_role"] == ROLE_AGENDA, f"Second slide should be AGENDA, got {slide_plans[1]['slide_role']}"
    
    print(f"✅ PASS: Slide roles enforced correctly")
    print(f"   Slide 1: {slide_plans[0]['slide_role']}")
    if len(slide_plans) > 1:
        print(f"   Slide 2: {slide_plans[1]['slide_role']}")
    print(f"   Total slides: {len(slide_plans)}")


def test_markdown_spacing():
    """Test that markdown parsing preserves spaces around emphasis."""
    print("\n=== TEST 2: Markdown Spacing ===")
    
    from src.nodes.pipeline_2_generation.beautifier import parse_markdown
    
    test_cases = [
        ("This is **bold text** in sentence", True),
        ("Text with *italic* words here", True),
        ("Multiple **bold** and *italic* runs", True),
        ("No emphasis here", False),
    ]
    
    for text, has_emphasis in test_cases:
        runs = parse_markdown(text)
        
        # Reconstruct text
        reconstructed = "".join(r["text"] for r in runs)
        
        # Remove emphasis markers from original
        clean_text = text.replace("**", "").replace("*", "")
        
        assert reconstructed == clean_text, f"Spacing mismatch: '{reconstructed}' != '{clean_text}'"
        
        # Check emphasis applied correctly
        if has_emphasis:
            has_bold = any(r.get("bold") for r in runs)
            has_italic = any(r.get("italic") for r in runs)
            if "**" in text:
                assert has_bold, f"Should have bold in: {text}"
            if text.count("*") % 2 == 0 and "*" in text and "**" not in text:
                assert has_italic, f"Should have italic in: {text}"
    
    print("✅ PASS: Markdown spacing preserved correctly")


def test_background_image_spec():
    """Test that image director creates proper specs."""
    print("\n=== TEST 3: Background Image Specification ===")
    
    from src.nodes.pipeline_2_generation.image_director import (
        image_director_node, ROLE_TITLE, ROLE_CONTENT
    )
    
    # Mock state
    state = {
        "manifest": [
            {
                "layout_index": 0,
                "slide_role": ROLE_TITLE,
                "content": {},
                "background_image": {"enabled": False, "keywords": "", "mood": "", "composition": "", "overlay_opacity": 0.0}
            },
            {
                "layout_index": 1,
                "slide_role": ROLE_CONTENT,
                "content": {},
                "background_image": {"enabled": False, "keywords": "", "mood": "", "composition": "", "overlay_opacity": 0.0}
            }
        ],
        "slide_plans": [
            {"layout_index": 0, "slide_intent": "Introduction to AI", "slide_role": ROLE_TITLE},
            {"layout_index": 1, "slide_intent": "Technical details", "slide_role": ROLE_CONTENT}
        ],
        "registry": {
            "layouts": [
                {"layout_index": 0, "supports_background_image": True},
                {"layout_index": 1, "supports_background_image": False}
            ]
        }
    }
    
    result = image_director_node(state)
    manifest = result["manifest"]
    
    # Verify TITLE slide has background enabled
    assert manifest[0]["background_image"]["enabled"] == True, "TITLE slide should have background enabled"
    assert len(manifest[0]["background_image"]["keywords"]) > 0, "TITLE slide should have keywords"
    
    # Verify CONTENT slide does NOT have background (layout doesn't support it)
    assert manifest[1]["background_image"]["enabled"] == False, "CONTENT slide should not have background (no layout support)"
    
    print("✅ PASS: Background image specs generated correctly")
    print(f"   TITLE slide keywords: {manifest[0]['background_image']['keywords'][:50]}...")
    print(f"   TITLE slide overlay: {manifest[0]['background_image']['overlay_opacity']:.0%}")


def test_header_text_filtering():
    """Test that header text patterns are detected correctly."""
    print("\n=== TEST 4: Header Text Filtering ===")
    
    from src.nodes.pipeline_2_generation.injector import _is_template_header
    
    test_cases = [
        ("Presentation title Page 1", True),
        ("Presentation title Page 10", True),
        ("16 February 2026", True),
        ("Page 5 16 February 2026", True),
        ("Normal slide content", False),
        ("My Presentation Title", False),
        ("", False),
    ]
    
    for text, expected in test_cases:
        result = _is_template_header(text)
        assert result == expected, f"Header detection failed for '{text}': expected {expected}, got {result}"
    
    print("✅ PASS: Header text filtering works correctly")


def test_role_aware_font_sizing():
    """Test that font sizes are role-aware."""
    print("\n=== TEST 5: Role-Aware Font Sizing ===")
    
    from src.nodes.pipeline_2_generation.beautifier import (
        _determine_font_size, ROLE_TITLE, ROLE_CONTENT,
        FONT_SIZE_TITLE_SLIDE_MAIN, FONT_SIZE_TITLE_LARGE
    )
    
    # Title slide should get larger fonts
    title_slide_size = _determine_font_size("title", 0.1, ROLE_TITLE)
    content_slide_size = _determine_font_size("title", 0.1, ROLE_CONTENT)
    
    assert title_slide_size == FONT_SIZE_TITLE_SLIDE_MAIN, f"Title slide main should be {FONT_SIZE_TITLE_SLIDE_MAIN}pt, got {title_slide_size}pt"
    assert content_slide_size == FONT_SIZE_TITLE_LARGE, f"Content slide title should be {FONT_SIZE_TITLE_LARGE}pt, got {content_slide_size}pt"
    assert title_slide_size > content_slide_size, "Title slide fonts should be larger"
    
    print("✅ PASS: Role-aware font sizing works correctly")
    print(f"   TITLE slide main font: {title_slide_size}pt")
    print(f"   CONTENT slide title font: {content_slide_size}pt")


def test_registry_schema_backward_compat():
    """Test that registry schema is backward compatible."""
    print("\n=== TEST 6: Registry Schema Backward Compatibility ===")
    
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
    try:
        layout = LayoutMetadata(**old_layout)
        assert layout.layout_role is None, "layout_role should default to None"
        assert layout.supports_background_image == False, "supports_background_image should default to False"
        assert layout.density == "medium", "density should default to medium"
        print("✅ PASS: Backward compatibility maintained")
    except Exception as e:
        print(f"❌ FAIL: {e}")
        raise


def run_all_tests():
    """Run all smoke tests."""
    print("\n" + "="*60)
    print("ENHANCED PIPELINE 2 SMOKE TESTS")
    print("="*60)
    
    try:
        test_slide_roles()
        test_markdown_spacing()
        test_background_image_spec()
        test_header_text_filtering()
        test_role_aware_font_sizing()
        test_registry_schema_backward_compat()
        
        print("\n" + "="*60)
        print("✅ ALL TESTS PASSED")
        print("="*60)
        return True
        
    except AssertionError as e:
        print("\n" + "="*60)
        print(f"❌ TEST FAILED: {e}")
        print("="*60)
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
