from typing import List, Dict, Any


def generate_explanation(species: str, parts: List[Dict], growth: str, observations: List[Dict]) -> Dict[str, Any]:
    """Deterministic explanation — which detected parts contributed and why."""
    details = []
    for p in (parts or [])[:2]:
        details.append({
            "part": p.get("class") or "unknown",
            "confidence": round(float(p.get("confidence") or 0.0), 4),
            "role": "Supports species inference" if (p.get("class") or "").lower() in ["leaf", "flower"] else "Ancillary",
        })

    return {
        "summary": f"Species {species} inferred from detected parts and visual appearance.",
        "details": details,
        "growth_signal": growth or "Unknown",
        "observation_count": len(observations),
    }
