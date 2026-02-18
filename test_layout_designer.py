import sys
import os
from dotenv import load_dotenv

# Load .env variables immediately
load_dotenv()

# Ensure src is in pythonpath
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.nodes.layout_designer import design_slide_layout
from src.core.layout_models import StrictLayout, Coordinates, StrictSlot, Styling
from pydantic import ValidationError

def test_valid_layout_generation():
    print("\n--- Testing Valid Generation ---")
    try:
        layout = design_slide_layout(
            topic="Annual Financial Report",
            purpose="Present key revenue metrics with a clear data table and summary."
        )
        print("Success! Generated Layout:")
        print(layout.model_dump_json(indent=2))
        
        # Manual Assertions just in case
        assert layout.slots[0].slot_id == 1
        assert layout.canvas['width'] == 1920
        
    except Exception as e:
        print(f"FAILED: {e}")
        raise e

def test_pydantic_enforcement():
    print("\n--- Testing Pydantic Enforcement (Simulated Failure) ---")
    
    # 1. Non-Sequential IDs
    print("Test 1: Non-Sequential IDs")
    try:
        bad_slots = [
            StrictSlot(
                slot_id=1, role="HEADER", content_type="text",
                coordinates=Coordinates(x=0,y=0,w=100,h=100),
                styling=Styling(font_size=50, font_weight="bold", alignment="center", hex_color="#000000"),
                description="Header"
            ),
            StrictSlot(
                slot_id=3, role="FOOTER", content_type="text", # Skipped 2
                coordinates=Coordinates(x=0,y=900,w=100,h=100),
                styling=Styling(font_size=20, font_weight="normal", alignment="center", hex_color="#000000"),
                description="Footer"
            )
        ]
        StrictLayout(template_name="fail", total_slots=2, slots=bad_slots)
        print("FAILED: Should have raised ValueError for non-sequential IDs")
    except ValueError as e:
        print(f"PASSED: Caught expected error: {e}")
    except Exception as e:
        print(f"FAILED: Caught unexpected error: {type(e)} - {e}")

    # 2. Header Position Violation
    print("\nTest 2: Header Position Violation")
    try:
        bad_header = [
            StrictSlot(
                slot_id=1, role="HEADER", content_type="text",
                coordinates=Coordinates(x=0,y=500,w=100,h=100), # y=500 is > 270
                styling=Styling(font_size=50, font_weight="bold", alignment="center", hex_color="#000000"),
                description="Header"
            )
        ]
        StrictLayout(template_name="fail_pos", total_slots=1, slots=bad_header)
        print("FAILED: Should have raised ValueError for Header Y pos")
    except ValueError as e:
        print(f"PASSED: Caught expected error: {e}")

    # 3. Collision Detection
    print("\nTest 3: Collision Detection")
    try:
        colliding_slots = [
            StrictSlot(
                slot_id=1, role="BODY_COPY", content_type="text",
                coordinates=Coordinates(x=100,y=100,w=200,h=200),
                styling=Styling(font_size=20, font_weight="normal", alignment="left", hex_color="#000000"),
                description="Box 1"
            ),
            StrictSlot(
                slot_id=2, role="BODY_COPY", content_type="text",
                coordinates=Coordinates(x=150,y=150,w=200,h=200), # Overlaps
                styling=Styling(font_size=20, font_weight="normal", alignment="left", hex_color="#000000"),
                description="Box 2"
            )
        ]
        StrictLayout(template_name="fail_col", total_slots=2, slots=colliding_slots)
        print("FAILED: Should have raised ValueError for Collision")
    except ValueError as e:
        print(f"PASSED: Caught expected error: {e}")

    # 4. Safe Zone Violation
    print("\nTest 4: Safe Zone Violation")
    try:
        bad_safe = [
            StrictSlot(
                slot_id=1, role="BODY_COPY", content_type="text",
                coordinates=Coordinates(x=10,y=10,w=100,h=100), # x=10 is < 100 margin
                styling=Styling(font_size=20, font_weight="normal", alignment="left", hex_color="#000000"),
                description="Box 1"
            )
        ]
        StrictLayout(template_name="fail_safe", total_slots=1, slots=bad_safe)
        print("FAILED: Should have raised ValueError for Safe Zone")
    except ValueError as e:
        print(f"PASSED: Caught expected error: {e}")

    # 5. Padding Violation (Too Close)
    print("\nTest 5: Padding Violation")
    try:
        crowded_slots = [
            StrictSlot(
                slot_id=1, role="BODY_COPY", content_type="text",
                coordinates=Coordinates(x=200,y=200,w=100,h=100),
                styling=Styling(font_size=20, font_weight="normal", alignment="left", hex_color="#000000"),
                description="Box 1"
            ),
            StrictSlot(
                slot_id=2, role="BODY_COPY", content_type="text",
                coordinates=Coordinates(x=305,y=200,w=100,h=100), # x=305. 305 - (200+100) = 5px gap. < 20px padding.
                styling=Styling(font_size=20, font_weight="normal", alignment="left", hex_color="#000000"),
                description="Box 2"
            )
        ]
        StrictLayout(template_name="fail_padding", total_slots=2, slots=crowded_slots)
        print("FAILED: Should have raised ValueError for Padding")
    except ValueError as e:
        print(f"PASSED: Caught expected error: {e}")

if __name__ == "__main__":
    # We run the unit tests first to verify our logic is strict
    test_pydantic_enforcement()
    
    # Skipped due to known environment/firewall issues
    # test_valid_layout_generation()
