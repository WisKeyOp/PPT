# Node 1: Logic to extract PPTX shape IDs with normalized geometry
from pptx import Presentation
from src.core.state import Pipeline1State
from src.utils.ppt_helper import get_placeholder_metadata, calculate_area

def parse_template_node(state: Pipeline1State):
    """
    Extracts placeholder metadata with normalized geometry (0.0 to 1.0) for semantic analysis.
    """
    prs = Presentation(state['template_path'])
    
    layouts_data = []
    
    # Iterate over all layouts in the master
    for i, layout in enumerate(prs.slide_layouts):
        # Get slide dimensions from the layout
        slide_width = prs.slide_width
        slide_height = prs.slide_height
        
        # Use the helper to get clean metadata for this layout
        shapes = get_placeholder_metadata(layout)
        
        # Enrich with normalized geometry and area calculations
        for shape in shapes:
            width = shape.get('width') or 0
            height = shape.get('height') or 0
            left = shape.get('left') or 0
            top = shape.get('top') or 0
            shape_type = shape.get('shape_type', 'rectangle')
            
            # Calculate normalized positions (0.0 to 1.0)
            shape['norm_left'] = left / slide_width if slide_width > 0 else 0
            shape['norm_top'] = top / slide_height if slide_height > 0 else 0
            shape['norm_width'] = width / slide_width if slide_width > 0 else 0
            shape['norm_height'] = height / slide_height if slide_height > 0 else 0
            
            # Calculate area ratio (percentage of slide)
            total_area = slide_width * slide_height
            shape['area_ratio'] = (width * height) / total_area if total_area > 0 else 0
            
            # Keep legacy area score for backward compatibility
            shape['area_score'] = calculate_area(width, height)
            
            # Add circular geometry metadata for oval shapes
            if shape_type == 'oval':
                # For ovals/circles, calculate radius (using minimum dimension for true circles)
                norm_width = shape['norm_width']
                norm_height = shape['norm_height']
                shape['is_circular'] = True
                shape['radius'] = min(norm_width, norm_height) / 2
                
                # For ellipses (different width/height), store both axes
                if abs(norm_width - norm_height) > 0.01:  # Not a perfect circle
                    shape['ellipse_axes'] = (norm_width / 2, norm_height / 2)
            else:
                shape['is_circular'] = False
            
        layouts_data.append({
            "index": i,
            "name": layout.name,
            "shapes": shapes
        })
        
    return {"raw_shape_data": layouts_data}