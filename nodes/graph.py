from langgraph.graph import StateGraph, END
from state import PPTState
from nodes import content_distiller_node, structural_architect_node, final_generator_node

def create_ppt_generator_graph():
    workflow = StateGraph(PPTState)

    # Add Nodes
    workflow.add_node("distiller", content_distiller_node)
    workflow.add_node("architect", structural_architect_node)
    workflow.add_node("generator", final_generator_node)

    # Set Flow
    workflow.set_entry_point("distiller")
    workflow.add_edge("distiller", "architect")

    # Conditional Logic: If architect fails/overflows, we could loop. 
    # For now, we go straight to generator.
    workflow.add_edge("architect", "generator")
    workflow.add_edge("generator", END)

    return workflow.compile()