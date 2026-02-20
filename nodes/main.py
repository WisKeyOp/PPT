import json
from graph import create_ppt_generator_graph

def run_pipeline():
    # 1. Load the Registry from Pipeline 1
    try:
        with open("template_registry.json", "r") as f:
            registry_data = json.load(f)
    except FileNotFoundError:
        print("❌ Error: Run Pipeline 1 first to generate template_registry.json")
        return

    # 2. Initialize the Graph
    app = create_ppt_generator_graph()

    # 3. Define the Initial State
    initial_state = {
        "registry": registry_data,
        "source_material": "DashResQ is an AI-powered accident detection system...",
        "user_context": "Target audience: Investors. Tone: Professional and data-driven.",
        "iteration_count": 0,
        "validation_errors": [],
        "status": "initialized"
    }

    # 4. Run the Agent
    print("🚀 Starting Pipeline 2...")
    result = app.invoke(initial_state)
    print(f"🏁 Generation Finished with status: {result['status']}")

if __name__ == "__main__":
    run_pipeline()