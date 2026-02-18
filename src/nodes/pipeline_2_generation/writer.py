# src/nodes/pipeline_2_generation/writer.py
from src.core.state import PPTState, ManifestEntry, BackgroundImageSpec
from src.utils.auth_helper import get_llm
from pydantic import BaseModel, Field
from typing import Dict, Any, List
import json

# Slide role constants (must match architect.py)
ROLE_TITLE = "TITLE"
ROLE_AGENDA = "AGENDA"
ROLE_CONTENT = "CONTENT"
ROLE_DIAGRAM = "DIAGRAM"
ROLE_TIMELINE = "TIMELINE"
ROLE_CLOSING = "CLOSING"

# Lazy LLM initialization
_llm_instance = None

def _get_llm():
    """Lazy load LLM instance."""
    global _llm_instance
    if _llm_instance is None:
        _llm_instance = get_llm(deployment_name="gpt-4", temperature=0.7)
    return _llm_instance
 
def _get_role_specific_rules(slide_role: str) -> str:
    """Return role-specific writing guidelines for the LLM."""
    rules = {
        ROLE_TITLE: """
**TITLE SLIDE RULES**:
- Title: 6-10 words maximum, punchy and memorable
- Subtitle: 10-15 words, provides context or tagline
- Keep it professional and impactful
- No paragraphs, just short phrases
""",
        ROLE_AGENDA: """
**AGENDA SLIDE RULES**:
- List 3-5 key sections/topics
- Each item: 3-6 words (brief section name)
- Use parallel structure (all nouns or all verbs)
- No descriptions, just topic labels
- Example format:
  Vision & Mission
  Current Challenges
  Proposed Solution
  Technical Architecture
  Roadmap
""",
        ROLE_CONTENT: """
**CONTENT SLIDE RULES**:
- Maximum 5 bullet points
- Each bullet: 8-12 words maximum
- Use action verbs and concrete nouns
- NO paragraph blocks - convert to bullets
- Keep language concise and scannable
- One idea per bullet
""",
        ROLE_DIAGRAM: """
**DIAGRAM SLIDE RULES**:
- Output component labels (2-4 words each)
- Add 1-2 brief callouts highlighting key relationships
- NO prose paragraphs
- Think: "what text labels would appear on a diagram?"
- Example: "Frontend Layer", "API Gateway", "Database Cluster"
""",
        ROLE_TIMELINE: """
**TIMELINE SLIDE RULES**:
- Use 3-phase structure: Now / Next / Later (or Q1/Q2/Q3, Phase 1/2/3)  
- Each phase: 1 heading (2-4 words) + 2-3 brief items (4-6 words each)
- Focus on deliverables and milestones
- NO detailed explanations
""",
        ROLE_CLOSING: """
**CLOSING SLIDE RULES**:
- Summary: 2-3 key takeaways (6-8 words each)
- Call-to-action or next steps (1-2 items, brief)
- Keep it motivational and forward-looking
- Avoid dense text
"""
    }
    return rules.get(slide_role, rules[ROLE_CONTENT])


def writer_node(state: PPTState):
    """
    Generates content for each slide using SEMANTIC FIELDS (title, bullets, body, image_query).
    This eliminates the need for arbitrary slot_id addressing, preventing overlap bugs.
    """
    slide_plans = state.get("slide_plans", [])
    content_map = state.get("content_map", "")
    registry = state.get("registry", {})
    final_manifest: List[ManifestEntry] = []
    
    for idx, plan in enumerate(slide_plans):
        l_idx = plan['layout_index']
        slide_role = plan.get('slide_role', ROLE_CONTENT)
        layout_schema = next((l for l in registry.get('layouts', []) if l['layout_index'] == l_idx), {})
        
        # Extract slot information
        slots_info = layout_schema.get('slots', [])
        
        # Identify available semantic roles in this layout
        available_roles = {}
        if slots_info:
            for s in slots_info:
                semantic_role = s.get('semantic_role', 'body')
                # Track which semantic roles are available
                if semantic_role not in available_roles:
                    available_roles[semantic_role] = []
                available_roles[semantic_role].append(s)
        
        # DEFENSIVE: If no slots found, create fallback based on slide role
        if not available_roles:
            print(f"  ⚠️  Slide {idx + 1}: No slots in layout {l_idx} - using role-based fallback for {slide_role}")
            # Provide sensible defaults based on slide role
            if slide_role == ROLE_TITLE:
                available_roles = {'title': [{'semantic_role': 'title', 'max_chars': 100}]}
            elif slide_role == ROLE_AGENDA:
                available_roles = {'title': [{'semantic_role': 'title', 'max_chars': 50}], 
                                   'bullets': [{'semantic_role': 'bullets', 'max_bullets': 5, 'max_chars_per_bullet': 50}]}
            elif slide_role in [ROLE_CONTENT, ROLE_DIAGRAM, ROLE_TIMELINE]:
                available_roles = {'title': [{'semantic_role': 'title', 'max_chars': 80}],
                                   'bullets': [{'semantic_role': 'bullets', 'max_bullets': 5, 'max_chars_per_bullet': 100}]}
            else:  # CLOSING or unknown
                available_roles = {'title': [{'semantic_role': 'title', 'max_chars': 80}],
                                   'body': [{'semantic_role': 'body', 'max_chars': 300}]}
        
        # Log detected semantic roles for debugging
        print(f"  → Slide {idx + 1} ({slide_role}): Semantic roles = {list(available_roles.keys())}")
        
        # Get role-specific writing rules
        role_rules = _get_role_specific_rules(slide_role)
        
        # Build semantic layout description
        semantic_desc = []
        for role, slots in available_roles.items():
            if role == 'title':
                semantic_desc.append(f"  - TITLE: Main headline (6-10 words max)")
            elif role == 'bullets':
                max_bullets = slots[0].get('max_bullets', 5)
                max_chars = slots[0].get('max_chars_per_bullet', 100)
                semantic_desc.append(f"  - BULLETS: Up to {max_bullets} points, {max_chars} chars each")
            elif role == 'body':
                max_chars = slots[0].get('max_chars', 500)
                semantic_desc.append(f"  - BODY: Text content ({max_chars} chars max)")
            elif role == 'image_query':
                semantic_desc.append(f"  - IMAGE_QUERY: Brief image description (50 words max)")
            elif role == 'footer':
                semantic_desc.append(f"  - FOOTER: Metadata (optional)")
        
        semantic_layout = "\n".join(semantic_desc)
        
        # Create example output based on available roles
        example_dict = {}
        if 'title' in available_roles:
            example_dict['title'] = 'Compelling Slide Title Here'
        if 'bullets' in available_roles:
            example_dict['bullets'] = ['First key point', 'Second key point', 'Third key point']
        if 'body' in available_roles:
            example_dict['body'] = 'Supporting text content here'
        # NOTE: image_query intentionally EXCLUDED (NO_IMAGE mode)
        
        prompt = f"""
You are a Professional Content Writer creating PowerPoint slide content.

PROJECT CONTEXT:
{content_map}

SLIDE #{idx + 1} - ROLE: {slide_role}
INTENT: {plan['slide_intent']}

{role_rules}

LAYOUT: {layout_schema.get('layout_name', 'Unknown')}
AVAILABLE SEMANTIC FIELDS:
{semantic_layout}

**SEMANTIC CONTENT GENERATION RULES**:

1. **Output only these semantic fields** (if available in layout):
   - "title": Main headline (6-10 words, punchy)
   - "bullets": Array of bullet points (respect max_bullets and max_chars_per_bullet)
   - "body": Paragraph text (respect max_chars)
   - "footer": Optional metadata (date, disclaimers)
   
   **DO NOT** generate "image_query" field (NO_IMAGE mode - text-only slides)

2. **CRITICAL TEXT FORMATTING RULES**:
   - Use **text** for bold emphasis and *text* for italic emphasis
   - ALWAYS preserve spaces around emphasis markers
   - CORRECT: "This is **bold text** in a sentence"
   - INCORRECT: "This is**bold text**in a sentence" or "due to **bold**text"
   - After closing emphasis markers, add a space before the next word
   - Use emphasis sparingly (1-2 times per field maximum)
   - Do NOT use other markdown (#, _, lists, code blocks)

3. **BULLETS FORMAT**:
   - Output as JSON array: ["First point", "Second point", "Third point"]
   - Each bullet is a separate string in the array
   - Do NOT include bullet symbols (•, -, *) - those are added automatically

4. **CONSTRAINTS**:
   - Only output fields that exist in the layout (see AVAILABLE SEMANTIC FIELDS above)
   - Respect character/bullet limits shown in the layout description
   - Keep content concise and slide-native (not document prose)

**OUTPUT FORMAT (JSON only, no markdown code blocks)**:
{{
  "content": {{
    "title": "string",
    "bullets": ["string", "string", ...],
    "body": "string",
    "image_query": "string",
    "footer": "string"
  }}
}}

Example for THIS layout:
{{
  "content": {json.dumps(example_dict)}
}}

**FINAL REMINDER**:
- Follow the **{slide_role} SLIDE RULES** above strictly
- Preserve spaces around **bold** and *italic* markers
- Output ONLY the semantic fields available in this layout
- Keep content concise and slide-native (not document prose)

Generate the JSON now:
        """
        
        try:
            response = _get_llm().invoke(prompt)
            response_text = response.content.strip()
            
            # Try to parse JSON, handling markdown code blocks if present
            if response_text.startswith("```"):
                # Remove markdown code fences
                response_text = response_text.split("```")[1]
                if response_text.startswith("json"):
                    response_text = response_text[4:]
                response_text = response_text.strip()
            
            # Parse the JSON
            parsed = json.loads(response_text)
            
            # Extract the content dictionary
            if "content" in parsed:
                content_dict = parsed["content"]
            else:
                content_dict = parsed
            
            # CRITICAL: Filter content to ONLY include fields that exist in available_roles
            # (Prevents LLM from generating unmappable content)
            valid_content = {}
            for field in ['title', 'bullets', 'body', 'footer', 'image_query']:
                if field in content_dict and field in available_roles:
                    valid_content[field] = content_dict[field]
                elif field in content_dict and field not in available_roles:
                    print(f"  ⚠️  Removed '{field}' from LLM output (not in layout: {list(available_roles.keys())})")
            
            content_dict = valid_content
            
            # DEFENSIVE: If filtering left us with no valid content, populate available roles
            if not content_dict:
                print(f"  ⚠️  All LLM content filtered out - generating content for available roles: {list(available_roles.keys())}")
                if 'title' in available_roles:
                    content_dict['title'] = plan.get('slide_intent', f"Slide {idx + 1}")
                if 'bullets' in available_roles:
                    content_dict['bullets'] = ["Key point 1", "Key point 2", "Key point 3"]
                if 'body' in available_roles:
                    # Use slide_intent or extract from content_map
                    content_dict['body'] = f"{plan.get('slide_intent', 'Content')}. {content_map[:200]}..."
                if 'footer' in available_roles:
                    content_dict['footer'] = "© EY 2026"
            
            # CRITICAL: Strip image_query if LLM generated it anyway (NO_IMAGE mode)
            if 'image_query' in content_dict:
                print(f"  ⚠️  Removed image_query from LLM output (NO_IMAGE mode)")
                del content_dict['image_query']
            
            # Defensive: Remove image prompt phrases from bullets
            if 'bullets' in content_dict:
                # DEFENSIVE: Ensure bullets is a list (LLM sometimes returns string)
                if isinstance(content_dict['bullets'], str):
                    # Try to split by newlines or convert to single-item list
                    if '\n' in content_dict['bullets']:
                        content_dict['bullets'] = [line.strip() for line in content_dict['bullets'].split('\n') if line.strip()]
                    else:
                        content_dict['bullets'] = [content_dict['bullets']]
                
                if isinstance(content_dict['bullets'], list):
                    sanitized_bullets = []
                    for bullet in content_dict['bullets']:
                        # Skip bullets that are image descriptions
                        if any(phrase in str(bullet).lower() for phrase in ['image:', 'photo of', 'diagram showing', 'timeline diagram', 'visual of', 'illustration of']):
                            print(f"  ⚠️  Filtered image prompt bullet: {str(bullet)[:50]}...")
                            continue
                        sanitized_bullets.append(bullet)
                    content_dict['bullets'] = sanitized_bullets
                else:
                    # Last resort: remove invalid bullets field
                    print(f"  ⚠️  Invalid bullets format (not list or string), removing field")
                    del content_dict['bullets']
            
            # Create default background image spec (will be populated by image_director)
            background_spec: BackgroundImageSpec = {
                "enabled": False,
                "keywords": "",
                "mood": "",
                "composition": "",
                "overlay_opacity": 0.0
            }
            
            final_manifest.append({
                "layout_index": l_idx,
                "content": content_dict,
                "slide_role": slide_role,
                "background_image": background_spec,
                "_semantic_mapping": available_roles  # Store slot metadata for Injector
            })
            
            # Log content summary for debugging
            content_fields = [k for k, v in content_dict.items() if v]  # Non-empty fields
            print(f"  ✓ Slide {idx + 1}: Generated {len(content_fields)} fields: {content_fields}")
            
        except (json.JSONDecodeError, Exception) as e:
            print(f"  ⚠️  Error parsing LLM response for slide {idx + 1}: {e}")
            if 'response_text' in locals():
                print(f"  Response preview: {response_text[:150]}...")
            elif 'response' in locals():
                print(f"  Response preview: {response.content[:150]}...")
            
            # Create role-based default semantic content as fallback
            default_content = {}
            if 'title' in available_roles:
                # Generate role-appropriate title
                if slide_role == ROLE_TITLE:
                    default_content['title'] = plan.get('slide_intent', f"Presentation Slide {idx + 1}")
                elif slide_role == ROLE_AGENDA:
                    default_content['title'] = "Agenda"
                else:
                    default_content['title'] = plan.get('slide_intent', f"Content Slide {idx + 1}")
            
            if 'bullets' in available_roles:
                # Generate role-appropriate bullets
                if slide_role == ROLE_AGENDA:
                    default_content['bullets'] = ["Overview", "Key Topics", "Next Steps"]
                else:
                    default_content['bullets'] = [
                        "Key point from project documentation",
                        "Supporting detail or evidence",
                        "Actionable insight or takeaway"
                    ]
            
            if 'body' in available_roles:
                default_content['body'] = f"Content for {slide_role} slide based on: {plan.get('slide_intent', 'project context')}"
            
            print(f"  → Using fallback content with fields: {list(default_content.keys())}")
            
            background_spec: BackgroundImageSpec = {
                "enabled": False,
                "keywords": "",
                "mood": "",
                "composition": "",
                "overlay_opacity": 0.0
            }
            final_manifest.append({
                "layout_index": l_idx,
                "content": default_content,
                "slide_role": slide_role,
                "background_image": background_spec,
                "_semantic_mapping": available_roles  # Store for Injector
            })
        
    print(f"--- Writer: Generated manifest for {len(final_manifest)} slides ---")
    return {"manifest": final_manifest}