"""
Search Engine for Template Registry
Helps the system "load the menu" before the Slide Architect starts working.
"""
import json
from pathlib import Path
from typing import Dict, Any

def load_all_registries(registry_dir: str = "data/registry/") -> Dict[str, Any]:
    """
    Scans the registry folder and combines all JSON metadata 
    into a single searchable dictionary.
    
    Returns:
        Dict[str, Any]: A dictionary where keys are template filenames (without extension)
                        and values are the layout metadata.
    """
    combined = {}
    path = Path(registry_dir)
    
    if not path.exists():
        print(f"Warning: Registry directory '{registry_dir}' not found")
        return {}
    
    # Glob for all .json files
    found_files = list(path.glob("*.json"))
    print(f"--- Registry Helper: Found {len(found_files)} registry files ---")
    
    for json_file in found_files:
        try:
            with open(json_file, "r") as f:
                data = json.load(f)
                # We key it by the filename so the Architect knows which master it belongs to
                # json_file.stem gives us 'brand_guide' from 'brand_guide.json'
                combined[json_file.stem] = data
        except Exception as e:
            print(f"Error loading {json_file}: {e}")
            
    return combined
