"""Qualify the existing deterministic sports engines; defaults are never measurements."""
from __future__ import annotations
import math


PREDICTION_INPUTS = {
    "tennis": {"wellness": ("sleep_score", "hrv_score", "soreness_pct", "training_load_pct"),
               "mental": ("frustration_pct", "anxiety_pct"), "match_stats": ("first_serve_pct", "backhand_target_win_pct", "unforced_errors")},
    "swimming": {"wellness": ("sleep_score", "soreness_pct", "shoulder_pain_pct"),
                 "breathing": ("bilateral_breathing_pct", "breath_control_pct", "panic_pct"),
                 "technique": ("body_position_pct", "catch_efficiency_pct", "kick_timing_pct")},
    "cycling": {"wellness": ("sleep_score", "hrv_score", "leg_soreness_pct", "knee_pain_pct", "back_pain_pct", "neck_pain_pct"),
                "bike_fit": ("knee_tracking_pct", "saddle_comfort_pct", "reach_comfort_pct"),
                },
}


def _finite(value):
    try:
        return value is not None and not isinstance(value, bool) and math.isfinite(float(value)) and float(value) >= 0
    except (TypeError, ValueError, OverflowError):
        return False


def qualify_sports_result(result: dict, data: dict, sport: str) -> dict:
    data = dict(data)
    if sport == 'cycling' and isinstance(data.get('wellness'),dict):
        data['wellness'] = dict(data['wellness'])
        if data['wellness'].get('leg_soreness_pct') is None and data['wellness'].get('soreness_pct') is not None:
            data['wellness']['leg_soreness_pct'] = data['wellness']['soreness_pct']
    missing = [f"{group}.{key}" for group, keys in PREDICTION_INPUTS[sport].items()
               for key in keys if not _finite((data.get(group) if isinstance(data.get(group),dict) else {}).get(key))]
    result["data_quality"] = {
        "prediction_basis": "heuristic_estimate" if not missing else "insufficient_evidence",
        "missing_prediction_inputs": missing,
        "provided_inputs": {key: sorted(value) for key, value in data.items() if isinstance(value, dict) and value},
        "defaults_are_measurements": False,
        "guidance_kind": "initial_guidance" if missing else "data_informed_guidance",
    }
    prediction = result["agents"]["qaf_prediction"]
    prediction["evidence_status"] = result["data_quality"]["prediction_basis"]
    prediction["missing_inputs"] = missing
    if missing:
        prediction["evidence"] = {key: None for key in prediction.get("evidence", {})}
        prediction["confidence"] = 0.0
        prediction["recommendation"] = "Faltan señales actuales para estimar preparación y riesgo. La propuesta es una guía inicial."
    else:
        prediction["evidence"]["interpretation"] = "Índices heurísticos; no son probabilidades clínicas ni mediciones directas."
    # The displayed duration agrees with the actual blocks, including direct API results.
    plan = result.get("session_plan") or {}
    blocks = plan.get("blocks") or []
    if blocks:
        plan["total_minutes"] = sum(float(b.get("minutes") or 0) for b in blocks)
    return result


def prediction_summary(result: dict) -> str:
    prediction = ((result.get("agents") or {}).get("qaf_prediction") or {})
    if prediction.get("evidence_status") != "heuristic_estimate":
        return "**Predicción QAF:** preparación y riesgo no estimados; faltan señales actuales. Los ejercicios son una guía inicial, no una medición de tu estado."
    evidence = prediction.get("evidence") or {}
    risk = evidence.get("injury_risk", evidence.get("overload_risk"))
    return f"**Predicción QAF:** índice heurístico de preparación {float(evidence['readiness']):.2f} y de riesgo {float(risk):.2f}. No representan probabilidades clínicas."


def fit_session_to_context(result: dict, context: dict) -> dict:
    plan = result.get("session_plan") or {}
    blocks = plan.get("blocks") or []
    minutes = int(float(context["session_minutes"]))
    if blocks:
        total = sum(float(b.get("minutes") or 0) for b in blocks)
        remaining = minutes
        for index, block in enumerate(blocks):
            duration = remaining if index == len(blocks) - 1 else max(1, round(minutes * float(block.get("minutes") or 0) / max(1, total)))
            duration = min(duration, remaining - (len(blocks) - index - 1))
            block["minutes"] = duration
            remaining -= duration
    plan["total_minutes"] = minutes
    if float(context["pain_0_10"]) > 3:
        plan["available_minutes"] = minutes
        plan["total_minutes"] = 0
        plan["blocks"] = []
        plan["status"] = "needs_pain_review"
        plan["intensity"] = "baja-controlada"
        plan["progression_rule"] = "No aumentar carga mientras exista dolor; revisar el contexto antes de progresar."
        result["risk_flags"] = list(dict.fromkeys([*result.get("risk_flags", []), "reported_pain_priority"]))
        result["next_best_action"] = "Priorizar la revisión de la molestia y adaptar la sesión antes de aumentar carga."
        result["priority_focus"] = "revisión de la molestia reportada"
        result["recommended_drills"] = []
        result["microcycle"] = []
    result["session_plan"] = plan
    result["sports_context"] = context
    return result

