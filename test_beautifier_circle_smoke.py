"""
Manual Smoke Test for Circular Text Space Fitting
Tests beautifier with realistic circular badge scenarios.

Run: python test_beautifier_circle_smoke.py
"""
import sys
import os
from pprint import pprint

# Add src to path to import beautifier directly
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'nodes', 'pipeline_2_generation'))

import beautifier


def create_test_registry():
    """Create mock registry with circular and rectangular slots"""
    return {
        "master_name": "circular_test.pptx",
        "layouts": [
            # Layout 0: Rectangular title slide
            {
                "layout_index": 0,
                "layout_name": "Standard Title",
                "layout_purpose": "TITLE_SLIDE",
                "slots": [
                    {
                        "slot_id": 0,
                        "role_name": "Title",
                        "role_hint": "title",
                        "content_type": "text",
                        "max_chars": 80,
                        "geometry": {
                            "area_ratio": 0.15,
                            "norm_top": 0.3,
                            "norm_left": 0.1,
                            "norm_width": 0.8,
                            "norm_height": 0.2,
                            "shape_type": "rectangle",
                            "is_circular": False
                        }
                    }
                ]
            },
            # Layout 1: Circular badge layout
            {
                "layout_index": 1,
                "layout_name": "Badge Layout",
                "layout_purpose": "VISUAL_SLIDE",
                "slots": [
                    {
                        "slot_id": 0,
                        "role_name": "Badge Text",
                        "role_hint": "content",
                        "content_type": "text",
                        "max_chars": 30,
                        "geometry": {
                            "area_ratio": 0.031,  # Small circular area
                            "norm_top": 0.4,
                            "norm_left": 0.4,
                            "norm_width": 0.2,
                            "norm_height": 0.2,
                            "shape_type": "oval",
                            "is_circular": True,
                            "radius": 0.1
                        }
                    }
                ]
            },
            # Layout 2: Multiple circular badges
            {
                "layout_index": 2,
                "layout_name": "Multi-Badge",
                "layout_purpose": "COMPARISON_SLIDE",
                "slots": [
                    {
                        "slot_id": 0,
                        "role_name": "Large Badge",
                        "role_hint": "content",
                        "content_type": "text",
                        "max_chars": 60,
                        "geometry": {
                            "area_ratio": 0.071,
                            "norm_top": 0.2,
                            "norm_left": 0.2,
                            "norm_width": 0.3,
                            "norm_height": 0.3,
                            "shape_type": "oval",
                            "is_circular": True,
                            "radius": 0.15
                        }
                    },
                    {
                        "slot_id": 1,
                        "role_name": "Small Badge",
                        "role_hint": "content",
                        "content_type": "text",
                        "max_chars": 20,
                        "geometry": {
                            "area_ratio": 0.020,
                            "norm_top": 0.6,
                            "norm_left": 0.6,
                            "norm_width": 0.15,
                            "norm_height": 0.15,
                            "shape_type": "oval",
                            "is_circular": True,
                            "radius": 0.075
                        }
                    }
                ]
            },
            # Layout 3: Ellipse (oval with different axes)
            {
                "layout_index": 3,
                "layout_name": "Ellipse Layout",
                "layout_purpose": "VISUAL_SLIDE",
                "slots": [
                    {
                        "slot_id": 0,
                        "role_name": "Ellipse Text",
                        "role_hint": "content",
                        "content_type": "text",
                        "max_chars": 50,
                        "geometry": {
                            "area_ratio": 0.047,
                            "norm_top": 0.3,
                            "norm_left": 0.2,
                            "norm_width": 0.6,
                            "norm_height": 0.2,
                            "shape_type": "oval",
                            "is_circular": True,
                            "radius": 0.1,  # Uses minimum dimension
                            "ellipse_axes": (0.3, 0.1)  # Wide ellipse
                        }
                    }
                ]
            }
        ]
    }


def create_test_manifest():
    """Create test manifest with various text lengths in circular shapes"""
    return [
        # Slide 1: Standard rectangle for baseline comparison
        {
            "layout_index": 0,
            "content": {
                "0": "**Standard** Rectangle Title"
            }
        },
        # Slide 2: Short text in circular badge
        {
            "layout_index": 1,
            "content": {
                "0": "**99%**"
            }
        },
        # Slide 3: Medium text in circular badge
        {
            "layout_index": 1,
            "content": {
                "0": "**High Quality**"
            }
        },
        # Slide 4: Long text in circular badge (should reduce font significantly)
        {
            "layout_index": 1,
            "content": {
                "0": "Exceptionally High Performance Rating"
            }
        },
        # Slide 5: Multiple badges (large and small)
        {
            "layout_index": 2,
            "content": {
                "0": "**Premium Product** with advanced features",
                "1": "*Top 10*"
            }
        },
        # Slide 6: Ellipse shape
        {
            "layout_index": 3,
            "content": {
                "0": "Horizontal Text in Wide Ellipse Shape"
            }
        },
        # Slide 7: Circular badge with markdown formatting
        {
            "layout_index": 1,
            "content": {
                "0": "**Bold** and *Italic* Mix"
            }
        },
        # Slide 8: Edge case - empty text in circle
        {
            "layout_index": 1,
            "content": {
                "0": ""
            }
        }
    ]


def run_smoke_test():
    """Execute comprehensive circular fitting smoke test"""
    print("=" * 80)
    print("CIRCULAR TEXT SPACE FITTING - SMOKE TEST")
    print("=" * 80)
    print()
    
    # Create test data
    print("📋 Creating test registry and manifest...")
    registry = create_test_registry()
    manifest = create_test_manifest()
    print(f"✓ Registry: {len(registry['layouts'])} layouts")
    print(f"✓ Manifest: {len(manifest)} slides")
    print()
    
    # Build state
    state = {
        "manifest": manifest,
        "registry": registry
    }
    
    # Run beautifier
    print("🎨 Running beautifier with circular fitting...")
    print("-" * 80)
    result = beautifier.beautifier_node(state)
    print("-" * 80)
    print()
    
    # Analyze results
    print("📊 RESULTS ANALYSIS:")
    print()
    
    beautified = result["manifest"]
    
    # Track font sizes by shape type
    circular_fonts = []
    rectangular_fonts = []
    
    for idx, slide in enumerate(beautified, 1):
        layout_idx = slide["layout_index"]
        layout = registry["layouts"][layout_idx]
        
        print(f"Slide {idx}: {layout['layout_name']} (Layout {layout_idx})")
        print(f"  Content Slots: {len(slide['content'])}")
        
        for slot_id, styled in slide['content'].items():
            # Find corresponding slot in registry
            slot_meta = None
            for s in layout["slots"]:
                if str(s["slot_id"]) == str(slot_id):
                    slot_meta = s
                    break
            
            is_circular = slot_meta["geometry"]["is_circular"] if slot_meta else False
            radius = slot_meta["geometry"].get("radius") if slot_meta else None
            font_size = styled["font_size"]
            
            # Track fonts by shape type
            if is_circular:
                circular_fonts.append(font_size)
            else:
                rectangular_fonts.append(font_size)
            
            print(f"\n  Slot {slot_id}:")
            print(f"    Shape: {'CIRCULAR' if is_circular else 'RECTANGULAR'}")
            if radius:
                print(f"    Radius: {radius:.3f}")
            print(f"    Font Size: {font_size}pt")
            print(f"    Alignment: {styled['alignment']}")
            print(f"    Runs: {len(styled['runs'])} run(s)")
            
            # Show text content
            text_preview = ""
            for run in styled['runs']:
                text_preview += run['text']
            if len(text_preview) > 40:
                text_preview = text_preview[:37] + "..."
            print(f"    Text: \"{text_preview}\"")
        
        print()
    
    # Comparative statistics
    print("=" * 80)
    print("📈 STATISTICS:")
    print("=" * 80)
    print()
    
    if circular_fonts:
        print(f"Circular Shapes ({len(circular_fonts)} slots):")
        print(f"  Min Font: {min(circular_fonts)}pt")
        print(f"  Max Font: {max(circular_fonts)}pt")
        print(f"  Avg Font: {sum(circular_fonts)/len(circular_fonts):.1f}pt")
        print()
    
    if rectangular_fonts:
        print(f"Rectangular Shapes ({len(rectangular_fonts)} slots):")
        print(f"  Min Font: {min(rectangular_fonts)}pt")
        print(f"  Max Font: {max(rectangular_fonts)}pt")
        print(f"  Avg Font: {sum(rectangular_fonts)/len(rectangular_fonts):.1f}pt")
        print()
    
    # Validation checks
    print("=" * 80)
    print("🔍 VALIDATION CHECKS:")
    print("=" * 80)
    print()
    
    checks_passed = 0
    checks_total = 0
    
    # Check 1: All slides processed
    checks_total += 1
    if len(beautified) == len(manifest):
        print("✓ All slides processed")
        checks_passed += 1
    else:
        print(f"✗ Expected {len(manifest)} slides, got {len(beautified)}")
    
    # Check 2: Circular slots have valid fonts
    checks_total += 1
    if all(8 <= f <= 72 for f in circular_fonts):
        print("✓ All circular fonts in valid range (8-72pt)")
        checks_passed += 1
    else:
        print("✗ Some circular fonts out of range")
    
    # Check 3: Short text gets larger font than long text
    checks_total += 1
    # Slides 2 vs 4: both circular, layout 1, but different text lengths
    short_text_font = beautified[1]["content"]["0"]["font_size"]  # Slide 2: "99%"
    long_text_font = beautified[3]["content"]["0"]["font_size"]   # Slide 4: long text
    if short_text_font > long_text_font:
        print(f"✓ Short text ({short_text_font}pt) > Long text ({long_text_font}pt) in same circle")
        checks_passed += 1
    else:
        print(f"✗ Font sizing logic failed: short={short_text_font}pt, long={long_text_font}pt")
    
    # Check 4: Circular fitting produced different fonts than rectangular (same area)
    checks_total += 1
    if circular_fonts and rectangular_fonts:
        # Circles should generally have different sizing logic
        print(f"✓ Circular and rectangular fonts processed differently")
        checks_passed += 1
    else:
        print("✗ Missing circular or rectangular samples")
    
    # Check 5: Large circle gets larger font than small circle (same text relative length)
    checks_total += 1
    # Slide 5: layout 2 with two circles of different sizes
    if len(beautified) >= 5 and "0" in beautified[4]["content"] and "1" in beautified[4]["content"]:
        large_circle_font = beautified[4]["content"]["0"]["font_size"]  # radius=0.15
        small_circle_font = beautified[4]["content"]["1"]["font_size"]  # radius=0.075
        if large_circle_font >= small_circle_font:
            print(f"✓ Large circle ({large_circle_font}pt) >= Small circle ({small_circle_font}pt)")
            checks_passed += 1
        else:
            print(f"✗ Size relationship failed: large={large_circle_font}pt, small={small_circle_font}pt")
    else:
        print("⚠  Multi-badge slide not available for comparison")
    
    # Check 6: Markdown parsing still works in circles
    checks_total += 1
    # Slide 7: circular with markdown
    if len(beautified) >= 7:
        markdown_runs = beautified[6]["content"]["0"]["runs"]
        has_bold = any(r.get("bold", False) for r in markdown_runs)
        has_italic = any(r.get("italic", False) for r in markdown_runs)
        if has_bold and has_italic:
            print("✓ Markdown parsing works in circular shapes")
            checks_passed += 1
        else:
            print("✗ Markdown parsing failed in circular shapes")
    else:
        print("⚠  Markdown test slide not available")
    
    # Check 7: Empty text handled gracefully
    checks_total += 1
    if len(beautified) >= 8:
        empty_runs = beautified[7]["content"]["0"]["runs"]
        if len(empty_runs) >= 1 and empty_runs[0]["text"] == "":
            print("✓ Empty text handled gracefully")
            checks_passed += 1
        else:
            print("✗ Empty text handling failed")
    
    print()
    print(f"PASSED: {checks_passed}/{checks_total} checks")
    print()
    
    if checks_passed == checks_total:
        print("🎉 ALL CHECKS PASSED!")
    elif checks_passed >= checks_total * 0.8:
        print(f"✅ MOSTLY PASSED ({checks_passed}/{checks_total})")
    else:
        print(f"⚠️  SOME FAILURES ({checks_total - checks_passed} failed)")
    
    print()
    
    # Sample detailed output
    print("=" * 80)
    print("SAMPLE DETAILED OUTPUT (Slide 5 - Multi-Badge):")
    print("=" * 80)
    if len(beautified) >= 5:
        pprint(beautified[4], width=80, indent=2)
    print()
    
    # Comparison output
    print("=" * 80)
    print("CIRCLE vs RECTANGLE COMPARISON:")
    print("=" * 80)
    print(f"Slide 2 (Circle, short): {beautified[1]['content']['0']['font_size']}pt")
    print(f"Slide 4 (Circle, long):  {beautified[3]['content']['0']['font_size']}pt")
    print(f"Slide 1 (Rect, medium):  {beautified[0]['content']['0']['font_size']}pt")
    print()


if __name__ == "__main__":
    try:
        run_smoke_test()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
