import os
from pathlib import Path
import json
from dotenv import load_dotenv
from src.core.graph import create_pipeline1_graph

def start_indexing():
    # Load environment variables from .env file
    load_dotenv()
    # 1. Setup paths
    # Using absolute path for safety, but relative works if run from root
    root_dir = Path.cwd()
    templates_dir = root_dir / "data" / "templates"
    registry_dir = root_dir / "data" / "registry"
    registry_dir.mkdir(parents=True, exist_ok=True)

    # 2. Find templates
    template_files = list(templates_dir.glob("*.pptx"))
    if not template_files:
        print(f"❌ No .pptx files found in {templates_dir}")
        return

    # 3. Initialize the Graph
    app = create_pipeline1_graph()
    
    print(f"--- 🚀 Starting Pipeline 1 for {len(template_files)} files ---")

    for template in template_files:
        print(f"\n📄 Processing: {template.name}...")
        
        # We pass the path as the initial state
        initial_state = {
            "template_path": str(template),
            "raw_shape_data": [],
            "json_description": None,
            "is_valid": False
        }
        
        # Run the graph
        config = {"configurable": {"thread_id": f"index_{template.stem}"}}
        try:
            result = app.invoke(initial_state, config=config)
            
            # 4. Save the Registry
            if result.get("json_description"):
                output_path = registry_dir / f"{template.stem}.json"
                with open(output_path, "w", encoding='utf-8') as f:
                    # result['json_description'] might already be a dict or a JSON string
                    # based on your LLM node implementation
                    data = result["json_description"]
                    if isinstance(data, str):
                        f.write(data)
                    else:
                        json.dump(data, f, indent=4)
                
                print(f"✅ Created Registry: {output_path}")
            else:
                print(f"⚠️ Failed to generate metadata for {template.name} (no json_description returned)")
        except Exception as e:
            print(f"❌ Error processing {template.name}: {e}")

if __name__ == "__main__":
    start_indexing()
