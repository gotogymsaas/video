"""Registered sports services reuse ExperienceTask; the 15-experience catalog stays stable."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
import math
import os
import re
import unicodedata
from typing import Any
from api.qaf_football_intelligence.catalog import AGENTS as FOOTBALL_AGENTS
from api.qaf_running_intelligence.contracts import AGENTS as RUNNING_AGENTS


@dataclass(frozen=True)
class SportsService:
    id: str
    sport: str
    label: str
    aliases: tuple[str, ...]
    description: str
    agent_keys: tuple[str, ...]

    @property
    def module(self) -> str:
        return f"api.qaf_{self.sport}_intelligence.engine"

    @property
    def legacy_key(self) -> str:
        return f"{self.sport}_intelligence_last"


SPORTS_SERVICES = {
    service.id: service for service in (
        SportsService("exp-014_tennis_intelligence", "tennis", "Entrenamiento de Tenis",
            ("tenis", "tennis", "tennis_coach"),
            "Técnica, táctica, rendimiento físico, recuperación, nutrición, mentalidad, aprendizaje y memoria deportiva.",
            ("biomechanics", "tactical", "match_intelligence", "physical_performance", "recovery", "nutrition", "mental", "learning", "qaf_entanglement", "asa_memory", "qaf_prediction")),
        SportsService("exp-015_swimming_intelligence", "swimming", "Entrenamiento de Natación",
            ("natacion", "swimming", "swimming_coach"),
            "Técnica de nado, respiración, resistencia, ritmo, seguridad, recuperación, nutrición, aprendizaje y memoria deportiva.",
            ("technique", "breathing", "endurance", "pace", "recovery", "safety", "nutrition", "learning", "asa_memory", "qaf_prediction")),
        SportsService("exp-016_cycling_intelligence", "cycling", "Entrenamiento de Ciclismo",
            ("ciclismo", "cycling", "cycling_coach", "bicicleta", "bici"),
            "Ajuste de bicicleta, potencia, resistencia, recuperación, nutrición, seguridad, aprendizaje y memoria deportiva.",
            ("bike_fit", "power", "endurance", "recovery", "nutrition", "safety", "learning", "qaf_entanglement", "asa_memory", "qaf_prediction")),
        SportsService("exp-017_running_intelligence", "running", "Entrenamiento de Running",
            ("running", "runing", "rining", "correr", "corredor", "running_coach"),
            "15 especialidades para revisar historial, recuperación, vida diaria y una sesión orientativa; medidas corporales opcionales con procedencia, sin predicción clínica ni análisis de vídeo.",
            tuple(RUNNING_AGENTS)),
        SportsService("exp-018_football_intelligence", "football", "Fútbol: aprendizaje y planificación",
            ("futbol", "football", "soccer", "football_coach"),
            "40 especialistas para entrenadores, asistentes, posiciones y arbitraje: aprendizaje y planificación contextual; sin análisis visual ni prescripción física automatizada.",
            tuple(FOOTBALL_AGENTS)),
    )
}


def normalize(value: Any) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", str(value or "").lower())
                   if unicodedata.category(c) != "Mn").strip()


def mentioned_services(message: str) -> list[SportsService]:
    text = normalize(message)
    return [s for s in SPORTS_SERVICES.values() if s.id in text or any(
        re.search(rf"\b{re.escape(alias)}\b", text) for alias in s.aliases)]


def sports_capability_request(message: str) -> bool:
    text = normalize(message)
    subject = bool(mentioned_services(text) or re.search(r"\b(deportes?|deportiv\w*|running|futbol)\b", text))
    inventory = bool(re.search(r"\b(tienes|tienen|hay|cuentas|cuentan|dispones|disponen|ofreces|ofrecen|que agentes|cuales agentes)\b", text))
    explanation = bool(re.search(r"\b(como funcionan?|para que sirven?|que hacen|que puede hacer|que puedes hacer)\b", text))
    specialist = bool(re.search(r"\b(agentes?|especialistas?|especiales?|exclusiv\w*|servicios?|entrenador\w*|coach)\b", text))
    platform_sports = bool(re.search(r"\b(tienes|tienen|cuentas|cuentan|dispones|disponen|ofreces|ofrecen|contigo|gotogym|plataforma)\b", text))
    return subject and ((inventory and (specialist or (platform_sports and re.search(r"\bdeportes?\b", text)))) or (explanation and specialist))


def sports_activation_id(data: dict) -> str:
    explicit = data.get('explicit_invocation')
    if isinstance(explicit,dict) and explicit.get('experience') in SPORTS_SERVICES:
        if (explicit.get('service') != 'training' or explicit.get('source') not in {'button','frontend_button','qaf_eig'}
                or (isinstance(data.get('service_intent'),dict) and data['service_intent'].get('experience') != explicit['experience'])):
            return ''
    invocation = data.get("service_intent") or data.get("explicit_invocation") or {}
    default_action = '' if data.get('service_intent') else 'start_new'
    if isinstance(invocation, dict) and invocation.get("action", default_action) in {"start_new", "start", "new_eval"}:
        eid = str(invocation.get("experience") or "")
        if eid in SPORTS_SERVICES:
            return eid
        if invocation.get("domain") == "training":
            agent = normalize(invocation.get("agent"))
            return next((s.id for s in SPORTS_SERVICES.values() if agent == f"{s.sport}_coach"), "")
    message = str(data.get("message") or "")
    from api.superagent.request_semantics import affirmative_request_text
    text = normalize(affirmative_request_text(message))
    if sports_capability_request(text) or not re.match(
        r"^(?:por favor\s+)?(?:activa(?:r)?|inicia(?:r)?|empieza|comienza|entrenemos|quiero (?:activar|iniciar|usar|empezar|entrenar))\b", text
    ):
        return ""
    services = mentioned_services(text)
    return services[0].id if len(services) == 1 else ""


def service_enabled(service):
    return os.environ.get(f'QAF_{service.sport.upper()}_ENABLED', 'true').lower() in {'1','true','yes'}


def sports_capture_key(service):
    return f'{service.sport}_context' if service.sport in {'football', 'running'} else 'sports_context'


def sports_capabilities() -> list[dict]:
    return [{"service_id": s.id, "sport": s.sport, "label": s.label,
             "description": s.description, "agent_count": len(s.agent_keys),
             "agent_keys": list(s.agent_keys), "implemented": True,
             "activation": "explicit_request", "execution": "experience_task",
             "source_of_truth": "api.sports_service_registry"} for s in SPORTS_SERVICES.values() if service_enabled(s)]


def render_sports_capabilities(message: str = "") -> str:
    text = normalize(message)
    lines = []
    lines.append("Tengo equipos especializados para tenis, natación y ciclismo. Estos son los servicios deportivos disponibles:")
    lines += [f"- **{s.label}:** {s.description}" for s in SPORTS_SERVICES.values() if service_enabled(s)]
    lines.append("Conversas conmigo y coordino el equipo del deporte que elijas. Primero revisamos tu objetivo, nivel, tiempo disponible y cómo te sientes; después recibes una sesión orientativa, ejercicios y métricas para dar seguimiento. Puedes pedirme ‘activa tenis’, ‘activa natación’, ‘activa ciclismo’.")
    if service_enabled(SPORTS_SERVICES["exp-018_football_intelligence"]):
        lines.append("Para fútbol, pide ‘activa fútbol’ y elige la especialidad en el formulario. Recibirás actividades educativas con fuentes y criterios de revisión.")
    if service_enabled(SPORTS_SERVICES['exp-017_running_intelligence']):
        lines.append('Para running, pide ‘activa running’. Revisaremos tu historial reciente, dolor, descanso y tiempo disponible antes de proponer una sesión. Los 15 módulos se ejecutan o se omiten con un motivo según los datos; no son 15 llamadas a un modelo.')
    return "\n\n".join(lines)


def sports_lifecycle_specs() -> dict:
    from api.experience_lifecycle_registry import ExperienceLifecycleSpec, _message_action
    return {s.id: ExperienceLifecycleSpec(
        id=s.id, label=s.label, enabled=service_enabled(s), scope="training", explicit_service="training",
        activation_contract={"requires_explicit_invocation": True, "service_kind": "sport"},
        start_action=_message_action(s.id, "Iniciar " + s.label, "training"),
        required_inputs=[sports_capture_key(s)], payload_key=f"{s.sport}_intelligence_request",
        ordered_steps=["activation", "collect_sports_context", "validate", "process", "persist", "deliver", "close"],
        result_key=f"qaf_{s.sport}_intelligence", persistence_key=s.legacy_key,
        processing_endpoint=f"qaf_{s.sport}_intelligence", backend_handler=f"qaf_{s.sport}_intelligence",
        frontend_handler="experience_task", folder="entrenamiento", tags=["deporte", s.sport],
        what_you_get=s.description, what_you_need=("especialidad, objetivo, nivel y tiempo de aprendizaje" if s.sport == "football" else "objetivo, nivel, tiempo disponible y estado de hoy"),
    ) for s in SPORTS_SERVICES.values()}


def specialist_spec(service_id: str):
    from api.experience_lifecycle_registry import EXPERIENCE_LIFECYCLE_REGISTRY
    from api.health_service_registry import health_lifecycle_specs
    return (EXPERIENCE_LIFECYCLE_REGISTRY.get(service_id) or sports_lifecycle_specs().get(service_id)
            or health_lifecycle_specs().get(service_id))


def sports_context_complete(value: Any) -> bool:
    if (not isinstance(value, dict) or not isinstance(value.get('level'),str) or not value['level'].strip()
            or not isinstance(value.get('goal'),str) or not value['goal'].strip()
            or isinstance(value.get('pain_0_10'),bool) or isinstance(value.get('session_minutes'),bool)):
        return False
    try:
        minutes, pain = float(value["session_minutes"]), float(value["pain_0_10"])
        return math.isfinite(minutes) and math.isfinite(pain) and 5 <= minutes <= 180 and 0 <= pain <= 10
    except (KeyError, TypeError, ValueError, OverflowError):
        return False


def update_sports_memory(state: dict, service_id: str, result: dict, updated_at: str) -> None:
    service = SPORTS_SERVICES[service_id]
    history_key = f"{service.sport}_intelligence_history"
    rows = [r for r in state.get(history_key, []) if isinstance(r, dict)] if isinstance(state.get(history_key), list) else []
    rows.append({"updated_at": updated_at, "focus": result.get("priority_focus"),
                 "risk_flags": result.get("risk_flags", []), "next_best_action": result.get("next_best_action")})
    state[history_key] = rows[-5:]
    state[service.legacy_key] = {"result": result, "updated_at": updated_at}


def persist_sports_result(user, result: dict, summary: str, *, input_context: dict | None = None) -> str:
    """Direct APIs publish canonical evidence atomically, without writing conversation state."""
    from uuid import uuid4
    from django.db import transaction
    from django.utils import timezone
    from api.models import User
    from api.experience_lifecycle_registry import ExperienceLifecycleService
    service_id = str(result.get("experience_id") or "")
    if service_id not in SPORTS_SERVICES:
        raise ValueError("sport_service_not_registered")
    run_id, updated_at = str(uuid4()), timezone.now().isoformat()
    with transaction.atomic():
        locked = User.objects.select_for_update().get(pk=user.pk)
        state = dict(locked.coach_state or {})
        buckets = dict(state.get("qaf_experiences") or {})
        bucket = dict(buckets.get(service_id) or {})
        entry = {"run_id": run_id, "result": result, "summary": summary, "saved_at": updated_at}
        bucket.update(latest_result=result, latest_summary=summary, latest_run_id=run_id, updated_at=updated_at,
                      history=(list(bucket.get("history") or []) + [entry])[-20:])
        if input_context:
            bucket["sports_context"] = input_context
        buckets[service_id] = bucket
        state["qaf_experiences"] = buckets
        update_sports_memory(state, service_id, result, updated_at)
        ExperienceLifecycleService(locked)._update_canonical_user_knowledge(
            state, experience_id=service_id, run_id=run_id, result=result, updated_at=updated_at,
            source="sports_endpoint_algorithm")
        locked.coach_state, locked.coach_state_updated_at = state, timezone.now()
        locked.save(update_fields=["coach_state", "coach_state_updated_at"])
    user.coach_state, user.coach_state_updated_at = locked.coach_state, locked.coach_state_updated_at
    return run_id

