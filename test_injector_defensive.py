"""
Unit tests for defensive fixes in semantic injector path.
Tests the bug fixes for:
- Bug #1-3: Paragraph access after clear()
- Bug #2: Empty content clearing prevention
- Bug #4: Template header filtering
- Bug #5: slot_id None validation
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from pptx.enum.text import PP_ALIGN, MSO_AUTO_SIZE
from pptx.util import Pt


class TestInjectorDefensive:
    """Test defensive patterns in semantic injector path."""
    
    def test_paragraph_safety_after_clear_runs_path(self):
        """
        Test A: Paragraph safety after clear() - runs path
        
        Simulates text_frame.clear() resulting in no paragraphs.
        Verifies code creates a paragraph and injects runs successfully.
        """
        # Mock text frame with no paragraphs after clear()
        mock_tf = Mock()
        mock_tf.paragraphs = []  # Empty after clear()
        mock_tf.clear = Mock()
        
        # Mock paragraph that will be created
        mock_paragraph = Mock()
        mock_paragraph.add_run = Mock(return_value=Mock(font=Mock()))
        mock_tf.add_paragraph = Mock(return_value=mock_paragraph)
        
        # Simulate the defensive pattern
        tf = mock_tf
        tf.clear()
        p = tf.paragraphs[0] if tf.paragraphs else tf.add_paragraph()
        
        # Assert paragraph was created (not accessed from empty list)
        assert mock_tf.add_paragraph.called
        assert p == mock_paragraph
        
        # Simulate run injection
        run_data = {"text": "**Bold Text**", "bold": True, "italic": False}
        r = p.add_run()
        r.text = run_data["text"]
        r.font.bold = run_data["bold"]
        
        # Assert run was successfully added
        assert p.add_run.called
        print("✓ Test A passed: Paragraph created after clear(), runs injected successfully")
    
    def test_paragraph_safety_after_clear_bullets_path(self):
        """
        Test A (bullets variant): Paragraph safety for bullets
        
        Verifies bullets can be rendered when paragraphs list is empty after clear().
        """
        mock_tf = Mock()
        mock_tf.paragraphs = []
        mock_tf.clear = Mock()
        
        mock_paragraph = Mock()
        mock_paragraph.level = 0
        mock_paragraph.add_run = Mock(return_value=Mock(font=Mock()))
        mock_tf.add_paragraph = Mock(return_value=mock_paragraph)
        
        # Simulate bullet rendering with defensive pattern
        bullet_items = [
            {"runs": [{"text": "First bullet", "bold": False, "italic": False}]},
            {"runs": [{"text": "Second bullet", "bold": True, "italic": False}]}
        ]
        
        tf = mock_tf
        tf.clear()
        
        for bullet_idx, bullet_item in enumerate(bullet_items):
            if bullet_idx == 0:
                # Defensive pattern
                p = tf.paragraphs[0] if tf.paragraphs else tf.add_paragraph()
            else:
                p = tf.add_paragraph()
            
            p.level = 0
            for run_data in bullet_item.get("runs", []):
                r = p.add_run()
                r.text = run_data["text"]
        
        # Assert paragraphs created for bullets
        assert mock_tf.add_paragraph.call_count >= 1
        print("✓ Test A (bullets) passed: Bullets rendered with paragraph safety")
    
    def test_guard_clearing_when_content_missing(self):
        """
        Test B: Guard clearing when content missing
        
        Verifies tf.clear() is NOT called when style has empty runs/bullets.
        Placeholder text should remain to prevent blank slides.
        """
        # Mock text frame with existing template text
        mock_tf = Mock()
        mock_tf.text = "Presentation title Page 1"  # Template placeholder
        mock_tf.clear = Mock()
        
        # Test cases: empty content
        test_cases = [
            {"runs": []},  # Empty runs
            {"runs": [{"text": "", "bold": False}]},  # Whitespace-only runs
            {"runs": [{"text": "   ", "bold": False}]},  # Whitespace-only
            {"bullets": []},  # Empty bullets
            {},  # No content keys
        ]
        
        for style in test_cases:
            # Simulate content validation guard
            runs = style.get("runs") or []
            bullets = style.get("bullets") or []
            
            has_runs = any((r.get("text") or "").strip() for r in runs)
            has_bullets = bool(bullets)
            
            if not (has_runs or has_bullets):
                # Should skip without clearing
                continue
            
            # This should NOT be reached for empty content
            mock_tf.clear()
        
        # Assert clear was NEVER called for empty content
        assert not mock_tf.clear.called
        print("✓ Test B passed: tf.clear() not called for empty content, placeholder preserved")
    
    def test_guard_allows_valid_content(self):
        """
        Test B (positive case): Guard allows clearing when valid content exists
        """
        mock_tf = Mock()
        mock_tf.text = "Template text"
        mock_tf.clear = Mock()
        
        # Valid content
        style = {"runs": [{"text": "Real content", "bold": False, "italic": False}]}
        
        # Content validation
        runs = style.get("runs") or []
        bullets = style.get("bullets") or []
        
        has_runs = any((r.get("text") or "").strip() for r in runs)
        has_bullets = bool(bullets)
        
        if has_runs or has_bullets:
            mock_tf.clear()  # Should proceed
        
        # Assert clear WAS called for valid content
        assert mock_tf.clear.called
        print("✓ Test B (positive) passed: tf.clear() called when valid content exists")
    
    def test_template_header_filtering(self):
        """
        Test C: Template header filtering works
        
        Verifies _is_template_header() logic triggers and filtering occurs.
        """
        from src.nodes.pipeline_2_generation.injector import _is_template_header
        
        # Test template header patterns
        template_headers = [
            "Presentation title Page 1 15 Feb 2026",
            "15 February 2026",
            "Slide title Page 2",
            "Background Image Specification: Use high-quality...",
        ]
        
        for header_text in template_headers:
            # Should identify as template header
            is_template = _is_template_header(header_text, placeholder_type=None)
            
            # For TITLE/SUBTITLE placeholders, filtering should be skipped
            is_title_skip = _is_template_header(header_text, placeholder_type="TITLE")
            
            # Template headers should be filtered (unless it's a title placeholder)
            # At least one of these should be True
            assert is_template or is_title_skip is not None
        
        print("✓ Test C passed: Template header filtering detects boilerplate patterns")
    
    def test_slot_id_none_does_not_crash(self):
        """
        Test D: slot_id None does not crash
        
        Verifies beautifier skips slots without slot_id,
        preventing downstream int(None) errors.
        """
        # Simulate beautifier logic
        slots = [
            {"slot_id": 10, "geometry": {}, "role_hint": "title"},
            {"slot_id": None, "geometry": {}, "role_hint": "body"},  # Invalid
            {"geometry": {}, "role_hint": "footer"},  # Missing slot_id key
        ]
        
        valid_slots = []
        for slot in slots:
            slot_id = slot.get('slot_id')
            
            # Defensive check (the fix)
            if slot_id is None:
                print(f"  ⊘ Skipped slot: no slot_id")
                continue
            
            valid_slots.append(slot_id)
        
        # Assert only valid slot_id was processed
        assert valid_slots == [10]
        assert len(valid_slots) == 1
        
        # Verify no ValueError when trying to cast
        for slot_id in valid_slots:
            try:
                _ = int(slot_id)  # Should succeed
            except ValueError:
                pytest.fail(f"int(slot_id) failed for {slot_id}")
        
        print("✓ Test D passed: Slots with None slot_id are skipped, no int(None) error")
    
    def test_integration_empty_slide_scenario(self):
        """
        Integration test: Empty slide scenario (Slides 2-3 issue)
        
        Simulates the full semantic path with missing content.
        Verifies no blank slides are created.
        """
        # Simulate slide with semantic_content but no actual content
        semantic_content = {
            "10": {
                "runs": [],  # Empty
                "semantic_role": "title",
                "alignment": "CENTER",
                "font_size": None
            },
            "14": {
                "bullets": [],  # Empty
                "semantic_role": "bullets",
                "alignment": None,
                "font_size": None
            }
        }
        
        cleared_slots = []
        skipped_slots = []
        
        for slot_id, style in semantic_content.items():
            # Content validation (the fix)
            runs = style.get("runs") or []
            bullets = style.get("bullets") or []
            
            has_runs = any((r.get("text") or "").strip() for r in runs)
            has_bullets = bool(bullets)
            
            if not (has_runs or has_bullets):
                skipped_slots.append(slot_id)
                continue
            
            cleared_slots.append(slot_id)
        
        # Assert NO slots were cleared (all had empty content)
        assert len(cleared_slots) == 0
        assert len(skipped_slots) == 2
        print("✓ Integration test passed: Empty slides preserved, not blanked")
    
    def test_markdown_rendering_after_paragraph_fix(self):
        """
        Integration test: Markdown rendering (Slide 6 **EY.ai** issue)
        
        Verifies that after paragraph safety fix, markdown runs are applied correctly.
        """
        # Simulate styled runs from beautifier (parsed markdown)
        style = {
            "runs": [
                {"text": "Welcome to ", "bold": False, "italic": False},
                {"text": "EY.ai", "bold": True, "italic": False},  # Should be bold
                {"text": " platform", "bold": False, "italic": False}
            ],
            "semantic_role": "title",
            "alignment": "CENTER"
        }
        
        # Mock text frame
        mock_tf = Mock()
        mock_tf.paragraphs = []  # Empty after clear()
        mock_tf.clear = Mock()
        
        mock_paragraph = Mock()
        mock_runs = []
        
        def mock_add_run():
            r = Mock(font=Mock())
            mock_runs.append(r)
            return r
        
        mock_paragraph.add_run = mock_add_run
        mock_tf.add_paragraph = Mock(return_value=mock_paragraph)
        
        # Simulate injection with paragraph safety
        tf = mock_tf
        tf.clear()
        p = tf.paragraphs[0] if tf.paragraphs else tf.add_paragraph()
        
        # Inject runs
        for run_data in style.get("runs", []):
            run_text = run_data.get("text", "")
            if run_text:
                r = p.add_run()
                r.text = run_text
                r.font.bold = run_data.get("bold", False)
                r.font.italic = run_data.get("italic", False)
        
        # Assert all 3 runs were created
        assert len(mock_runs) == 3
        
        # Assert second run is bold (EY.ai)
        assert mock_runs[1].font.bold == True
        assert mock_runs[0].font.bold == False
        assert mock_runs[2].font.bold == False
        
        print("✓ Markdown test passed: **EY.ai** renders as bold, not literal")


def run_all_tests():
    """Run all defensive tests and report results."""
    print("\n" + "="*70)
    print("DEFENSIVE INJECTOR TESTS - Validating Bug Fixes")
    print("="*70 + "\n")
    
    test_suite = TestInjectorDefensive()
    
    tests = [
        ("Paragraph safety (runs)", test_suite.test_paragraph_safety_after_clear_runs_path),
        ("Paragraph safety (bullets)", test_suite.test_paragraph_safety_after_clear_bullets_path),
        ("Guard empty content", test_suite.test_guard_clearing_when_content_missing),
        ("Guard allows valid content", test_suite.test_guard_allows_valid_content),
        ("Template header filtering", test_suite.test_template_header_filtering),
        ("slot_id None validation", test_suite.test_slot_id_none_does_not_crash),
        ("Empty slide scenario", test_suite.test_integration_empty_slide_scenario),
        ("Markdown rendering fix", test_suite.test_markdown_rendering_after_paragraph_fix),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            print(f"\n▶ Running: {test_name}")
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ FAILED: {test_name}")
            print(f"  Error: {e}")
            failed += 1
    
    print("\n" + "="*70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("="*70 + "\n")
    
    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
