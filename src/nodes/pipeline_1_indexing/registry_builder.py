"""
Pipeline 1 Node: Generator
Creates structured metadata (layout_map.json) for templates using LLM.
"""

from src.core.state import Pipeline1State
from src.nodes.pipeline_1_indexing.layout_validator import (
    MasterRegistry, 
    LayoutMetadata, 
    SlotSchema,
    GeometryMetadata
)
from pydantic import BaseModel
from typing import List
import os

from src.utils.auth_helper import get_llm

# Lazy LLM initialization
_llm_instance = None

def _get_layout_analyzer():
    """Lazy load LLM instance."""
    global _llm_instance
    if _llm_instance is None:
        llm_base = get_llm(deployment_name="gpt-4", temperature=0)
        _llm_instance = llm_base.with_structured_output(LayoutMetadata, method="function_calling")
    return _llm_instance

def derive_role_hint(shape: dict) -> str:
    """
    Deterministic logic to assign semantic role_hint based on normalized geometry.
    NO LLM - Pure Python logic for consistency.
    """
    norm_top = shape.get('norm_top', 0)
    norm_height = shape.get('norm_height', 0)
    area_ratio = shape.get('area_ratio', 0)
    
    # Rule 1: Top region with small height = Title
    if norm_top < 0.2 and norm_height < 0.2:
        return "title"
    
    # Rule 2: Bottom region = Footer
    if norm_top > 0.8:
        return "footer"
    
    # Rule 3: Large area = Body/Main Content
    if area_ratio > 0.3:
        return "body"
    
    # Rule 4: Medium area in middle = Content block
    if 0.2 <= norm_top <= 0.8 and area_ratio > 0.1:
        return "content"
    
    # Default: Generic content
    return "content"

def build_registry_node(state: Pipeline1State):
    """
    Analyzes raw shape data for ALL layouts and generates enriched registry with:
    - Normalized geometry (for Writer reasoning)
    - Semantic role_hints (for content quality)
    """
    layouts_data = state['raw_shape_data'] # List of dicts {index, name, shapes}
    template_path = state['template_path']
    template_name = os.path.basename(template_path)
    
    analyzed_layouts = []
    
    print(f"--- Registry Builder: Analyzing {len(layouts_data)} layouts in {template_name} ---")
    
    for layout_raw in layouts_data:
        idx = layout_raw['index']
        name = layout_raw['name']
        shapes = layout_raw['shapes']
        
        # Skip layouts with no useful placeholders (optional optimization)
        if not shapes:
            continue
        
        # Enrich shapes with role_hint BEFORE sending to LLM
        enriched_shapes = []
        for shape in shapes:
            enriched_shape = shape.copy()
            enriched_shape['role_hint'] = derive_role_hint(shape)
            enriched_shapes.append(enriched_shape)
        
        # Analyze slot composition for better descriptions
        slot_count = len(enriched_shapes)
        title_slots = sum(1 for s in enriched_shapes if s['role_hint'] == 'title')
        body_slots = sum(1 for s in enriched_shapes if s['role_hint'] == 'body')
        content_slots = sum(1 for s in enriched_shapes if s['role_hint'] == 'content')
        image_slots = sum(1 for s in enriched_shapes if 'Picture' in s.get('name', ''))
        
        # Identify layout patterns and spatial characteristics
        has_columns = content_slots >= 2
        has_image = image_slots > 0
        layout_type = "multi-column" if has_columns else "single-area" if body_slots > 0 else "title-focused"
        
        # Detect layout purpose based on composition
        has_large_title = any(s.get('area_ratio', 0) > 0.05 and s['role_hint'] == 'title' for s in enriched_shapes)
        has_only_title = title_slots >= 1 and body_slots == 0 and content_slots <= 1
        
        if has_only_title and has_large_title:
            layout_purpose = "TITLE_SLIDE"
        elif image_slots > 0:
            layout_purpose = "VISUAL_SLIDE"
        elif has_columns and content_slots >= 2:
            layout_purpose = "COMPARISON_SLIDE"
        elif body_slots >= 1:
            layout_purpose = "CONTENT_SLIDE"
        else:
            layout_purpose = "GENERAL_CONTENT"
            
        # === BUILD SLOTS DIRECTLY FROM PLACEHOLDER DATA (more reliable than LLM) ===
        slots = []
        for i, shape in enumerate(enriched_shapes):
            # Infer semantic role from placeholder type and template text
            template_text = shape.get('template_text', '') or ''
            template_text_lower = template_text.lower()
            ppt_type = shape['type']  # e.g., "TITLE (1)", "BODY (2)", "PICTURE (18)"
            
            if 'TITLE' in ppt_type or 'CENTER_TITLE' in ppt_type:
                semantic_role = "title"
                role_name = "Title"
                max_chars = 100
            elif 'BODY' in ppt_type or 'OBJECT' in ppt_type or 'Content' in shape['name']:
                # Distinguish bullets from body text
                if any(kw in template_text_lower for kw in ['bullet', 'point', 'list', 'agenda', 'items']):
                    semantic_role = "bullets"
                    role_name = "Bullet List"
                    max_chars = 500
                else:
                    semantic_role = "body"
                    role_name = "Content"
                    max_chars = 500
            elif 'PICTURE' in ppt_type or 'MEDIA' in ppt_type or 'CHART' in ppt_type:
                semantic_role = "image_query"
                role_name = "Image"
                max_chars = 100
            elif 'Footer' in shape['name'] or 'Date' in shape['name']:
                semantic_role = "footer"
                role_name = shape['name']
                max_chars = 50
            else:
                semantic_role = "body"  # Default to body instead of generic "content"
                role_name = shape['name']
                max_chars = 200
            
            # Create slot with stable identity
            slot = SlotSchema(
                layout_index=idx,
                placeholder_idx=shape['idx'],
                placeholder_type=shape['type'],
                placeholder_name=shape['name'],
                semantic_role=semantic_role,
                slot_id=shape['idx'],  # Legacy compatibility
                role_name=role_name,
                content_type="image" if semantic_role == "image_query" else "text",
                max_chars=max_chars,
                description=f"{role_name} placeholder",
                template_text=shape.get('template_text'),
                template_formatting={
                    "default_font_size_pt": shape.get('default_font_size_pt'),
                    "default_font_name": shape.get('default_font_name'),
                    "default_alignment": shape.get('default_alignment'),
                    "is_bold": shape.get('is_bold'),
                    "is_italic": shape.get('is_italic'),
                    "word_wrap": shape.get('word_wrap', True),
                    "auto_size": shape.get('auto_size'),
                    "line_spacing": shape.get('line_spacing')
                },
                role_hint=shape['role_hint'],
                content_priority="optional" if semantic_role == "footer" else "required"
            )
            
            # Calculate font constraints
            default_font = shape.get('default_font_size_pt')
            if default_font:
                slot.min_font_pt = max(8, int(default_font * 0.65))
                slot.max_font_pt = int(default_font * 1.15)
            else:
                if semantic_role == "title":
                    slot.min_font_pt = 28
                    slot.max_font_pt = 50
                elif semantic_role in ["bullets", "body"]:
                    slot.min_font_pt = 14
                    slot.max_font_pt = 24
                else:
                    slot.min_font_pt = 10
                    slot.max_font_pt = 20
            
            # Calculate max_bullets from placeholder height
            height_emu = shape.get('height', 0)
            if semantic_role == "bullets" and height_emu and default_font:
                line_height_emu = default_font * 12700 * 1.5
                usable_height = height_emu * 0.7
                slot.max_bullets = max(3, min(10, int(usable_height / line_height_emu)))
            elif semantic_role == "bullets":
                slot.max_bullets = 5
            
            # Calculate max_chars_per_bullet from width
            width_emu = shape.get('width', 0)
            if semantic_role == "bullets" and width_emu and default_font:
                avg_char_width_emu = default_font * 12700 * 0.6
                chars_per_line = int(width_emu * 0.85 / avg_char_width_emu)
                slot.max_chars_per_bullet = max(60, min(150, chars_per_line))
            elif semantic_role == "bullets":
                slot.max_chars_per_bullet = 100
            
            # Set overflow policy
            slot.overflow_policy = "split_slide" if semantic_role == "bullets" else "shrink"
            
            # Add geometry
            slot.geometry = GeometryMetadata(
                area_ratio=shape['area_ratio'],
                norm_top=shape['norm_top'],
                norm_left=shape['norm_left'],
                norm_width=shape['norm_width'],
                norm_height=shape['norm_height'],
                shape_type=shape.get('shape_type', 'rectangle'),
                is_circular=shape.get('is_circular', False),
                radius=shape.get('radius'),
                ellipse_axes=shape.get('ellipse_axes')
            )
            
            slots.append(slot)
        
        # CRITICAL: Detect if layout has image placeholders (for NO_IMAGE filtering)
        has_image_slot = any(
            'PICTURE' in slot.placeholder_type or
            'OBJECT' in slot.placeholder_type or
            'MEDIA' in slot.placeholder_type or
            slot.semantic_role == 'image_query'
            for slot in slots
        )
        
        # Generate simple layout description (fast, no LLM calls)
        # For AI-enhanced descriptions, integrate LLM generation here
        description = f"{layout_purpose.replace('_', ' ').title()} layout with {slot_count} placeholders"
        
        # Create LayoutMetadata with pre-built slots
        try:
            metadata = LayoutMetadata(
                layout_index=idx,
                layout_name=name,
                layout_purpose=layout_purpose,
                description=description,
                slots=slots,
                layout_role=None,  # Will be inferred by architect
                supports_background_image=False,
                has_image_slot=has_image_slot,  # NEW: For NO_IMAGE filtering
                density="low" if slot_count <= 2 else "high" if slot_count >= 5 else "medium"
            )
            
            # Slots are already fully enriched above, just append the layout
            analyzed_layouts.append(metadata)
            print(f"  Indexed layout {idx}: {name}")
        except Exception as e:
            print(f"  Failed to analyze layout {idx}: {e}")
            
    registry = MasterRegistry(master_name=template_name, layouts=analyzed_layouts)
    
    return {"json_description": registry.model_dump()}
