"""
Configuration module for PPT Generation Pipeline
Controls styling behavior, font sizing policies, and template overrides
"""
import os

# Master slide defaults: when True, respect template alignment/sizing unless explicitly overridden
RESPECT_MASTER_DEFAULTS = os.getenv("RESPECT_MASTER_DEFAULTS", "true").lower() == "true"

# Layouts that MUST have explicit font sizing (e.g., KPI tiles need consistent sizing)
# Format: set of layout names that should enforce font size from beautifier
FORCE_FONT_SIZE_LAYOUTS = set(
    os.getenv("FORCE_FONT_SIZE_LAYOUTS", "KPI_TILE,METRIC_CARD").split(",")
) if os.getenv("FORCE_FONT_SIZE_LAYOUTS", "KPI_TILE,METRIC_CARD").strip() else set()

# Roles that benefit from shrink-to-fit autosize behavior
# Format: set of role_hint values where TEXT_TO_FIT_SHAPE should be enabled
ENABLE_AUTOFIT_ROLES = set(
    os.getenv("ENABLE_AUTOFIT_ROLES", "caption,circular_text").split(",")
) if os.getenv("ENABLE_AUTOFIT_ROLES", "caption,circular_text").strip() else set()

# Debug: Log configuration on import
if os.getenv("DEBUG_CONFIG", "false").lower() == "true":
    print(f"📋 Config loaded:")
    print(f"  RESPECT_MASTER_DEFAULTS: {RESPECT_MASTER_DEFAULTS}")
    print(f"  FORCE_FONT_SIZE_LAYOUTS: {FORCE_FONT_SIZE_LAYOUTS}")
    print(f"  ENABLE_AUTOFIT_ROLES: {ENABLE_AUTOFIT_ROLES}")
