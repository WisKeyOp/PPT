from src.nodes.parser import parse_template_node

# Mock state
mock_state = {"template_path": "data/templates/ey_intro.pptx"}

try:
    result = parse_template_node(mock_state)
    print("\n--- Extraction Results ---")
    for shape in result["raw_shape_data"]:
        print(f"ID: {shape['slot_id']} | Name: {shape['name']} | Type: {shape['type']}")
except FileNotFoundError:
    print("Error: 'data/templates/ey_intro.pptx' not found. Please ensure the file exists.")
except Exception as e:
    print(f"An error occurred: {e}")
