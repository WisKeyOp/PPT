# src/nodes/pipeline_2_generation/architect.py
"""
Pipeline 2 Node: Architect
Responsibility: Decide WHAT slides to create and in WHAT order
Enforces narrative arc, slide roles, and prevents layout hallucinations
"""
from src.core.state import PPTState, ArchitecturePlan
from pydantic import BaseModel, Field, ConfigDict
import json
from src.utils.auth_helper import get_llm

# Slide role constants
ROLE_TITLE = "TITLE"
ROLE_AGENDA = "AGENDA"
ROLE_CONTENT = "CONTENT"
ROLE_DIAGRAM = "DIAGRAM"
ROLE_TIMELINE = "TIMELINE"
ROLE_CLOSING = "CLOSING"

# NO_IMAGE mode: Exclude all layouts with image placeholders
NO_IMAGE_MODE = True

# Lazy LLM initialization
_llm_instance = None

def _get_llm():
    """Lazy load LLM instance."""
    global _llm_instance
    if _llm_instance is None:
        llm_base = get_llm(deployment_name="gpt-4", temperature=0.2)
        _llm_instance = llm_base.with_structured_output(ArchitecturePlan)
    return _llm_instance
 
def _map_purpose_to_role(purpose: str) -> str:
    """Map layout_purpose to slide_role with safe defaults."""
    purpose_upper = purpose.upper()
    if "TITLE" in purpose_upper:
        return ROLE_TITLE
    elif "COMPARISON" in purpose_upper or "DATA" in purpose_upper:
        return ROLE_DIAGRAM
    elif "VISUAL" in purpose_upper:
        return ROLE_CONTENT
    else:
        return ROLE_CONTENT


def architect_slides_node(state: PPTState):
    """
    Pipeline 2 – Node 2
    Converts content_map into an ordered slide plan with enforced roles.
    
    Enforces:
    - Slide 1: TITLE role (always)
    - Slide 2: AGENDA role (always)
    - Remaining slides: CONTENT, DIAGRAM, TIMELINE based on content
    - Optional last slide: CLOSING role
    - Layout diversity (no more than 2 uses of the same layout)
    - Layout purpose matching
    """
    content_map = state["content_map"]
    registry = state["registry"]
    
    # Get all layouts
    all_layouts = registry.get("layouts", [])
    
    # CRITICAL: Filter out image layouts in NO_IMAGE mode
    if NO_IMAGE_MODE:
        filtered_layouts = [l for l in all_layouts if not l.get('has_image_slot', False)]
        print(f"  🚫 NO_IMAGE mode: Excluded {len(all_layouts) - len(filtered_layouts)} image layouts")
        all_layouts = filtered_layouts
    
    if not all_layouts:
        raise ValueError("No text-only layouts available after NO_IMAGE filtering")
    
    # Build simplified layout summary with role metadata
    layout_summary = []
    for l in all_layouts:
        # Get or infer layout_role
        explicit_role = l.get("layout_role")
        if explicit_role:
            role = explicit_role
        else:
            # Map from layout_purpose if layout_role not present (backward compat)
            role = _map_purpose_to_role(l.get("layout_purpose", "GENERAL_CONTENT"))
        
        layout_summary.append({
            "layout_index": l["layout_index"],
            "layout_name": l["layout_name"],
            "slot_count": len(l.get("slots", [])),
            "description": l.get("description", ""),
            "purpose": l.get("layout_purpose", "GENERAL_CONTENT"),
            "role": role,
            "supports_background": l.get("supports_background_image", False),
            "density": l.get("density", "medium")
        })
    
    # Categorize by role for clearer guidance
    title_layouts = [l for l in layout_summary if l["role"] == ROLE_TITLE]
    agenda_layouts = [l for l in layout_summary if l["role"] == ROLE_AGENDA]
    content_layouts = [l for l in layout_summary if l["role"] == ROLE_CONTENT]
    diagram_layouts = [l for l in layout_summary if l["role"] == ROLE_DIAGRAM]
    timeline_layouts = [l for l in layout_summary if l["role"] == ROLE_TIMELINE]
    closing_layouts = [l for l in layout_summary if l["role"] == ROLE_CLOSING]
    
    # Fallback if no specific role layouts (use purpose-based)
    if not title_layouts:
        title_layouts = [l for l in layout_summary if "TITLE" in l["purpose"]]
    if not agenda_layouts:
        # Use content layouts for agenda if no dedicated agenda layout
        agenda_layouts = content_layouts[:1] if content_layouts else layout_summary[:1]
    
    prompt = f"""
You are the Lead Presentation Architect.
Your job: produce a slide plan that uses the RIGHT layout categories by slide index, and ensures strong title composition.

CONTENT SUMMARY:
{content_map}

MODE:
- NO_IMAGE = TRUE (text-only layouts ONLY)
- Convert diagrams/timelines into structured text (bullets/numbered phases/comparisons)
- NEVER request image placeholders

AVAILABLE LAYOUTS (only choose from these lists):

TITLE_LAYERS (Slide 1 ONLY):
{json.dumps(title_layouts, indent=2)}

AGENDA_LAYOUTS (Slide 2 ONLY):
{json.dumps(agenda_layouts, indent=2)}

CONTENT_LAYOUTS (Slides 3..N):
{json.dumps(content_layouts, indent=2)}

DIAGRAM_LAYOUTS (Slides 3..N):
{json.dumps(diagram_layouts, indent=2)}

TIMELINE_LAYOUTS (Slides 3..N):
{json.dumps(timeline_layouts, indent=2)}

CLOSING_LAYOUTS (Last slide optional):
{json.dumps(closing_layouts, indent=2)}

=========================
HARD CONSTRAINTS (MUST FOLLOW)
=========================

A) MANDATORY SLIDE ORDER
- Slide 1: ROLE = TITLE, layout MUST come from TITLE_LAYOUTS
- Slide 2: ROLE = AGENDA, layout MUST come from AGENDA_LAYOUTS
- Slides 3..(N-1): ROLE MUST be one of [CONTENT, DIAGRAM, TIMELINE]
- Last Slide (optional): ROLE = CLOSING, layout MUST come from CLOSING_LAYOUTS

B) HARD BLOCKS (STRICT)
- Slides 3..N MUST NOT use any layout from TITLE_LAYOUTS or AGENDA_LAYOUTS.
- If you select a layout for slides 3..N that exists in TITLE_LAYOUTS/AGENDA_LAYOUTS => your answer is INVALID.

C) TITLE SLIDE QUALITY (Slide 1)
- Title MUST be 4–9 words, max 2 lines.
- Subtitle MUST be <= 12 words (optional).
- Slide 1 MUST NOT contain bullets, long paragraphs, or instruction/spec text.
- Slide 1 intent: a single strong headline + subtitle only.
- Title should be "boardroom strong": concise, confident, centered.

D) CONTENT SLIDE MINIMUM FILL (Slides 3..N)
- Every slide from 3..N MUST include at least ONE of:
  - 3–6 bullets, OR
  - 2-column comparison (Pros/Cons, Now/Next), OR
  - 3-phase timeline bullets (Now/Next/Later)
- A slide with only a header is INVALID.

E) LAYOUT DIVERSITY
- Do NOT repeat the same layout_index more than 2 times overall.
- Avoid consecutive slides using the same layout_index.

F) SLIDE COUNT
- Total slides must be 5–8.

=========================
OUTPUT FORMAT (STRICT JSON)
=========================
Return a JSON array called "slides". Each slide object must include:
- slide_number (int)
- slide_role (TITLE/AGENDA/CONTENT/DIAGRAM/TIMELINE/CLOSING)
- layout_index (int)
- layout_name (string)
- slide_intent (string, 1 sentence)
- planned_content (object):
    - title (string)            # required for TITLE, optional otherwise
    - subtitle (string)         # optional
    - bullets (list of strings) # required for slides 3..N unless using timeline/comparison
    - timeline (dict)           # optional: {{ "Now":[..], "Next":[..], "Later":[..] }}
    - comparison (dict)         # optional: {{ "Left":[..], "Right":[..] }}

=========================
SELF-CHECK (YOU MUST DO THIS)
=========================
After generating the JSON, validate internally:
1) Slide 1 uses TITLE layout list
2) Slide 2 uses AGENDA layout list
3) Slides 3..N do NOT use TITLE/AGENDA layouts
4) Slides 3..N are NOT header-only (must have bullets/timeline/comparison)
If any rule fails, FIX your JSON before responding.

Now generate the slide plan JSON.
"""

    
    plan_response = _get_llm().invoke(prompt)
    print(f"--- Architect: Generated plan with {len(plan_response.slides)} slides ---")
    
    # Convert Pydantic models to TypedDict format with role enforcement
    slide_plans = []
    for idx, slide in enumerate(plan_response.slides):
        # Get slide_role from LLM or enforce based on position
        slide_role = getattr(slide, 'slide_role', None)
        
        # Force first two slides to be TITLE and AGENDA
        if idx == 0:
            slide_role = ROLE_TITLE
            # Ensure we use a title layout
            if title_layouts and slide.layout_index not in [l["layout_index"] for l in title_layouts]:
                slide.layout_index = title_layouts[0]["layout_index"]
                slide.layout_name = title_layouts[0]["layout_name"]
        elif idx == 1:
            slide_role = ROLE_AGENDA
            # Ensure we use an agenda layout (or content layout if no agenda)
            if agenda_layouts and slide.layout_index not in [l["layout_index"] for l in agenda_layouts]:
                slide.layout_index = agenda_layouts[0]["layout_index"]
                slide.layout_name = agenda_layouts[0]["layout_name"]
        elif not slide_role:
            # Infer role from layout if not provided
            matching_layout = next((l for l in layout_summary if l["layout_index"] == slide.layout_index), None)
            slide_role = matching_layout["role"] if matching_layout else ROLE_CONTENT
        
        slide_plans.append({
            "layout_index": slide.layout_index,
            "layout_name": slide.layout_name,
            "slide_intent": slide.slide_intent,
            "slide_role": slide_role
        })
    
    # Audit layout diversity
    layout_usage = {}
    for plan in slide_plans:
        idx = plan["layout_index"]
        layout_usage[idx] = layout_usage.get(idx, 0) + 1
    
    overused = {idx: count for idx, count in layout_usage.items() if count > 2}
    if overused:
        print(f"⚠️  Warning: Layouts used more than twice: {overused}")
    
    # Audit role enforcement
    if slide_plans:
        if slide_plans[0]["slide_role"] != ROLE_TITLE:
            print(f"⚠️  Warning: First slide role is {slide_plans[0]['slide_role']}, expected {ROLE_TITLE}")
        if len(slide_plans) > 1 and slide_plans[1]["slide_role"] != ROLE_AGENDA:
            print(f"⚠️  Warning: Second slide role is {slide_plans[1]['slide_role']}, expected {ROLE_AGENDA}")
    
    print(f"--- Architect: Roles assigned: {[p['slide_role'] for p in slide_plans]} ---")
    
    return {"slide_plans": slide_plans}