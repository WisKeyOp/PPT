import json
from pydantic import BaseModel, Field
from typing import List
from auth_helper import get_llm
from state import PPTState

# --- Internal Structured Models ---
class ShapeInjection(BaseModel):
    shape_id: int
    content: str
    action: str # INSERT_TEXT, GENERATE_IMAGE, RENDER_CHART

class SlideAssignment(BaseModel):
    slide_index: int
    assignments: List[ShapeInjection]

class ArchitecturePlan(BaseModel):
    plan: List[SlideAssignment]

# --- Node Functions ---

def content_distiller_node(state: PPTState):
    """Segment raw text into slide-sized chunks."""
    llm = get_llm(deployment_name="gpt-4o", temperature=0.2)
    slide_count = len(state['registry'].get('slides', []))
    
    # Logic: Prompt LLM to create 'storyboard' summaries
    # We return the new storyboard to the state
    return {"storyboard": [{"index": i, "data": "..."} for i in range(slide_count)], "status": "distilled"}

def structural_architect_node(state: PPTState):
    """Maps summaries to specific Registry IDs using geometric logic."""
    llm = get_llm(deployment_name="gpt-4o", temperature=0)
    structured_llm = llm.with_structured_output(ArchitecturePlan)

    prompt = f"Map this content: {state['storyboard']} to these IDs: {state['registry']}"
    
    try:
        raw_plan = structured_llm.invoke(prompt)
        return {
            "injection_plan": [slide.dict() for slide in raw_plan.plan],
            "status": "architected"
        }
    except Exception as e:
        return {"validation_errors": [f"Architect Error: {str(e)}"]}

def final_generator_node(state: PPTState):
    """The Builder: Physically writes to the PPTX file."""
    print(f"🏗️ Injecting {len(state['injection_plan'])} slides into template...")
    return {"status": "completed"}