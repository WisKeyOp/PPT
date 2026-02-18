"""
Pipeline 2 StateGraph: Surgical Template Injection Workflow
Enforces strict separation of concerns with dedicated styling node
"""
import os
from langgraph.graph import StateGraph, END
from src.core.state import PPTState
from src.utils.vault_client import VaultClient
from src.nodes.pipeline_2_generation import (
    extract_context_node,
    architect_slides_node,
    writer_node,
    image_director_node,
    beautifier_node,
    surgical_injection_node
)

def create_pipeline2_graph():
    """
    Creates the Pipeline 2 workflow graph for surgical template injection.
    
    Flow:
    1. Extractor: Condense raw docs into content_map
    2. Architect: Match content to templates, create slide_plans with roles
    3. Writer: Generate specific content for each slide (create manifest)
    4. Image Director: Enrich manifest with background image specs
    5. Beautifier: Convert text to deterministic style instructions (IR)
    6. Injector: Perform surgical injection and create .pptx
    
    The Beautifier serves as the "contract enforcement boundary" between
    LLM-generated content and physical document rendering.
    """
    # PRE-FETCH VAULT CREDENTIALS (forces single fetch per pipeline run)
    if os.getenv("KEYVAULTURL"):
        VaultClient.get_api_key()
    
    workflow = StateGraph(PPTState)
    
    # Add nodes
    workflow.add_node("extractor", extract_context_node)
    workflow.add_node("architect", architect_slides_node)
    workflow.add_node("writer", writer_node)
    workflow.add_node("image_director", image_director_node)
    workflow.add_node("beautifier", beautifier_node)
    workflow.add_node("injector", surgical_injection_node)
    
    # Define flow with Image Director and Beautifier in the pipeline
    workflow.set_entry_point("extractor")
    workflow.add_edge("extractor", "architect")
    workflow.add_edge("architect", "writer")
    workflow.add_edge("writer", "image_director")
    workflow.add_edge("image_director", "beautifier")
    workflow.add_edge("beautifier", "injector")
    
    workflow.add_edge("injector", END)
    
    return workflow.compile()
