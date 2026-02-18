import os
from dotenv import load_dotenv

# Force reload of .env file
load_dotenv(override=True)
from src.core.graph import create_pipeline1_graph
import json

def run_pipeline_1(template_filename: str):
    # 1. Setup the initial state
    # We point to the template you created in your data folder
    initial_state = {
        "template_path": f"data/templates/{template_filename}",
        "raw_shape_data": [],
        "json_description": None,
        "is_valid": False
    }

    # 2. Initialize the Graph
    app = create_pipeline1_graph()

    # 3. Execute the Graph
    print(f"--- 🚀 Starting Pipeline 1 for: {template_filename} ---")
    
    # We use a thread_id because LangGraph requires it for 
    # checkpointing (even if we aren't pausing yet)
    config = {"configurable": {"thread_id": "ey_init_001"}}
    
    final_state = app.invoke(initial_state, config=config)

    # 4. Save the Result to the Registry
    if final_state.get("json_description"):
        registry_path = f"data/registry/{template_filename.replace('.pptx', '.json')}"
        with open(registry_path, "w") as f:
            json.dump(final_state["json_description"], f, indent=4)
        
        print(f"--- ✅ Success! Metadata saved to: {registry_path} ---")
    else:
        print("--- ❌ Pipeline failed to generate metadata. ---")

if __name__ == "__main__":
    import pathlib
    
    # Define templates directory
    templates_dir = pathlib.Path("data/templates")
    
    # Check if directory exists
    if not templates_dir.exists():
        print(f"Error: Directory '{templates_dir}' not found. Please create it and add .pptx files.")
        exit(1)
        
    # Find all .pptx files
    pptx_files = list(templates_dir.glob("*.pptx"))
    
    if not pptx_files:
        print(f"No .pptx files found in '{templates_dir}'.")
    else:
        print(f"--- Found {len(pptx_files)} templates to process ---")
        for pptx_file in pptx_files:
            run_pipeline_1(pptx_file.name)
