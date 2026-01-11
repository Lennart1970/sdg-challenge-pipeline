"""
JSON schemas for structured LLM outputs
"""

# Technology Discovery Agent output schema
# Used with OpenAI Responses API for guaranteed JSON structure
TECH_DISCOVERY_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "properties": {
        "challenge_summary": {
            "type": "string",
            "description": "Brief restatement of the challenge being addressed"
        },
        "core_functions": {
            "type": "array",
            "items": {"type": "string"},
            "description": "List of core functions that must be performed (what must happen)"
        },
        "underlying_principles": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Physical, chemical, or mechanical principles that enable these functions"
        },
        "technology_paths": {
            "type": "array",
            "items": {
                "type": "object",
                "additionalProperties": False,
                "properties": {
                    "path_name": {
                        "type": "string",
                        "description": "Descriptive name for this technology path"
                    },
                    "principles_used": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Which principles from the list are used in this path"
                    },
                    "technology_classes": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Technology classes (NOT brands or products) that could implement this"
                    },
                    "why_this_is_plausible": {
                        "type": "string",
                        "description": "Explanation of why this path is technically and economically feasible"
                    },
                    "estimated_cost_band_eur": {
                        "type": "string",
                        "description": "Cost estimate band (e.g., '€500-€2000', '€3000-€8000')"
                    },
                    "risks_and_unknowns": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Key risks, unknowns, or assumptions in this path"
                    }
                },
                "required": [
                    "path_name",
                    "principles_used",
                    "technology_classes",
                    "why_this_is_plausible",
                    "estimated_cost_band_eur",
                    "risks_and_unknowns"
                ]
            },
            "minItems": 1,
            "maxItems": 3,
            "description": "2-3 plausible technology paths under the budget constraint"
        },
        "confidence": {
            "type": "number",
            "minimum": 0.0,
            "maximum": 1.0,
            "description": "Confidence in the feasibility of these paths (0.0-1.0)"
        }
    },
    "required": [
        "challenge_summary",
        "core_functions",
        "underlying_principles",
        "technology_paths",
        "confidence"
    ]
}
