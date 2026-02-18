"""
Pipeline 2 Node: Beautifier
Responsibility: Convert raw text into fully-specified style instructions
This node creates an Intermediate Representation (IR) - it does NOT touch PPTX

Now includes role-aware styling for improved presentation quality.
"""
import math
from typing import List, Dict, Any, Optional
from src.core.state import PPTState
from src.config import FORCE_FONT_SIZE_LAYOUTS

# Slide role constants (must match architect.py and writer.py)
ROLE_TITLE = "TITLE"
ROLE_AGENDA = "AGENDA"
ROLE_CONTENT = "CONTENT"
ROLE_DIAGRAM = "DIAGRAM"
ROLE_TIMELINE = "TIMELINE"
ROLE_CLOSING = "CLOSING"

# --- Font Size Policies (role-based with geometry awareness) ---
# Title slide sizes (larger, more impact)
FONT_SIZE_TITLE_SLIDE_MAIN = 44
FONT_SIZE_TITLE_SLIDE_SUBTITLE = 28
FONT_SIZE_TITLE_SLIDE_FOOTER = 11

# Standard slide sizes
FONT_SIZE_TITLE_LARGE = 32    # area_ratio > 0.05
FONT_SIZE_TITLE_SMALL = 28
FONT_SIZE_BODY_LARGE = 22     # area_ratio > 0.3
FONT_SIZE_BODY_DEFAULT = 18
FONT_SIZE_CONTENT_LARGE = 16  # area_ratio > 0.15
FONT_SIZE_CONTENT_DEFAULT = 14
FONT_SIZE_FOOTER = 10
FONT_SIZE_FALLBACK = 16

# --- Geometry Thresholds ---
AREA_THRESHOLD_TITLE = 0.05
AREA_THRESHOLD_BODY = 0.3
AREA_THRESHOLD_CONTENT = 0.15

# --- Circular Text Fitting Constants ---
TEXT_PADDING_RATIO = 0.1      # 10% padding inside circular shapes
FONT_SIZE_RANGE = (8, 72)     # Min/max font sizes for binary search
FIT_PRECISION = 0.5           # Binary search stops within 0.5pt
CHAR_WIDTH_RATIO = 0.6        # Average char width as ratio of font_size
BOLD_WIDTH_MULTIPLIER = 1.1   # Bold text is ~10% wider
LINE_HEIGHT_RATIO = 1.2       # Line height as ratio of font_size

# --- Markdown Tokens ---
MD_BOLD = "**"
MD_ITALIC = "*"


def _is_boundary(text: str, idx: int) -> bool:
    """
    Return True if idx is at a non-alphanumeric boundary (or start/end).
    Prevents emphasis markers from activating inside words (e.g., fi*sh*ing).
    """
    if idx <= 0 or idx >= len(text):
        return True
    return not (text[idx - 1].isalnum() and text[idx].isalnum())


def parse_markdown(text: str) -> List[Dict[str, Any]]:
    r"""
    Converts markdown emphasis into styled runs with robust handling.
    
    Supports:
    - **bold** → bold text
    - *italic* → italic text
    - Escaped markers: \* and \** → literal asterisks
    - Ignores markers inside words (fi*sh*ing → plain text)
    - Treats unbalanced markers as plain text
    
    Args:
        text: Input text with markdown formatting (or None)
        
    Returns:
        List of run specifications with bold/italic flags
    """
    if text is None:
        return [{"text": "", "bold": False, "italic": False}]
    
    s = str(text)
    
    # Handle empty string edge case
    if not s:
        return [{"text": "", "bold": False, "italic": False}]
    
    runs: List[Dict[str, Any]] = []
    bold_on = False
    italic_on = False
    buf: List[str] = []
    i = 0
    n = len(s)
    
    def flush():
        """Flush current buffer to runs list"""
        if not buf:
            return
        runs.append({
            "text": "".join(buf),
            "bold": bold_on,
            "italic": italic_on
        })
        buf.clear()
    
    while i < n:
        ch = s[i]
        
        # Handle escape sequences
        if ch == "\\" and i + 1 < n:
            buf.append(s[i + 1])
            i += 2
            continue
        
        # Try to match bold marker
        if s.startswith(MD_BOLD, i):
            # Check boundaries to avoid toggling inside words
            left_ok = _is_boundary(s, i)
            right_ok = _is_boundary(s, i + len(MD_BOLD))
            if left_ok and right_ok:
                flush()
                bold_on = not bold_on
                i += len(MD_BOLD)
                continue
        
        # Try to match italic marker
        if ch == MD_ITALIC:
            left_ok = _is_boundary(s, i)
            right_ok = _is_boundary(s, i + 1)
            if left_ok and right_ok:
                flush()
                italic_on = not italic_on
                i += 1
                continue
        
        # Default: append literal character
        buf.append(ch)
        i += 1
    
    # Flush remaining buffer
    flush()
    
    # If we ended with unbalanced markers (bold_on/italic_on True),
    # merge all runs back to plain text to avoid partial styling
    if bold_on or italic_on:
        literal = "".join(r["text"] for r in runs)
        return [{"text": literal, "bold": False, "italic": False}]
    
    # If no runs were created (shouldn't happen with checks above), return empty run
    if not runs:
        return [{"text": "", "bold": False, "italic": False}]
    
    return runs


def _safe_int(val: Any) -> Optional[int]:
    """
    Safely convert value to int, returning None on failure.
    Prevents crashes from non-numeric slot IDs.
    """
    try:
        return int(val)
    except (TypeError, ValueError):
        return None


def _calculate_chord_width(y_offset: float, radius: float, center_y: float = 0.0) -> float:
    """
    Calculate available text width at a given vertical position within a circle.
    
    Uses chord-width formula: W(y) = 2 * sqrt(r² - (y - center_y)²)
    
    Args:
        y_offset: Vertical position relative to circle center (-radius to +radius)
        radius: Circle radius (normalized, 0.0-1.0)
        center_y: Y-coordinate of circle center (default 0 for centered)
        
    Returns:
        Available width at this y-position (0.0 if outside circle)
    """
    if radius <= 0:
        return 0.0
    
    # Distance from center
    dy = abs(y_offset - center_y)
    
    # Outside circle
    if dy >= radius:
        return 0.0
    
    # Chord width formula
    width = 2.0 * math.sqrt(radius * radius - dy * dy)
    return max(0.0, width)


def _estimate_text_dimensions(text: str, font_size: int, runs: List[Dict[str, Any]]) -> tuple:
    """
    Estimate text width and height using character-count heuristics.
    
    This is a conservative approximation; actual rendering may differ.
    Binary search compensates for estimation errors.
    
    Args:
        text: Full text content
        font_size: Font size in points
        runs: Styled runs (for bold detection)
        
    Returns:
        (estimated_width, estimated_height) in normalized units
    """
    if not text or font_size <= 0:
        return (0.0, 0.0)
    
    # Convert font size to approximate normalized width
    # Assumption: ~0.6 char width per pt, slide width ~10 inches (960pt @ 96dpi)
    # Normalized: divide by slide dimension
    char_width = (font_size * CHAR_WIDTH_RATIO) / 960.0  # Rough normalization
    
    # Account for bold runs (wider characters)
    total_width = 0.0
    for run in runs:
        text_len = len(run.get("text", ""))
        multiplier = BOLD_WIDTH_MULTIPLIER if run.get("bold", False) else 1.0
        total_width += text_len * char_width * multiplier
    
    # Estimate height (one line for now; will be recalculated during wrapping)
    line_height = (font_size * LINE_HEIGHT_RATIO) / 720.0  # Normalized
    
    return (total_width, line_height)


def _fit_text_in_circle(text: str, runs: List[Dict[str, Any]], radius: float, padding_ratio: float = TEXT_PADDING_RATIO) -> int:
    """
    Binary search for largest font size that fits text inside a circle.
    
    Uses chord-width constraints at each line's vertical position.
    
    Args:
        text: Full text content
        runs: Styled runs from markdown parsing
        radius: Circle radius (normalized 0.0-1.0)
        padding_ratio: Padding as ratio of radius
        
    Returns:
        Font size in points that fits, or minimum if none fit
    """
    if not text or radius <= 0:
        return FONT_SIZE_RANGE[0]
    
    # Apply padding
    effective_radius = radius * (1.0 - padding_ratio)
    if effective_radius <= 0:
        print(f"⚠️  [Beautifier Warning] Padding exceeds radius, using minimum font")
        return FONT_SIZE_RANGE[0]
    
    min_font, max_font = FONT_SIZE_RANGE
    best_fit = min_font
    
    # Binary search for optimal font size
    while max_font - min_font > FIT_PRECISION:
        mid_font = (min_font + max_font) / 2.0
        
        # Estimate line height
        line_height = (mid_font * LINE_HEIGHT_RATIO) / 720.0
        
        # Simple word wrapping with chord-width constraints
        words = text.split()
        lines = []
        current_line = []
        current_y = -effective_radius  # Start at top of circle
        
        fits = True
        for word in words:
            # Estimate word width
            word_width = (len(word) + 1) * (mid_font * CHAR_WIDTH_RATIO) / 960.0  # +1 for space
            
            # Check if word fits on current line at current y-position
            available_width = _calculate_chord_width(current_y + line_height/2, effective_radius)
            
            # Start new line if word doesn't fit
            if current_line and sum(len(w) + 1 for w in current_line) * (mid_font * CHAR_WIDTH_RATIO) / 960.0 > available_width:
                lines.append(" ".join(current_line))
                current_line = [word]
                current_y += line_height
                
                # Check if we've exceeded circle height
                if current_y + line_height > effective_radius:
                    fits = False
                    break
            else:
                current_line.append(word)
        
        # Add final line
        if current_line and fits:
            lines.append(" ".join(current_line))
            current_y += line_height
            if current_y > effective_radius:
                fits = False
        
        # Update binary search bounds
        if fits:
            best_fit = mid_font
            min_font = mid_font
        else:
            max_font = mid_font
    
    return int(best_fit)


def _determine_font_size(role_hint: str, area_ratio: float, slide_role: str = ROLE_CONTENT) -> int:
    """
    Calculate font size based on slot role, geometry, and slide role.
    Matches ppt_helper.py pattern for consistency.
    
    Args:
        role_hint: Slot role (title, body, content, footer, etc.)
        area_ratio: Percentage of slide area (0.0-1.0)
        slide_role: Slide-level role (TITLE, AGENDA, CONTENT, etc.)
        
    Returns:
        Font size in points
    """
    role = (role_hint or "").lower()
    
    # Title slides get special treatment (larger, more impactful)
    if slide_role == ROLE_TITLE:
        if "title" in role or "header" in role or "headline" in role:
            return FONT_SIZE_TITLE_SLIDE_MAIN
        elif "subtitle" in role or "body" in role:
            return FONT_SIZE_TITLE_SLIDE_SUBTITLE
        elif "footer" in role:
            return FONT_SIZE_TITLE_SLIDE_FOOTER
        else:
            return FONT_SIZE_TITLE_LARGE
    
    # Standard role-based sizing for other slides
    if "title" in role or "header" in role or "headline" in role:
        return FONT_SIZE_TITLE_LARGE if area_ratio > AREA_THRESHOLD_TITLE else FONT_SIZE_TITLE_SMALL
    elif "body" in role:
        return FONT_SIZE_BODY_LARGE if area_ratio > AREA_THRESHOLD_BODY else FONT_SIZE_BODY_DEFAULT
    elif "content" in role:
        return FONT_SIZE_CONTENT_LARGE if area_ratio > AREA_THRESHOLD_CONTENT else FONT_SIZE_CONTENT_DEFAULT
    elif "footer" in role:
        return FONT_SIZE_FOOTER
    else:
        return FONT_SIZE_FALLBACK


def _alignment_for_role(role_hint: str = None, semantic_role: str = None, slide_role: str = None) -> Optional[str]:
    """
    Map role hints to text alignment with semantic and slide role awareness.
    Supports CENTER, RIGHT, LEFT, or None (to respect Master Slide defaults).
    
    Args:
        role_hint: Slot role metadata (legacy)
        semantic_role: Semantic field name (title, bullets, body, etc.)
        slide_role: Slide-level role (TITLE, AGENDA, CONTENT, etc.)
        
    Returns:
        Alignment string ("CENTER", "RIGHT", "LEFT") or None to preserve template defaults
    """
    # Title slides and title fields ALWAYS centered
    if slide_role == ROLE_TITLE or semantic_role == 'title':
        return "CENTER"
    
    # Legacy role_hint check (backward compatibility)
    role = (role_hint or "").lower()
    
    # Center alignment for titles, headers, captions
    if any(key in role for key in ("title", "header", "headline", "section-title", 
                                     "tagline", "caption", "quote", "center")):
        return "CENTER"
    
    # Right alignment for numbers and metrics
    if any(key in role for key in ("number", "value", "metric", "right")):
        return "RIGHT"
    
    # Default to None: let Master Slide template decide alignment
    return None


def _beautify_semantic_content(
    semantic_content: dict,
    layout: dict,
    slide_role: str,
    slide_idx: int,
    semantic_mapping: dict
) -> dict:
    """
    Convert semantic content (title, bullets, body) into styled-run format.
    
    This replaces the semantic bypass to ensure markdown is parsed and content is styled.
    
    Args:
        semantic_content: Dict with semantic keys (title, bullets, body, footer)
        layout: Layout metadata from registry
        slide_role: Slide role (TITLE, AGENDA, CONTENT, etc.)
        slide_idx: Slide index for logging
        semantic_mapping: Slot metadata by semantic role
        
    Returns:
        Dict in slot_id format with styled runs (same as legacy path output)
    """
    styled_content = {}
    
    for semantic_role, raw_content in semantic_content.items():
        if semantic_role.startswith('_'):  # Skip metadata fields
            continue
        
        # CRITICAL: Skip image_query entirely (NO_IMAGE mode)
        if semantic_role == 'image_query':
            print(f"  ⊘ Skipping image_query (NO_IMAGE mode)")
            continue
        
        # Find slot metadata for this semantic role
        slots = semantic_mapping.get(semantic_role, [])
        if not slots:
            continue
        
        slot = slots[0]  # Use first matching slot
        slot_id = slot.get('slot_id')
        
        # DEFENSIVE: Skip slots with invalid/missing slot_id (prevents downstream int(None) errors)
        if slot_id is None:
            print(f"  ⊘ Skipped semantic field '{semantic_role}': slot has no slot_id")
            continue
        
        geometry = slot.get('geometry', {})
        role_hint = slot.get('role_hint', semantic_role)
        
        # Determine font size based on layout policy
        # Only enforce font size for specific layouts (e.g., KPI tiles)
        # Otherwise let PPT autosize/autofit handle it
        layout_name = layout.get('layout_name', '')
        if layout_name in FORCE_FONT_SIZE_LAYOUTS:
            area_ratio = geometry.get('area_ratio', 0.1)
            font_size = _determine_font_size(
                role_hint=role_hint,
                area_ratio=area_ratio,
                slide_role=slide_role
            )
        else:
            font_size = None  # Let PPT autosize/autofit work
        
        # Determine alignment with semantic awareness
        alignment = _alignment_for_role(
            role_hint=role_hint,
            semantic_role=semantic_role,
            slide_role=slide_role
        )
        
        # Parse markdown and build styled runs based on content type
        if semantic_role == 'bullets' and isinstance(raw_content, list):
            # Bullets: Create list of bullet items, each with its own runs
            # This allows injector to create ONE PARAGRAPH PER BULLET
            bullet_items = []
            for bullet_text in raw_content:
                runs = parse_markdown(str(bullet_text))
                bullet_items.append({"runs": runs})
            
            styled_content[str(slot_id)] = {
                "bullets": bullet_items,  # List structure, not "\n"-separated
                "font_size": font_size,
                "alignment": alignment,
                "semantic_role": semantic_role
            }
        else:
            # Single text field (title, body, footer)
            runs = parse_markdown(str(raw_content))
            
            styled_content[str(slot_id)] = {
                "runs": runs,
                "font_size": font_size,
                "alignment": alignment,
                "semantic_role": semantic_role
            }
        
        # Add vertical anchor for title slides
        if slide_role == ROLE_TITLE and semantic_role == 'title':
            styled_content[str(slot_id)]["vertical_anchor"] = "MIDDLE"
    
    return styled_content


def beautifier_node(state: PPTState) -> Dict[str, Any]:
    """
    Pipeline 2 – Node 4
    Converts text manifest into deterministic style instructions.
    
    This is the "contract enforcement boundary" between LLM imagination
    and physical document reality. It handles:
    - Markdown parsing (bold & italic with escape support and proper spacing)
    - Geometry-aware font sizing (role_hint + area_ratio + slide_role)
    - Alignment based on role semantics
    - Soft failure for hallucinated layout indices
    - Content validation against max_chars
    - Null safety for robustness
    - Role-aware styling (TITLE slides get larger fonts, etc.)
    
    Returns:
        Updated state with beautified manifest containing style specs
    """
    # Validate inputs
    if "manifest" not in state or "registry" not in state:
        raise ValueError("State must contain 'manifest' and 'registry' keys.")
    
    manifest = state["manifest"]
    registry = state["registry"]
    
    # Get default fallback layout (first in registry)
    layouts = registry.get("layouts", [])
    if not layouts:
        raise ValueError("Registry contains no layouts - cannot beautify")
    
    default_layout = layouts[0]
    beautified = []
    
    # Build layout lookup for performance (O(1) access)
    layout_by_idx = {l["layout_index"]: l for l in layouts}
    
    for slide_idx, slide in enumerate(manifest):
        layout_idx = slide.get("layout_index")
        slide_role = slide.get("slide_role", ROLE_CONTENT)  # Get slide role from manifest
        
        # Find layout with soft failure handling
        layout = layout_by_idx.get(layout_idx)
        
        if layout is None:
            # Soft failure: fallback + audit trail
            print(
                f"⚠️  [Beautifier Warning] Unknown layout_index {layout_idx}. "
                f"Falling back to layout_index {default_layout['layout_index']} "
                f"({default_layout.get('layout_name', 'unknown')})."
            )
            layout = default_layout
            layout_idx = default_layout["layout_index"]
        
        styled_content = {}
        
        # Handle missing/invalid content dict
        slide_content = slide.get("content", {}) or {}
        if not isinstance(slide_content, dict):
            print(f"⚠️  [Beautifier Warning] Slide {slide_idx} content is not a dict. Coercing to empty.")
            slide_content = {}
        
        # Check if content is semantic (new approach) or slot_id-based (legacy)
        is_semantic = any(key in slide_content for key in ['title', 'bullets', 'body', 'image_query', 'footer'])
        
        if is_semantic:
            # SEMANTIC CONTENT: Apply styling (NO LONGER BYPASSING)
            print(f"  → Slide {slide_idx + 1} using semantic mapping (with styled-run conversion)")
            
            # Convert semantic content to styled runs
            styled_content = _beautify_semantic_content(
                semantic_content=slide_content,
                layout=layout,
                slide_role=slide_role,
                slide_idx=slide_idx,
                semantic_mapping=slide.get("_semantic_mapping", {})
            )
            
            beautified.append({
                "layout_index": layout_idx,
                "content": styled_content,  # Now contains styled runs, not raw semantic
                "slide_role": slide_role,
                "background_image": slide.get("background_image", {}),
                "_is_semantic": True  # Flag for injector to know this came from semantic path
            })
            continue  # Skip to next slide
        
        # LEGACY SLOT_ID-BASED CONTENT: Apply styling as before
        # Build slot metadata lookup for performance (O(1) access)
        slots_meta = layout.get("slots", []) or []
        slot_meta_by_id = {}
        for sm in slots_meta:
            sid = _safe_int(sm.get("slot_id"))
            if sid is not None:
                slot_meta_by_id[sid] = sm
        
        for slot_key, raw_text in slide_content.items():
            # Normalize slot key to int for metadata lookup
            slot_id_int = _safe_int(slot_key)
            slot_meta = slot_meta_by_id.get(slot_id_int)
            
            # Handle None text (convert to empty string, not "None")
            text_str = "" if raw_text is None else str(raw_text)
            
            # Validate content length if max_chars is defined
            if slot_meta:
                max_chars = slot_meta.get("max_chars")
                if max_chars and len(text_str) > max_chars:
                    print(
                        f"⚠️  [Beautifier Warning] Slot {slot_key} content ({len(text_str)} chars) "
                        f"exceeds max_chars ({max_chars})"
                    )
            
            # Parse markdown into styled runs
            runs = parse_markdown(text_str)
            
            # Determine font size using geometry-based approach with slide_role awareness
            if slot_meta:
                role_hint = slot_meta.get("role_hint", "")
                geometry = slot_meta.get("geometry", {})
                area_ratio = geometry.get("area_ratio", 0.1)
                is_circular = geometry.get("is_circular", False)
                
                # Check for circular/oval shape fitting
                if is_circular:
                    radius = geometry.get("radius")
                    if radius and radius > 0:
                        # Use circular text fitting with chord-width constraints
                        font_size = _fit_text_in_circle(text_str, runs, radius)
                        print(
                            f"--- Circular fit: Slot {slot_key} → {font_size}pt "
                            f"(radius={radius:.3f})"
                        )
                    else:
                        # Circular shape but missing radius metadata
                        print(
                            f"⚠️  [Beautifier Warning] Circular shape detected for slot {slot_key} "
                            f"but missing radius, using rectangular sizing"
                        )
                        font_size = _determine_font_size(role_hint, area_ratio, slide_role)
                else:
                    # Standard rectangular sizing with slide_role awareness
                    font_size = _determine_font_size(role_hint, area_ratio, slide_role)
                
                alignment = _alignment_for_role(role_hint)
            else:
                # Fallback if slot metadata not found
                font_size = FONT_SIZE_FALLBACK
                alignment = "LEFT"
            
            # Build style specification for this slot
            styled_content[str(slot_key)] = {
                "runs": runs,
                "font_size": font_size,
                "alignment": alignment
            }
        
        beautified.append({
            "layout_index": layout_idx,
            "content": styled_content,  # Keep "content" key for TypedDict compatibility
            "slide_role": slide_role,  # Preserve slide_role for downstream nodes
            "background_image": slide.get("background_image", {})  # Preserve background spec
        })
    
    print(f"--- Beautifier: Styled {len(beautified)} slides ---")
    
    return {"manifest": beautified}
