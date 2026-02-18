from pydantic import BaseModel, Field, ConfigDict
from typing import List, Literal, Optional, Dict, Any

class GeometryMetadata(BaseModel):
    """Normalized geometry for semantic reasoning (not used for injection).
    
    Now includes shape-aware metadata for circular/oval shape support.
    """
    area_ratio: float = Field(description="Percentage of slide area (0.0-1.0)")
    norm_top: float = Field(description="Normalized top position (0.0-1.0)")
    norm_left: float = Field(description="Normalized left position (0.0-1.0)")
    norm_width: float = Field(description="Normalized width (0.0-1.0)")
    norm_height: float = Field(description="Normalized height (0.0-1.0)")
    
    # Shape-aware geometry fields
    shape_type: str = Field(default="rectangle", description="Shape category: rectangle, oval, other")
    is_circular: bool = Field(default=False, description="True if shape is circular/oval")
    radius: Optional[float] = Field(None, description="Normalized radius for circular shapes (0.0-1.0)")
    ellipse_axes: Optional[List[float]] = Field(
        default=None,
        min_length=2,
        max_length=2,
        description="Ellipse axes [rx, ry] in normalized units"
    )

class SlotSchema(BaseModel):
    model_config = ConfigDict(extra='allow')  # Allow geometry enrichment
    
    # === STABLE PLACEHOLDER IDENTITY (canonical PowerPoint binding) ===
    layout_index: int = Field(description="Layout this placeholder belongs to")
    placeholder_idx: int = Field(description="PowerPoint's placeholder_format.idx (canonical ID)")
    placeholder_type: str = Field(description="PowerPoint's placeholder type (TITLE, BODY, PICTURE, etc.)")
    placeholder_name: str = Field(description="PowerPoint's placeholder name (e.g., 'Title 1')")
    
    # === SEMANTIC FIELDS (for LLM output contract) ===
    semantic_role: str = Field(description="What content LLM should provide: title, bullets, body, image_query, footer")
    
    # === LEGACY FIELDS (backward compatibility, deprecated) ===
    slot_id: int = Field(description="[DEPRECATED] Use placeholder_idx instead")
    
    # === DESCRIPTIVE FIELDS (LLM-enriched) ===
    role_name: str = Field(description="Friendly name like 'Hero Title' or 'Feature List'")
    content_type: Literal["text", "image", "table"] = Field(description="The type of data this slot expects")
    max_chars: int = Field(description="Maximum characters allowed before layout breaks")
    description: str = Field(description="Instruction for the content-writer LLM in Pipeline 2")
    
    # === TEMPLATE INTELLIGENCE (extracted from PPTX) ===
    template_text: Optional[str] = Field(None, description="Instructional text from template (e.g., 'Click to add title')")
    template_formatting: Optional[Dict[str, Any]] = Field(None, description="Default formatting from template")
    
    # === CONSTRAINTS (derived from geometry + template) ===
    min_font_pt: Optional[int] = Field(None, description="Minimum readable font size")
    max_font_pt: Optional[int] = Field(None, description="Maximum font size")
    max_bullets: Optional[int] = Field(None, description="Maximum bullet points (for list placeholders)")
    max_chars_per_bullet: Optional[int] = Field(None, description="Maximum characters per bullet")
    overflow_policy: Optional[str] = Field("truncate", description="How to handle overflow: truncate, split_slide, ignore")
    content_priority: Optional[str] = Field("required", description="Priority level: required, optional, fallback")
    
    # === ENRICHED METADATA (existing fields) ===
    role_hint: Optional[str] = Field(None, description="Semantic role hint: title, body, footer, content")
    geometry: Optional[GeometryMetadata] = Field(None, description="Normalized spatial metadata for reasoning")
    
    @property
    def stable_key(self) -> str:
        """Generate stable identifier for this placeholder."""
        return f"{self.layout_index}:{self.placeholder_type}:{self.placeholder_idx}"

class LayoutMetadata(BaseModel):
    model_config = ConfigDict(extra='forbid')
    layout_index: int = Field(description="The index of this layout in the master file.")
    layout_name: str = Field(description="The name of the layout.")
    layout_purpose: str = Field(description="Category: TITLE_SLIDE, CONTENT_SLIDE, VISUAL_SLIDE, DATA_SLIDE, COMPARISON_SLIDE, GENERAL_CONTENT")
    description: str = Field(description="What this layout is best used for (e.g. Title Slide, Comparison).")
    slots: List[SlotSchema]
    
    # Enhanced metadata for improved layout selection (non-breaking additions)
    layout_role: Optional[str] = Field(None, description="Slide role: TITLE, AGENDA, CONTENT, DIAGRAM, TIMELINE, CLOSING")
    supports_background_image: bool = Field(False, description="Whether this layout supports background images")
    has_image_slot: bool = Field(False, description="Whether layout contains PICTURE/OBJECT placeholders (for NO_IMAGE filtering)")
    density: str = Field("medium", description="Content density: low, medium, high")
    
    # Professional narrative metadata (Phase G)
    narrative_category: Optional[str] = Field(None, description="Narrative purpose: opening, agenda, section_break, content, visual, closing")
    recommended_position: Optional[str] = Field(None, description="Recommended placement: first, early, middle, late, last")
    visual_weight: Optional[str] = Field("medium", description="Layout complexity: light, medium, heavy (based on slot count and density)")

class MasterRegistry(BaseModel):
    model_config = ConfigDict(extra='forbid')
    master_name: str
    layouts: List[LayoutMetadata]