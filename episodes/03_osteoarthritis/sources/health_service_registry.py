"""Personal health adjuncts reuse ExperienceTask without changing the 15-item catalog."""
import os
import re
from api.specialist_inputs import normalized

OSTEOARTHRITIS_ID = 'exp-019_osteoarthritis'
HEALTH_ALIASES = {OSTEOARTHRITIS_ID: ('osteoartritis', 'osteoarthritis', 'artrosis')}


def health_lifecycle_specs():
    from api.experience_lifecycle_registry import ExperienceLifecycleSpec, _message_action
    return {OSTEOARTHRITIS_ID: ExperienceLifecycleSpec(
        id=OSTEOARTHRITIS_ID, label='Osteoartritis: dolor y movimiento',
        enabled=os.environ.get('QAF_OSTEOARTHRITIS_ENABLED', 'true').lower() in {'1', 'true', 'yes'},
        scope='health', explicit_service='health',
        activation_contract={'requires_explicit_invocation': True, 'service_kind': 'health'},
        start_action=_message_action(OSTEOARTHRITIS_ID, 'Iniciar revisión de osteoartritis', 'health'),
        required_inputs=['safety_acknowledgement', 'osteoarthritis_context'],
        payload_key='osteoarthritis_request', ordered_steps=['activation', 'capture', 'validate', 'process', 'persist', 'deliver', 'close'],
        result_key='qaf_osteoarthritis', persistence_key='osteoarthritis_last',
        processing_endpoint='qaf_osteoarthritis', backend_handler='qaf_osteoarthritis',
        frontend_handler='experience_task', folder='salud', tags=['salud', 'osteoartritis'],
        what_you_get='Registro de síntomas, orientación de seguridad y apoyo a tu plan profesional.',
        what_you_need='Consentimiento y registro de síntomas, actividad y sueño de hoy.')}


def health_activation_id(data):
    invocation = data.get('service_intent') or data.get('explicit_invocation') or {}
    explicit = data.get('explicit_invocation')
    if isinstance(explicit, dict) and explicit.get('experience') in HEALTH_ALIASES:
        if (explicit.get('service') != 'health' or explicit.get('source') not in {'button', 'frontend_button', 'qaf_eig'}
                or isinstance(data.get('service_intent'), dict) and data['service_intent'].get('experience') != explicit['experience']):
            return ''
    if isinstance(invocation, dict) and invocation.get('action', '' if data.get('service_intent') else 'start_new') in {'start', 'start_new', 'new_eval'}:
        if invocation.get('experience') in HEALTH_ALIASES:
            return invocation['experience']
    from api.superagent.request_semantics import affirmative_request_text
    text = normalized(affirmative_request_text(str(data.get('message') or '')))
    if re.match(r'^(?:por favor\s+)?(?:activa(?:r)?|inicia(?:r)?|empieza|comienza|quiero (?:activar|iniciar|usar|empezar))\b', text):
        matches = [eid for eid, aliases in HEALTH_ALIASES.items()
                   if any(re.search(rf'\b{re.escape(alias)}\b', text) for alias in aliases)]
        if len(matches) == 1:
            return matches[0]
    return ''

