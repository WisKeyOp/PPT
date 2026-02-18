# StateGraph orchestration
from langgraph.graph import StateGraph, END
from src.core.state import Pipeline1State
from src.nodes.pipeline_1_indexing import parse_template_node, build_registry_node

def create_pipeline1_graph():
    # 1. Initialize the Graph with our State schema
    workflow = StateGraph(Pipeline1State)

    # 2. Add the Nodes (The "Workstations")
    workflow.add_node("parser", parse_template_node)
    workflow.add_node("registry_builder", build_registry_node)

    # 3. Define the Edges (The "Flow")
    workflow.set_entry_point("parser")
    workflow.add_edge("parser", "registry_builder")

    # 4. Add the HITL logic
    # We want the graph to stop after 'registry_builder' so the Human can review the JSON.
    workflow.add_edge("registry_builder", END)

    # 5. Compile the graph
    return workflow.compile()