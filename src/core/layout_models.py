from pydantic import BaseModel, Field, model_validator, field_validator
from typing import List, Literal, Optional

class Coordinates(BaseModel):
    x: int = Field(..., ge=0, le=1920, description="X coordinate (0-1920)")
    y: int = Field(..., ge=0, le=1080, description="Y coordinate (0-1080)")
    w: int = Field(..., gt=0, description="Width")
    h: int = Field(..., gt=0, description="Height")

    @model_validator(mode='after')
    def validate_bounds(self):
        # Safe Zone: 100 units margin
        SAFE_MARGIN = 100
        if self.x < SAFE_MARGIN:
             raise ValueError(f"Element x({self.x}) violates Safe Zone (left margin {SAFE_MARGIN})")
        if self.y < SAFE_MARGIN:
             raise ValueError(f"Element y({self.y}) violates Safe Zone (top margin {SAFE_MARGIN})")
        if self.x + self.w > 1920 - SAFE_MARGIN:
            raise ValueError(f"Element exceeds Safe Zone: x+w({self.x + self.w}) > {1920 - SAFE_MARGIN}")
        if self.y + self.h > 1080 - SAFE_MARGIN:
            raise ValueError(f"Element exceeds Safe Zone: y+h({self.y + self.h}) > {1080 - SAFE_MARGIN}")
        return self

class Styling(BaseModel):
    font_size: int = Field(..., ge=10, le=200, description="Font size in points (10-200)")
    font_weight: Literal["bold", "normal"] = Field(..., description="Font weight")
    alignment: Literal["left", "center", "right"] = Field(..., description="Text alignment")
    hex_color: str = Field(..., pattern=r"^#[0-9a-fA-F]{6}$", description="Font color in HEX format (e.g., #FFFFFF)")

class StrictSlot(BaseModel):
    slot_id: int = Field(..., description="Sequential integer ID starting from 1")
    role: Literal["HEADER", "SUB_HEADER", "BODY_COPY", "CALLOUT", "FOOTER", "TABLE", "CHART"]
    content_type: Literal["text", "image", "table", "chart"]
    coordinates: Coordinates
    styling: Styling
    max_chars: Optional[int] = Field(None, description="Max characters for text elements")
    data_schema: Optional[str] = Field(None, description="JSON schema or description for structure of data if role is TABLE or CHART")
    description: str = Field(..., description="Instruction for content generation")

    @model_validator(mode='after')
    def validate_content_requirements(self):
        if self.role in ["TABLE", "CHART"] and not self.data_schema:
            raise ValueError(f"Slot {self.slot_id} with role {self.role} must have a 'data_schema' defined.")
        return self

class StrictLayout(BaseModel):
    template_name: str
    total_slots: int
    canvas: dict = Field(default={"width": 1920, "height": 1080}, description="Canvas dimensions")
    slots: List[StrictSlot]

    @model_validator(mode='after')
    def validate_structure(self):
        # 1. Check sequential IDs
        sorted_slots = sorted(self.slots, key=lambda s: s.slot_id)
        ids = [s.slot_id for s in sorted_slots]
        if ids != list(range(1, len(ids) + 1)):
            raise ValueError(f"slot_ids must be sequential starting from 1. Got: {ids}")
        
        # 2. Spatial Constraint: Header must be in the top 25% (270px)
        header_found = False
        for slot in self.slots:
            if slot.role == "HEADER":
                header_found = True
                if slot.coordinates.y + slot.coordinates.h > 270: # Stricter: Encapsulate strictly or just start point? 
                                                                  # User said "y < 270" usually implies Top Y, but safer to check if it lives mostly up there. 
                                                                  # The prompt said "Title Must always reside in the top 25%... y < 270".
                                                                  # I will stick to slot.coordinates.y < 270.
                    if slot.coordinates.y >= 270:
                        raise ValueError(f"HEADER slot {slot.slot_id} must start in the top 25% (y < 270). Got y={slot.coordinates.y}")
        
        # 3. Collision Detection with Padding
        PADDING = 20
        for i, s1 in enumerate(self.slots):
            for s2 in self.slots[i+1:]:
                if self._check_overlap(s1.coordinates, s2.coordinates, padding=PADDING):
                    raise ValueError(f"Slot {s1.slot_id} is too close to Slot {s2.slot_id} (min padding {PADDING}px)")
                    
        return self

    def _check_overlap(self, c1: Coordinates, c2: Coordinates, padding: int = 0) -> bool:
        # Check if rectangles overlap OR are within padding distance
        # Effective rectangle = original + padding/2 on all sides? 
        # Simpler: Expand box 1 by padding and check intersection
        
        # Rect 1 with padding
        r1_x1 = c1.x - padding
        r1_y1 = c1.y - padding
        r1_x2 = c1.x + c1.w + padding
        r1_y2 = c1.y + c1.h + padding

        # Rect 2 (strict)
        r2_x1 = c2.x
        r2_y1 = c2.y
        r2_x2 = c2.x + c2.w
        r2_y2 = c2.y + c2.h

        if r1_x1 >= r2_x2 or r2_x1 >= r1_x2:
            return False
        if r1_y1 >= r2_y2 or r2_y1 >= r1_y2:
            return False
        return True
