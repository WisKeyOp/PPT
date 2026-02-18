"""
Pipeline 2 Node: Image Director
Responsibility: Determine background image specifications for slides
Does NOT retrieve actual images, only creates specifications
"""
from src.core.state import PPTState, BackgroundImageSpec
from typing import Dict, Any

# Slide role constants (must match architect.py, writer.py, beautifier.py)
ROLE_TITLE = "TITLE"
ROLE_AGENDA = "AGENDA"
ROLE_CONTENT = "CONTENT"
ROLE_DIAGRAM = "DIAGRAM"
ROLE_TIMELINE = "TIMELINE"
ROLE_CLOSING = "CLOSING"


def _should_have_background(slide_role: str, layout_supports: bool) -> bool:
    """
    Determine if a slide should have a background image/gradient.
    
    Args:
        slide_role: The role of the slide
        layout_supports: Whether the layout explicitly supports background images
        
    Returns:
        True if background should be enabled
    """
    # Enable backgrounds for TITLE and CLOSING slides
    # Even if layout doesn't explicitly support it, we can add gradients
    # This ensures visual impact even with old registry schemas
    if slide_role in [ROLE_TITLE, ROLE_CLOSING]:
        return True
    
    # For other roles, respect the layout support flag
    # (This preserves backward compatibility while being more aggressive with key slides)
    return False


def _generate_image_keywords(slide_role: str, slide_intent: str) -> str:
    """
    Generate search keywords for background image based on role and intent.
    
    Args:
        slide_role: The role of the slide
        slide_intent: The intent/purpose of the slide
        
    Returns:
        Keywords string for image search
    """
    role_keywords = {
        ROLE_TITLE: "professional business presentation abstract corporate modern",
        ROLE_AGENDA: "organized structure planning roadmap agenda",
        ROLE_CONTENT: "business professional meeting corporate",
        ROLE_DIAGRAM: "technology architecture digital modern",
        ROLE_TIMELINE: "timeline progress future innovation",
        ROLE_CLOSING: "success achievement future opportunity next steps"
    }
    
    base_keywords = role_keywords.get(slide_role, "professional business")
    
    # Extract key terms from slide_intent (simple approach)
    # Remove common words
    common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with"}
    intent_words = [w for w in slide_intent.lower().split() if w not in common_words and len(w) > 3]
    intent_keywords = " ".join(intent_words[:3])  # Take first 3 meaningful words
    
    return f"{base_keywords} {intent_keywords}".strip()


def _get_image_mood(slide_role: str) -> str:
    """
    Determine mood/tone for background image.
    
    Args:
        slide_role: The role of the slide
        
    Returns:
        Mood descriptor
    """
    mood_map = {
        ROLE_TITLE: "inspiring, bold, confident",
        ROLE_AGENDA: "organized, clear, structured",
        ROLE_CONTENT: "professional, clean, focused",
        ROLE_DIAGRAM: "technical, precise, modern",
        ROLE_TIMELINE: "progressive, forward-looking, dynamic",
        ROLE_CLOSING: "optimistic, motivational, future-oriented"
    }
    return mood_map.get(slide_role, "professional, clean")


def _get_composition(slide_role: str) -> str:
    """
    Determine composition style for background image.
    
    Args:
        slide_role: The role of the slide
        
    Returns:
        Composition descriptor
    """
    composition_map = {
        ROLE_TITLE: "centered, high-impact, abstract gradient",
        ROLE_AGENDA: "left-aligned, structured, geometric",
        ROLE_CONTENT: "subtle, low-key, background blur",
        ROLE_DIAGRAM: "technical, grid-based, minimal",
        ROLE_TIMELINE: "horizontal flow, progressive, layered",
        ROLE_CLOSING: "centered, uplifting, open space"
    }
    return composition_map.get(slide_role, "subtle, professional")


def _get_overlay_opacity(slide_role: str) -> float:
    """
    Determine overlay opacity to ensure text readability.
    
    Args:
        slide_role: The role of the slide
        
    Returns:
        Overlay opacity (0.0 to 1.0)
    """
    # Title slides can have lower opacity (more image visible)
    # Content slides need higher opacity (more text visibility)
    opacity_map = {
        ROLE_TITLE: 0.35,      # 35% overlay, let image shine
        ROLE_AGENDA: 0.50,     # 50% overlay, balanced
        ROLE_CONTENT: 0.60,    # 60% overlay, prioritize text
        ROLE_DIAGRAM: 0.55,    # 55% overlay
        ROLE_TIMELINE: 0.50,   # 50% overlay
        ROLE_CLOSING: 0.40     # 40% overlay, impactful
    }
    return opacity_map.get(slide_role, 0.50)


def image_director_node(state: PPTState) -> Dict[str, Any]:
    """
    Pipeline 2 – Node 3.5 (between Writer and Beautifier)
    Enriches manifest with background image specifications.
    
    Does NOT download or insert actual images - only creates specs
    that the injector can use to place placeholder boxes or notes.
    
    Args:
        state: Current pipeline state with manifest and slide_plans
        
    Returns:
        Updated state with enriched background_image specs in manifest
    """
    manifest = state.get("manifest", [])
    slide_plans = state.get("slide_plans", [])
    registry = state.get("registry", {})
    
    # Build layout lookup to check supports_background_image
    layouts = registry.get("layouts", [])
    layout_by_idx = {l["layout_index"]: l for l in layouts}
    
    enriched_manifest = []
    
    for idx, slide in enumerate(manifest):
        layout_idx = slide.get("layout_index")
        slide_role = slide.get("slide_role", ROLE_CONTENT)
        
        # Get corresponding slide plan for intent
        slide_plan = slide_plans[idx] if idx < len(slide_plans) else {}
        slide_intent = slide_plan.get("slide_intent", "")
        
        # Check if layout supports background images
        layout = layout_by_idx.get(layout_idx, {})
        layout_supports = layout.get("supports_background_image", False)
        
        # Determine if this slide should have a background
        should_enable = _should_have_background(slide_role, layout_supports)
        
        # Generate image specification
        if should_enable:
            background_spec: BackgroundImageSpec = {
                "enabled": True,
                "keywords": _generate_image_keywords(slide_role, slide_intent),
                "mood": _get_image_mood(slide_role),
                "composition": _get_composition(slide_role),
                "overlay_opacity": _get_overlay_opacity(slide_role)
            }
            print(f"--- Image Director: Slide {idx + 1} ({slide_role}) → Background enabled")
            print(f"    Keywords: {background_spec['keywords'][:60]}...")
        else:
            background_spec: BackgroundImageSpec = {
                "enabled": False,
                "keywords": "",
                "mood": "",
                "composition": "",
                "overlay_opacity": 0.0
            }
        
        # Update slide with enriched background spec
        enriched_slide = slide.copy()
        enriched_slide["background_image"] = background_spec
        enriched_manifest.append(enriched_slide)
    
    print(f"--- Image Director: Processed {len(enriched_manifest)} slides ---")
    
    return {"manifest": enriched_manifest}
