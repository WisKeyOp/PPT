from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator

class PPTState(TypedDict):
    # Inputs from Pipeline 1 and User
    registry: Dict[str, Any]
    source_material: str
    user_context: Optional[str]
    
    # Reasoning data
    storyboard: List[Dict[str, Any]]
    injection_plan: List[Dict[str, Any]]
    
    # Execution data
    assets: Dict[int, str]
    validation_errors: Annotated[List[str], operator.add]
    iteration_count: int
    status: str