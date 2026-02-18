"""
Manual Smoke Test for Beautifier Node
Tests beautifier with realistic registry and manifest data.

Run: python test_beautifier_smoke.py
"""
import json
import os
import sys
from pprint import pprint

# Add src to path to import beautifier directly without triggering pipeline __init__
src_path = os.path.join(os.path.dirname(__file__), 'src', 'nodes', 'pipeline_2_generation')
sys.path.insert(0, src_path)

# Verify the path exists before importing
if not os.path.exists(src_path):
    print(f"❌ ERROR: Path not found: {src_path}")
    print(f"Current directory: {os.getcwd()}")
    sys.exit(1)

# Direct import to avoid pipeline initialization
import beautifier

def load_registry():
    """Load real registry from data/registry/"""
    registry_path = "data/registry/template2.json"
    
    if not os.path.exists(registry_path):
        print(f"⚠️  Registry not found at {registry_path}")
        print("Using minimal mock registry instead...\n")
        return {
            "master_name": "test.pptx",
            "layouts": [
                {
                    "layout_index": 0,
                    "layout_name": "Title Slide",
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
                                "norm_top": 0.2,
                                "norm_left": 0.1,
                                "norm_width": 0.8,
                                "norm_height": 0.2
                            }
                        },
                        {
                            "slot_id": 1,
                            "role_name": "Subtitle",
                            "role_hint": "body",
                            "content_type": "text",
                            "max_chars": 120,
                            "geometry": {
                                "area_ratio": 0.25,
                                "norm_top": 0.5,
                                "norm_left": 0.1,
                                "norm_width": 0.8,
                                "norm_height": 0.3
                            }
                        }
                    ]
                },
                {
                    "layout_index": 1,
                    "layout_name": "Content Slide",
                    "layout_purpose": "CONTENT_SLIDE",
                    "slots": [
                        {
                            "slot_id": 0,
                            "role_name": "Title",
                            "role_hint": "title",
                            "content_type": "text",
                            "max_chars": 60,
                            "geometry": {
                                "area_ratio": 0.08,
                                "norm_top": 0.05,
                                "norm_left": 0.05,
                                "norm_width": 0.9,
                                "norm_height": 0.1
                            }
                        },
                        {
                            "slot_id": 16,
                            "role_name": "Content",
                            "role_hint": "content",
                            "content_type": "text",
                            "max_chars": 350,
                            "geometry": {
                                "area_ratio": 0.45,
                                "norm_top": 0.2,
                                "norm_left": 0.05,
                                "norm_width": 0.9,
                                "norm_height": 0.7
                            }
                        }
                    ]
                }
            ]
        }
    
    with open(registry_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def create_test_manifest():
    """Create test manifest with various edge cases"""
    return [
        # Slide 1: Valid layout with markdown
        {
            "layout_index": 0,
            "content": {
                "0": "**Product Launch** Strategy",
                "1": "Introducing our *innovative* solution to market challenges"
            }
        },
        # Slide 2: Different layout
        {
            "layout_index": 1,
            "content": {
                "0": "Key **Benefits**",
                "16": "Our solution offers **40% cost reduction**, *faster* deployment, and enhanced security. "
                      "The platform integrates seamlessly with existing infrastructure while providing "
                      "real-time analytics and automated reporting capabilities."
            }
        },
        # Slide 3: Unknown layout (should fallback)
        {
            "layout_index": 999,
            "content": {
                "0": "Fallback Test - Unknown Layout"
            }
        },
        # Slide 4: Content exceeding max_chars
        {
            "layout_index": 0,
            "content": {
                "0": "x" * 150,  # Exceeds typical max_chars for title
                "1": "Normal content here"
            }
        },
        # Slide 5: Edge cases in markdown
        {
            "layout_index": 1,
            "content": {
                "0": "Edge Cases",
                "16": "Escaped: \\*not italic\\*, Word boundary: fi*sh*ing, Unbalanced: **bold only, "
                      "Multiple: **first** and **second**, Adjacent: **bold***italic*"
            }
        },
        # Slide 6: None and empty content
        {
            "layout_index": 0,
            "content": {
                "0": None,  # Should become empty string, not "None"
                "1": ""     # Empty string
            }
        },
        # Slide 7: Numeric formatting (right-aligned test)
        {
            "layout_index": 1,
            "content": {
                "0": "Quarterly *Results*",
                "16": "Revenue: **$2.5M** | Growth: **35%** | Customers: **1,200**"
            }
        }
    ]


def run_smoke_test():
    """Execute smoke test with comprehensive scenarios"""
    print("=" * 70)
    print("BEAUTIFIER NODE - SMOKE TEST")
    print("=" * 70)
    print()
    
    # Load registry
    print("📁 Loading registry...")
    registry = load_registry()
    print(f"✓ Loaded {len(registry.get('layouts', []))} layouts")
    print()
    
    # Create test manifest
    print("📝 Creating test manifest...")
    manifest = create_test_manifest()
    print(f"✓ Created {len(manifest)} test slides")
    print()
    
    # Build state
    state = {
        "manifest": manifest,
        "registry": registry
    }
    
    # Run beautifier
    print("🎨 Running beautifier node...")
    print("-" * 70)
    result = beautifier.beautifier_node(state)
    print("-" * 70)
    print()
    
    # Display results
    print("📊 RESULTS:")
    print()
    
    beautified = result["manifest"]
    
    for idx, slide in enumerate(beautified, 1):
        print(f"Slide {idx}:")
        print(f"  Layout Index: {slide['layout_index']}")
        print(f"  Content Slots: {len(slide['content'])}")
        
        for slot_id, styled in slide['content'].items():
            print(f"\n  Slot {slot_id}:")
            print(f"    Font Size: {styled['font_size']}pt")
            print(f"    Alignment: {styled['alignment']}")
            print(f"    Runs: {len(styled['runs'])} run(s)")
            
            # Show runs details
            for run_idx, run in enumerate(styled['runs']):
                style_flags = []
                if run['bold']:
                    style_flags.append("BOLD")
                if run['italic']:
                    style_flags.append("ITALIC")
                style_str = f" ({', '.join(style_flags)})" if style_flags else ""
                
                # Truncate long text
                text = run['text']
                if len(text) > 50:
                    display_text = text[:47] + "..."
                else:
                    display_text = text
                
                print(f"      Run {run_idx + 1}: \"{display_text}\"{style_str}")
        
        print()
    
    print("=" * 70)
    print("✅ SMOKE TEST COMPLETE")
    print("=" * 70)
    print()
    
    # Validation checks
    print("🔍 VALIDATION CHECKS:")
    checks_passed = 0
    checks_total = 0
    
    # Check 1: All slides processed
    checks_total += 1
    if len(beautified) == len(manifest):
        print("✓ All slides processed")
        checks_passed += 1
    else:
        print(f"✗ Expected {len(manifest)} slides, got {len(beautified)}")
    
    # Check 2: Unknown layout fallback worked
    checks_total += 1
    if beautified[2]['layout_index'] == 0:  # Slide 3 should fallback to 0
        print("✓ Unknown layout fallback working")
        checks_passed += 1
    else:
        print(f"✗ Unknown layout fallback failed (got {beautified[2]['layout_index']})")
    
    # Check 3: None handling (slide 6, slot 0)
    checks_total += 1
    slide_6_runs = beautified[5]['content']['0']['runs']
    if slide_6_runs[0]['text'] == "":
        print("✓ None text converted to empty string (not 'None')")
        checks_passed += 1
    else:
        print(f"✗ None handling failed (got '{slide_6_runs[0]['text']}')")
    
    # Check 4: Bold parsing (slide 1, slot 0)
    checks_total += 1
    slide_1_runs = beautified[0]['content']['0']['runs']
    has_bold = any(r['bold'] for r in slide_1_runs)
    if has_bold:
        print("✓ Bold markdown parsing working")
        checks_passed += 1
    else:
        print("✗ Bold markdown parsing failed")
    
    # Check 5: Italic parsing (slide 1, slot 1)
    checks_total += 1
    slide_1_sub_runs = beautified[0]['content']['1']['runs']
    has_italic = any(r['italic'] for r in slide_1_sub_runs)
    if has_italic:
        print("✓ Italic markdown parsing working")
        checks_passed += 1
    else:
        print("✗ Italic markdown parsing failed")
    
    # Check 6: Alignment based on role_hint
    checks_total += 1
    slide_1_alignment = beautified[0]['content']['0']['alignment']
    # Note: Real registry may have different role_hints per layout
    # This just verifies alignment was set (not default None)
    if slide_1_alignment in ["CENTER", "LEFT", "RIGHT"]:
        print(f"✓ Alignment logic working (slot 0 = {slide_1_alignment})")
        checks_passed += 1
    else:
        print(f"✗ Alignment logic failed (got {slide_1_alignment})")
    
    # Check 7: Geometry-based font sizing applied
    checks_total += 1
    title_font = beautified[0]['content']['0']['font_size']
    # Font size should be reasonable (not 0 or None)
    if isinstance(title_font, int) and 10 <= title_font <= 40:
        print(f"✓ Geometry-based font sizing working (font_size = {title_font}pt)")
        checks_passed += 1
    else:
        print(f"✗ Font sizing failed (got {title_font})")
    
    print()
    print(f"PASSED: {checks_passed}/{checks_total} checks")
    print()
    
    if checks_passed == checks_total:
        print("🎉 ALL CHECKS PASSED!")
    else:
        print(f"⚠️  {checks_total - checks_passed} check(s) failed")
    
    print()
    
    # Optional: Pretty print a sample slide for manual inspection
    print("=" * 70)
    print("SAMPLE OUTPUT (Slide 2 - Full Details):")
    print("=" * 70)
    pprint(beautified[1], width=70, indent=2)
    print()


if __name__ == "__main__":
    try:
        run_smoke_test()
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
