# State definition for LangGraph
from typing import TypedDict, List, Optional, Any, Dict
from pydantic import BaseModel, Field

class Pipeline1State(TypedDict):
    """
    The 'Shared Memory' for Pipeline 1 (Indexing).
    Every node in the graph can read from and write to this dictionary.
    """
    # --- Inputs ---
    template_path: str          # Path to the .pptx file we are analyzing
    
    # --- Internal Data ---
    raw_shape_data: List[dict]   # List of IDs, names, and sizes from parser.py
    
    # --- Outputs ---
    json_description: Optional[dict]  # The final structured JSON from registry_builder.py
    
    # --- Control Flags ---
    is_valid: bool              # Flag to indicate if the JSON passed validation
    feedback: Optional[str]     # Stores human input for the feedback loop


class SlidePlan(TypedDict):
    """
    Intermediate plan from Architect, containing layout choice and intent.
    """
    layout_index: int
    layout_name: str
    slide_intent: str
    slide_role: str  # TITLE, AGENDA, CONTENT, DIAGRAM, TIMELINE, CLOSING

class SlidePlanModel(BaseModel):
    """Pydantic model for structured LLM output in architect."""
    layout_index: int = Field(description="Index of the layout to use")
    layout_name: str = Field(description="Name of the layout")
    slide_intent: str = Field(description="Purpose and key message of this slide")
    slide_role: str = Field(description="Slide role: TITLE, AGENDA, CONTENT, DIAGRAM, TIMELINE, CLOSING")

class ArchitecturePlan(BaseModel):
    """Wrapper for LLM-generated slide plan."""
    slides: List[SlidePlanModel] = Field(description="List of slides in the presentation")

class BackgroundImageSpec(TypedDict, total=False):
    """Background image specification for a slide."""
    enabled: bool
    keywords: str
    mood: str
    composition: str
    overlay_opacity: float  # 0.0 to 1.0

class ManifestEntry(TypedDict):
    """
    Single slide instruction in the presentation manifest.
    Strictly decouples logic from file paths.
    """
    layout_index: int           # Index of the layout in the master template
    content: Dict[str, Any]     # Content to populate (role/placeholder_name -> value)
    slide_role: str             # TITLE, AGENDA, CONTENT, DIAGRAM, TIMELINE, CLOSING
    background_image: BackgroundImageSpec  # Image specification (optional)
    # Note: No file paths here.


class PPTState(TypedDict):
    """
    The 'Shared Memory' for Pipeline 2 - Generation.
    Manages the entire presentation generation workflow.
    """
    # --- Discovery Data ---
    primary_master_path: str        # Path to the SINGLE master file
    registry: Dict[str, Any]        # The loaded JSON registry for the master

    # --- Pipeline 2 Data ---
    raw_docs: str                   # Input text from user
    content_map: Optional[str]      # AI-structured summary of raw_docs
    
    # --- Generation Stage ---
    # The architect produces a plan, the writer fills the content.
    slide_plans: List[SlidePlan]    # Output of Architect
    manifest: List[ManifestEntry]   # Output of Writer, ready for Injector
    
    # --- Persistence ---
    thread_id: Optional[str]
    current_step: Optional[str]
    
    # --- Output ---
    final_file_path: Optional[str] # Path to generated .pptx
    
    # --- Control Flags ---
    validation_errors: List[str]   # Track any issues