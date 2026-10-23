from __future__ import annotations

import re
import unicodedata
from api.qaf_sports_evidence import qualify_sports_result, prediction_summary
from dataclasses import dataclass
from typing import Any, Dict, List


AGENT_KEYS = (
    "tennis_coach_orchestrator",
    "biomechanics",
    "tactical",
    "match_intelligence",
    "physical_performance",
    "recovery",
    "nutrition",
    "mental",
    "learning",
    "qaf_entanglement",
    "asa_memory",
    "qaf_prediction",
)


@dataclass(frozen=True)
class TennisIntelligenceResult:
    payload: Dict[str, Any]


def _safe_dict(value: Any) -> Dict[str, Any]:
    return value if isinstance(value, dict) else {}


def _safe_text(value: Any) -> str:
    try:
        return str(value or "")
    except Exception:
        return ""


def _normalize_text(value: Any) -> str:
    text = _safe_text(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", text).strip()


def _clamp(value: Any, default: float = 0.0, lo: float = 0.0, hi: float = 1.0) -> float:
    try:
        out = float(value)
    except Exception:
        out = float(default)
    if out < lo:
        return lo
    if out > hi:
        return hi
    return out


def _score_from_percent(value: Any, default: float = 0.55) -> float:
    score = _clamp(value, default=default, lo=0.0, hi=100.0)
    if score > 1.0:
        return _clamp(score / 100.0)
    return _clamp(score, default=default)


def _keyword_hit(text: str, *words: str) -> bool:
    return any(word in text for word in words)


def _agent_payload(name: str, focus: str, score: float, recommendation: str, evidence: Dict[str, Any] | None = None) -> Dict[str, Any]:
    return {
        "agent": name,
        "status": "active",
        "focus": focus,
        "confidence": round(_clamp(score, default=0.55), 4),
        "recommendation": recommendation,
        "evidence": evidence or {},
    }


def _biomechanics_agent(message_norm: str, biomechanics: Dict[str, Any]) -> Dict[str, Any]:
    serve_angle = _clamp(biomechanics.get("serve_elbow_angle_deg"), default=95.0, lo=0.0, hi=180.0)
    hip_rotation = _score_from_percent(biomechanics.get("hip_rotation_pct"), default=0.58)
    weight_transfer = _score_from_percent(biomechanics.get("weight_transfer_pct"), default=0.56)
    serve_context = _keyword_hit(message_norm, "saque", "servicio", "serve")
    if serve_context and (hip_rotation < 0.62 or weight_transfer < 0.62):
        focus = "saque: rotación y transferencia"
        recommendation = "Priorizar cadena cinética: carga de piernas, rotación de cadera y transferencia hacia delante antes de acelerar el brazo."
        score = 0.72 + (0.12 if serve_angle < 105 else 0.0)
    elif _keyword_hit(message_norm, "reves", "revés", "backhand"):
        focus = "revés: estabilidad y punto de contacto"
        recommendation = "Entrenar apoyo externo, preparación temprana y punto de contacto delante del cuerpo."
        score = 0.68
    elif _keyword_hit(message_norm, "drive", "derecha", "forehand"):
        focus = "drive: timing y cierre de golpe"
        recommendation = "Ajustar distancia lateral, acelerar desde cadera-hombro y cerrar con control de balance."
        score = 0.66
    else:
        focus = "técnica base"
        recommendation = "Registrar 20 segundos de golpe principal para medir postura, pies y transferencia."
        score = 0.55
    return _agent_payload(
        "Tennis Biomechanics Agent",
        focus,
        score,
        recommendation,
        {"serve_elbow_angle_deg": round(serve_angle, 1), "hip_rotation": hip_rotation, "weight_transfer": weight_transfer},
    )


def _tactical_agent(message_norm: str, match_stats: Dict[str, Any]) -> Dict[str, Any]:
    first_serve = _score_from_percent(match_stats.get("first_serve_pct"), default=0.58)
    backhand_win = _score_from_percent(match_stats.get("backhand_target_win_pct"), default=0.55)
    unforced_errors = _clamp(match_stats.get("unforced_errors"), default=14.0, lo=0.0, hi=80.0)
    if first_serve < 0.55:
        focus = "patrón con primer servicio"
        recommendation = "Bajar riesgo del primer saque y abrir punto con dirección segura antes de buscar potencia."
        score = 0.74
    elif backhand_win >= 0.62:
        focus = "explotar revés del rival"
        recommendation = "Construir puntos profundos al revés rival y cambiar paralelo solo con pelota corta."
        score = 0.73
    elif unforced_errors >= 18:
        focus = "reducción de errores no forzados"
        recommendation = "Usar margen alto cruzado por 6 bolas antes de acelerar a línea."
        score = 0.70
    else:
        focus = "plan táctico base"
        recommendation = "Medir primer saque, errores y puntos ganados por zona para detectar patrón dominante."
        score = 0.58
    return _agent_payload("Tennis Tactical Agent", focus, score, recommendation, {"first_serve": first_serve, "backhand_target_win": backhand_win, "unforced_errors": unforced_errors})


def _match_intelligence_agent(match_stats: Dict[str, Any]) -> Dict[str, Any]:
    break_points = _score_from_percent(match_stats.get("break_points_won_pct"), default=0.45)
    second_serve = _score_from_percent(match_stats.get("second_serve_points_won_pct"), default=0.48)
    focus = "scouting competitivo"
    if break_points < 0.42:
        recommendation = "Crear dos patrones predefinidos para break points: devolución profunda cruzada y primer golpe al centro."
        score = 0.70
    elif second_serve < 0.46:
        recommendation = "Proteger segundo saque con efecto alto y dirección al cuerpo; evitar doble falta emocional."
        score = 0.68
    else:
        recommendation = "Construir scouting por rival: dirección de saque, bola débil y patrón bajo presión."
        score = 0.57
    return _agent_payload("Tennis Match Intelligence Agent", focus, score, recommendation, {"break_points_won": break_points, "second_serve_points_won": second_serve})


def _physical_agent(wellness: Dict[str, Any]) -> Dict[str, Any]:
    lateral_speed = _score_from_percent(wellness.get("lateral_speed_pct"), default=0.62)
    training_load = _score_from_percent(wellness.get("training_load_pct"), default=0.62)
    if lateral_speed < 0.55:
        focus = "velocidad lateral"
        recommendation = "Añadir bloques cortos de split-step, desplazamiento lateral y recuperación al centro."
        score = 0.74
    elif training_load > 0.82:
        focus = "carga acumulada"
        recommendation = "Reducir volumen 20% durante 48 horas y mantener intensidad técnica controlada."
        score = 0.72
    else:
        focus = "potencia específica"
        recommendation = "Mantener microdosis de fuerza unilateral, core rotacional y aceleraciones de 5 metros."
        score = 0.59
    return _agent_payload("Tennis Physical Performance Agent", focus, score, recommendation, {"lateral_speed": lateral_speed, "training_load": training_load})


def _recovery_agent(wellness: Dict[str, Any]) -> Dict[str, Any]:
    sleep = _score_from_percent(wellness.get("sleep_score"), default=0.64)
    hrv = _score_from_percent(wellness.get("hrv_score"), default=0.60)
    soreness = _score_from_percent(wellness.get("soreness_pct"), default=0.35)
    risk = _clamp((1.0 - sleep) * 0.38 + (1.0 - hrv) * 0.32 + soreness * 0.30)
    if risk >= 0.55:
        focus = "riesgo de sobrecarga"
        recommendation = "Priorizar sueño, movilidad y sesión técnica sin fatigar piernas antes de competir."
        score = 0.78
    else:
        focus = "recuperación suficiente"
        recommendation = "Mantener rutina nocturna y recuperación activa post-entrenamiento."
        score = 0.58
    return _agent_payload("Tennis Recovery Agent", focus, score, recommendation, {"recovery_risk": round(risk, 4), "sleep_score": sleep, "hrv_score": hrv, "soreness": soreness})


def _nutrition_agent(nutrition: Dict[str, Any]) -> Dict[str, Any]:
    hydration = _score_from_percent(nutrition.get("hydration_pct"), default=0.62)
    carb_timing = _score_from_percent(nutrition.get("carb_timing_pct"), default=0.58)
    if hydration < 0.55:
        focus = "hidratación de partido"
        recommendation = "Plan de hidratación 2 horas antes y sorbos con electrolitos en cambios de lado."
        score = 0.72
    elif carb_timing < 0.55:
        focus = "energía pre-partido"
        recommendation = "Asegurar carbohidrato fácil 90-150 minutos antes y snack si el partido supera 75 minutos."
        score = 0.69
    else:
        focus = "nutrición estable"
        recommendation = "Mantener timing nutricional y registrar sensaciones durante tercer set o sesiones largas."
        score = 0.56
    return _agent_payload("Tennis Nutrition Agent", focus, score, recommendation, {"hydration": hydration, "carb_timing": carb_timing})


def _mental_agent(message_norm: str, mental: Dict[str, Any]) -> Dict[str, Any]:
    frustration_signal = _score_from_percent(mental.get("frustration_pct"), default=0.0)
    anxiety_signal = _score_from_percent(mental.get("anxiety_pct"), default=0.0)
    cue_hit = _keyword_hit(message_norm, "frustr", "ansiedad", "miedo", "error", "me bloqueo", "presion", "presión")
    pressure = _clamp(max(frustration_signal, anxiety_signal, 0.68 if cue_hit else 0.0))
    if pressure >= 0.62:
        focus = "control emocional bajo presión"
        recommendation = "Usar rutina de 12 segundos: respirar, elegir objetivo grande y aceptar margen antes del siguiente punto."
        score = 0.77
    else:
        focus = "mental competitivo"
        recommendation = "Definir una frase de proceso por set y revisar si la atención se queda en el punto actual."
        score = 0.57
    return _agent_payload("Tennis Mental Agent", focus, score, recommendation, {"pressure_signal": round(pressure, 4)})


def _learning_agent(skills: Dict[str, Any]) -> Dict[str, Any]:
    normalized = {
        "drive": _score_from_percent(skills.get("drive"), default=0.68),
        "reves": _score_from_percent(skills.get("reves"), default=0.58),
        "volea": _score_from_percent(skills.get("volea"), default=0.48),
        "saque": _score_from_percent(skills.get("saque"), default=0.60),
        "movilidad": _score_from_percent(skills.get("movilidad"), default=0.62),
    }
    weakest = min(normalized, key=normalized.get)
    focus = f"aprendizaje: {weakest}"
    recommendation = f"Crear bloque deliberado de 15 minutos para {weakest}: una métrica, una consigna y feedback inmediato."
    score = 0.62 + (0.18 * (1.0 - normalized[weakest]))
    return _agent_payload("Tennis Learning Agent", focus, score, recommendation, {"skill_map": normalized, "lowest_skill": weakest})


def _asa_memory_agent(memory: Dict[str, Any], message_norm: str) -> Dict[str, Any]:
    previous = memory.get("previous_issues") if isinstance(memory.get("previous_issues"), list) else []
    normalized_previous = [_normalize_text(item) for item in previous if _safe_text(item)]
    repeated = ""
    for item in normalized_previous:
        if item and (item in message_norm or any(token in message_norm for token in item.split()[:2])):
            repeated = item
            break
    if repeated:
        focus = "patrón recurrente detectado"
        recommendation = "Retomar el ajuste ya trabajado y comparar métrica actual contra el último registro ASA."
        score = 0.76
    else:
        focus = "memoria deportiva ASA"
        recommendation = "Guardar objetivo, lesión, golpe prioritario y próximos torneos para continuidad del coach."
        score = 0.58
    return _agent_payload("ASA Memory Agent", focus, score, recommendation, {"previous_issue_match": repeated, "known_issues": normalized_previous[-5:]})


def _entanglement_agent(agents: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    recovery_risk = _clamp((agents.get("recovery") or {}).get("evidence", {}).get("recovery_risk"), default=0.32)
    mental_pressure = _clamp((agents.get("mental") or {}).get("evidence", {}).get("pressure_signal"), default=0.35)
    physical_load = _clamp((agents.get("physical_performance") or {}).get("evidence", {}).get("training_load"), default=0.62)
    entanglement = _clamp(0.38 * recovery_risk + 0.34 * mental_pressure + 0.28 * physical_load)
    if entanglement >= 0.62:
        focus = "correlación sueño-fatiga-presión"
        recommendation = "No interpretar el fallo técnico aislado: validar sueño, carga y presión emocional antes de subir volumen."
        score = 0.79
    else:
        focus = "correlaciones QAF estables"
        recommendation = "Seguir acumulando datos para relacionar sueño, nutrición, mentalidad y resultado."
        score = 0.58
    return _agent_payload("QAF Entanglement Agent", focus, score, recommendation, {"entanglement_score": round(entanglement, 4)})


def _prediction_agent(agents: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    recovery_risk = _clamp((agents.get("recovery") or {}).get("evidence", {}).get("recovery_risk"), default=0.32)
    entanglement = _clamp((agents.get("qaf_entanglement") or {}).get("evidence", {}).get("entanglement_score"), default=0.38)
    tactical_conf = _clamp((agents.get("tactical") or {}).get("confidence"), default=0.58)
    injury_risk = _clamp(0.62 * recovery_risk + 0.38 * entanglement)
    readiness = _clamp(1.0 - injury_risk + (tactical_conf - 0.55) * 0.18)
    focus = "predicción rendimiento-riesgo"
    if injury_risk >= 0.55:
        recommendation = "Reducir carga y priorizar precisión técnica; riesgo de lesión/caída de rendimiento elevado."
    elif readiness >= 0.68:
        recommendation = "Buen momento para sesión competitiva con objetivo táctico específico."
    else:
        recommendation = "Sesión mixta: técnica + táctica sin sobrecargar volumen."
    return _agent_payload("QAF Prediction Agent", focus, 0.66, recommendation, {"injury_risk": round(injury_risk, 4), "readiness": round(readiness, 4)})



def _profile_context(player_profile: Dict[str, Any], message_norm: str) -> Dict[str, Any]:
    level = _normalize_text(player_profile.get("level") or "recreativo/intermedio")
    style = _normalize_text(player_profile.get("style") or player_profile.get("playing_style") or "all-court")
    goal = _normalize_text(player_profile.get("goal") or player_profile.get("objective") or "mejorar rendimiento")
    surface = _normalize_text(player_profile.get("surface") or player_profile.get("preferred_surface") or "dura/arcilla")
    competition_mode = _normalize_text(player_profile.get("competition_mode") or player_profile.get("mode") or "singles")
    dominant_hand = _normalize_text(player_profile.get("dominant_hand") or "no especificada")
    backhand_type = _normalize_text(player_profile.get("backhand_type") or "no especificado")
    if "dobles" in message_norm or "doubles" in message_norm:
        competition_mode = "dobles"
    is_beginner = any(token in level for token in ("principiante", "beginner", "inicial", "recreativo"))
    is_competitive = any(token in level for token in ("compet", "avanz", "ranking", "torneo", "alto rendimiento")) or any(token in goal for token in ("torneo", "ranking", "compet"))
    return {
        "level": level or "recreativo/intermedio",
        "style": style or "all-court",
        "goal": goal or "mejorar rendimiento",
        "surface": surface or "dura/arcilla",
        "competition_mode": competition_mode or "singles",
        "dominant_hand": dominant_hand,
        "backhand_type": backhand_type,
        "is_beginner": is_beginner,
        "is_competitive": is_competitive,
    }


def _technical_gaps(message_norm: str, biomechanics: Dict[str, Any], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    gaps: List[Dict[str, Any]] = []
    serve_toss = _score_from_percent(biomechanics.get("serve_toss_consistency_pct"), default=0.58)
    contact = _score_from_percent(biomechanics.get("contact_point_pct"), default=0.60)
    split_step = _score_from_percent(biomechanics.get("split_step_timing_pct"), default=0.57)
    net_stability = _score_from_percent(biomechanics.get("net_stability_pct"), default=0.55)
    if _keyword_hit(message_norm, "saque", "servicio", "serve") or serve_toss < 0.55:
        gaps.append({"area": "saque", "metric": "lanzamiento + contacto", "priority": round(1.0 - min(serve_toss, contact), 4), "cue": "lanzamiento consistente, impacto alto y caída equilibrada"})
    if _keyword_hit(message_norm, "volea", "red", "dobles", "volley") or net_stability < 0.55:
        gaps.append({"area": "volea/transición", "metric": "split-step + estabilidad en red", "priority": round(1.0 - min(split_step, net_stability), 4), "cue": "split-step antes del golpe rival, raqueta adelante y cierre corto"})
    if _keyword_hit(message_norm, "reves", "revés", "backhand"):
        gaps.append({"area": "revés", "metric": "preparación + contacto delante", "priority": 0.42, "cue": f"adaptar progresión al revés {profile.get('backhand_type') or 'del jugador'}"})
    if _keyword_hit(message_norm, "drive", "derecha", "forehand"):
        gaps.append({"area": "drive", "metric": "distancia lateral + cadena cadera-hombro", "priority": 0.40, "cue": "crear margen cruzado antes de acelerar paralelo"})
    return sorted(gaps, key=lambda row: float(row.get("priority") or 0.0), reverse=True)[:4]


def _injury_precautions(agents: Dict[str, Dict[str, Any]], biomechanics: Dict[str, Any], wellness: Dict[str, Any]) -> List[Dict[str, Any]]:
    recovery_risk = _clamp((agents.get("recovery") or {}).get("evidence", {}).get("recovery_risk"), default=0.32)
    soreness = _score_from_percent(wellness.get("soreness_pct"), default=0.35)
    serve_volume = _clamp(wellness.get("serve_volume") or wellness.get("serves_today"), default=60.0, lo=0.0, hi=300.0)
    shoulder = _score_from_percent(wellness.get("shoulder_pain_pct"), default=0.0)
    elbow = _score_from_percent(wellness.get("elbow_pain_pct"), default=0.0)
    wrist = _score_from_percent(wellness.get("wrist_pain_pct"), default=0.0)
    knee = _score_from_percent(wellness.get("knee_pain_pct"), default=0.0)
    risks: List[Dict[str, Any]] = []
    if shoulder >= 0.35 or serve_volume >= 95:
        risks.append({"zone": "hombro", "level": "medium" if shoulder < 0.65 else "high", "action": "limitar volumen de saques, priorizar manguito rotador y técnica de cadena cinética"})
    if elbow >= 0.30 or wrist >= 0.30:
        risks.append({"zone": "codo/muñeca", "level": "medium" if max(elbow, wrist) < 0.65 else "high", "action": "revisar grip/tensión de raqueta y añadir fuerza de antebrazo sin dolor"})
    if knee >= 0.35 or soreness >= 0.62:
        risks.append({"zone": "rodilla/pierna", "level": "medium" if max(knee, soreness) < 0.70 else "high", "action": "bajar cambios de dirección, incluir movilidad y progresión lateral controlada"})
    if recovery_risk >= 0.55:
        risks.append({"zone": "sistema general", "level": "high", "action": "convertir la sesión en técnica de baja fatiga y recuperación activa"})
    return risks[:4]


def _recommended_drills(priority_key: str, agents: Dict[str, Dict[str, Any]], profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    mode = profile.get("competition_mode") or "singles"
    level = profile.get("level") or "intermedio"
    drills = {
        "biomechanics": [
            {"name": "Saque: toss-contact-balance", "duration_minutes": 12, "sets": 3, "reps": "8 saques por set", "intensity": "moderada", "success_metric": "70% de lanzamientos caen en la misma zona y caída equilibrada", "coaching_cue": "subir con piernas antes de acelerar el brazo"},
            {"name": "Shadow swings con pausa de contacto", "duration_minutes": 6, "sets": 2, "reps": "10 repeticiones", "intensity": "baja", "success_metric": "contacto delante sin perder postura", "coaching_cue": "preparar temprano y mantener cabeza estable"},
        ],
        "tactical": [
            {"name": "Patrón 6 bolas cruzadas + cambio", "duration_minutes": 14, "sets": 4, "reps": "rallies a 6 bolas", "intensity": "media-alta", "success_metric": "60% de rallies llegan a 6 bolas antes del cambio", "coaching_cue": "margen primero, aceleración solo con pelota corta"},
            {"name": "Serve +1 por dirección", "duration_minutes": 12, "sets": 3, "reps": "6 puntos por dirección", "intensity": "competitiva", "success_metric": "ganar o neutralizar 65% de primeros golpes", "coaching_cue": "decidir el primer golpe antes de sacar"},
        ],
        "physical_performance": [
            {"name": "Split-step + recuperación al centro", "duration_minutes": 10, "sets": 4, "reps": "20 segundos trabajo / 40 descanso", "intensity": "alta controlada", "success_metric": "volver al centro sin cruzar pies", "coaching_cue": "aterrizar cuando el rival impacta"},
        ],
        "recovery": [
            {"name": "Tennis 10+ modificado: warm-up/cool-down", "duration_minutes": 10, "sets": 1, "reps": "movilidad dinámica + activación + descarga", "intensity": "baja", "success_metric": "dolor no aumenta durante la sesión", "coaching_cue": "preparar hombro, cadera, columna, rodilla y Aquiles"},
        ],
        "mental": [
            {"name": "Rutina de 12 segundos entre puntos", "duration_minutes": 8, "sets": 2, "reps": "10 puntos simulados", "intensity": "competitiva", "success_metric": "usar respiración + objetivo antes de cada punto", "coaching_cue": "atención en proceso, no en resultado"},
        ],
        "learning": [
            {"name": "Bloque deliberado de habilidad débil", "duration_minutes": 15, "sets": 3, "reps": "5 minutos por consigna", "intensity": "moderada", "success_metric": agents["learning"].get("evidence", {}).get("lowest_skill") or "habilidad prioritaria", "coaching_cue": "una métrica, una consigna, feedback inmediato"},
        ],
    }
    selected = list(drills.get(priority_key, drills["learning"]))
    if "dobles" in str(mode):
        selected.append({"name": "Dobles: saque + primera volea / cobertura", "duration_minutes": 12, "sets": 3, "reps": "8 puntos por lado", "intensity": "competitiva", "success_metric": "comunicación clara antes del punto y cobertura correcta", "coaching_cue": "cerrar ángulos, no mirar solo la pelota"})
    elif profile.get("is_beginner"):
        selected.append({"name": "Serve-rally-score progresivo", "duration_minutes": 12, "sets": 3, "reps": "puntos cooperativos a 7", "intensity": "baja-media", "success_metric": "mantener pelota en juego y contar puntos", "coaching_cue": "jugar, rally y puntuación antes de complejidad"})
    else:
        selected.append({"name": f"Punto condicionado para {level}", "duration_minutes": 12, "sets": 3, "reps": "6 puntos", "intensity": "competitiva", "success_metric": "ejecutar el patrón elegido en 4/6 puntos", "coaching_cue": "plan A claro y ajuste si el rival neutraliza"})
    return selected[:3]


def _session_plan(priority_key: str, priority_agent: Dict[str, Any], agents: Dict[str, Dict[str, Any]], profile: Dict[str, Any], injury_precautions: List[Dict[str, Any]]) -> Dict[str, Any]:
    high_risk = any(row.get("level") == "high" for row in injury_precautions)
    total_minutes = 45 if high_risk else (75 if profile.get("is_competitive") else 60)
    return {
        "total_minutes": total_minutes,
        "intensity": "baja-controlada" if high_risk else ("competitiva" if profile.get("is_competitive") else "moderada"),
        "blocks": [
            {"name": "Warm-up tenis específico", "minutes": 10, "goal": "movilidad dinámica, activación y progresión de baja a media intensidad"},
            {"name": "Bloque técnico prioritario", "minutes": 15 if high_risk else 20, "goal": priority_agent.get("recommendation")},
            {"name": "Bloque táctico/aplicación", "minutes": 10 if high_risk else 20, "goal": agents["tactical"].get("recommendation")},
            {"name": "Cool-down + registro", "minutes": 10, "goal": "bajar pulsaciones, movilidad suave y registrar métrica clave"},
        ],
        "progression_rule": "subir complejidad solo si la métrica de éxito supera 70% y no aumenta dolor/fatiga",
        "deload_rule": "si aparece dolor >3/10, sueño bajo o HRV bajo, reducir volumen 20-40% y priorizar técnica sin fatiga",
        "primary_agent": priority_key,
    }

def evaluate_tennis_intelligence(payload: Dict[str, Any] | None = None) -> TennisIntelligenceResult:
    data = _safe_dict(payload)
    message = _safe_text(data.get("message") or data.get("text"))
    message_norm = _normalize_text(message)
    player_profile = _safe_dict(data.get("player_profile"))
    profile_context = _profile_context(player_profile, message_norm)
    match_stats = _safe_dict(data.get("match_stats"))
    biomechanics = _safe_dict(data.get("biomechanics"))
    wellness = _safe_dict(data.get("wellness") or data.get("signals"))
    nutrition = _safe_dict(data.get("nutrition"))
    mental = _safe_dict(data.get("mental"))
    skills = _safe_dict(data.get("skills"))
    memory = _safe_dict(data.get("memory"))

    agents: Dict[str, Dict[str, Any]] = {}
    agents["biomechanics"] = _biomechanics_agent(message_norm, biomechanics)
    agents["tactical"] = _tactical_agent(message_norm, match_stats)
    agents["match_intelligence"] = _match_intelligence_agent(match_stats)
    agents["physical_performance"] = _physical_agent(wellness)
    agents["recovery"] = _recovery_agent(wellness)
    agents["nutrition"] = _nutrition_agent(nutrition)
    agents["mental"] = _mental_agent(message_norm, mental)
    agents["learning"] = _learning_agent(skills)
    agents["asa_memory"] = _asa_memory_agent(memory, message_norm)
    agents["qaf_entanglement"] = _entanglement_agent(agents)
    agents["qaf_prediction"] = _prediction_agent(agents)

    technical_gaps = _technical_gaps(message_norm, biomechanics, profile_context)
    injury_precautions = _injury_precautions(agents, biomechanics, wellness)

    ranked_agents = sorted(agents.items(), key=lambda item: float(item[1].get("confidence") or 0.0), reverse=True)
    priority_key, priority_agent = ranked_agents[0]
    secondary = [key for key, _ in ranked_agents[1:4]]
    recommended_drills = _recommended_drills(priority_key, agents, profile_context)
    session_plan = _session_plan(priority_key, priority_agent, agents, profile_context, injury_precautions)
    microcycle = [
        {"day": "Día 1", "focus": priority_agent["focus"], "block": priority_agent["recommendation"], "drill": recommended_drills[0]["name"] if recommended_drills else "bloque técnico"},
        {"day": "Día 2", "focus": agents["learning"]["focus"], "block": agents["learning"]["recommendation"], "drill": "Bloque deliberado de habilidad débil"},
        {"day": "Día 3", "focus": agents["tactical"]["focus"], "block": agents["tactical"]["recommendation"], "drill": "Punto condicionado táctico"},
    ]
    risk_flags: List[str] = []
    injury_risk = agents["qaf_prediction"]["evidence"].get("injury_risk")
    if isinstance(injury_risk, (int, float)) and float(injury_risk) >= 0.55:
        risk_flags.append("injury_risk_high")
    if agents["mental"]["evidence"].get("pressure_signal", 0.0) >= 0.62:
        risk_flags.append("competitive_pressure_high")
    if agents["recovery"]["evidence"].get("recovery_risk", 0.0) >= 0.55:
        risk_flags.append("recovery_priority")

    orchestrator = _agent_payload(
        "Tennis Coach Orchestrator",
        priority_agent["focus"],
        max(0.62, float(priority_agent.get("confidence") or 0.62)),
        "Coordinar el plan alrededor del foco de mayor impacto y validar datos faltantes antes de elevar complejidad.",
        {"primary_agent": priority_key, "secondary_agents": secondary},
    )

    output = {
        "contract_version": "tennis_intelligence_v1",
        "experience_id": "exp-014_tennis_intelligence",
        "service": "tennis_intelligence",
        "domain": "training",
        "orchestrator": orchestrator,
        "agents": agents,
        "priority_focus": priority_agent["focus"],
        "next_best_action": priority_agent["recommendation"],
        "risk_flags": risk_flags,
        "microcycle": microcycle,
        "session_plan": session_plan,
        "recommended_drills": recommended_drills,
        "technical_gaps": technical_gaps,
        "injury_precautions": injury_precautions,
        "metrics_to_track": ["first_serve_pct", "unforced_errors", "rally_length", "readiness", "pain_0_10", "drill_success_pct"],
        "coach_questions": [
            "¿Cuál es tu golpe prioritario y qué métrica quieres mejorar esta semana?",
            "¿Hay dolor en hombro, codo, muñeca, rodilla o Aquiles durante/después de jugar?",
            "¿Juegas más singles o dobles y en qué superficie compites?",
        ],
        "player_level": _safe_text(player_profile.get("level") or "recreativo/intermedio"),
        "player_context": profile_context,
        "source_architecture": "QAF Tennis Intelligence Team v2",
    }
    return TennisIntelligenceResult(payload=qualify_sports_result(output, data, "tennis"))


def render_professional_summary(result: Dict[str, Any]) -> str:
    data = _safe_dict(result)
    orchestrator = _safe_dict(data.get("orchestrator"))
    agents = _safe_dict(data.get("agents"))
    prediction = _safe_dict(agents.get("qaf_prediction"))
    prediction_evidence = _safe_dict(prediction.get("evidence"))
    risk_flags = data.get("risk_flags") if isinstance(data.get("risk_flags"), list) else []
    microcycle = data.get("microcycle") if isinstance(data.get("microcycle"), list) else []

    lines = [
        "🎾 **Tennis Intelligence activado**",
        "",
        f"**Foco prioritario:** {data.get('priority_focus') or orchestrator.get('focus') or 'evaluación integral'}.",
        f"**Siguiente mejor acción:** {data.get('next_best_action') or orchestrator.get('recommendation') or 'medir técnica, carga y estado mental antes de decidir'}",
        "",
        "**Lectura multiagente:**",
    ]
    for key in ("biomechanics", "tactical", "physical_performance", "recovery", "mental", "learning", "qaf_entanglement", "asa_memory"):
        agent = _safe_dict(agents.get(key))
        if agent:
            lines.append(f"- {agent.get('agent')}: {agent.get('focus')} → {agent.get('recommendation')}")
    lines.extend(["", prediction_summary(data)])
    if risk_flags:
        lines.append(f"**Alertas:** {', '.join(str(flag) for flag in risk_flags)}.")
    if microcycle:
        lines.append("")
        lines.append("**Microciclo recomendado:**")
        for block in microcycle[:3]:
            row = _safe_dict(block)
            drill = f" | Drill: {row.get('drill')}" if row.get('drill') else ""
            lines.append(f"- {row.get('day')}: {row.get('focus')} — {row.get('block')}{drill}")
    drills = data.get("recommended_drills") if isinstance(data.get("recommended_drills"), list) else []
    if drills:
        lines.append("")
        lines.append("**Drills accionables:**")
        for drill in drills[:3]:
            row = _safe_dict(drill)
            lines.append(f"- {row.get('name')} ({row.get('duration_minutes')} min): {row.get('success_metric')}")
    injury_precautions = data.get("injury_precautions") if isinstance(data.get("injury_precautions"), list) else []
    if injury_precautions:
        lines.append("")
        lines.append("**Precauciones de lesión:**")
        for item in injury_precautions[:3]:
            row = _safe_dict(item)
            lines.append(f"- {row.get('zone')} [{row.get('level')}]: {row.get('action')}")
    lines.append("")
    lines.append("Regla profesional: primero proteger salud y continuidad; luego optimizar técnica, táctica y aprendizaje.")
    return "\n".join(lines)

