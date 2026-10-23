"""QAF-OSTEO rules: source-backed routing, descriptive records, no diagnosis."""
from dataclasses import dataclass
from .contracts import SERVICE_ID, VERSION, normalize_context

PAIN_SOURCE = 'https://www.nhs.uk/symptoms/joint-pain/'
SUPPORT_SOURCE = 'https://www.nhs.uk/conditions/osteoarthritis/treatment/'


@dataclass(frozen=True)
class OsteoarthritisResult:
    payload: dict


def qaf_osteo_rr(c):
    """Safety routing precedes coaching; never infer a diagnosis from a pain score."""
    if c['unable_to_bear_weight'] or c['recent_injury'] and (c['new_numbness'] or c['pain_0_10'] >= 8):
        return 'urgent_medical_attention', ['unable_to_bear_weight_or_severe_injury']
    if c['hot_swollen_joint'] or c['fever_or_unwell'] or c['new_numbness']:
        return 'urgent_medical_attention', ['hot_joint_or_systemic_or_neurologic_symptoms']
    if (c['recent_injury'] or c['worsening'] or c['daily_life_affected'] or not c['diagnosis_confirmed'] or c['pain_0_10'] >= 7
            or c['morning_stiffness_minutes'] > 30):
        return 'professional_review', ['needs_professional_assessment']
    return 'continue_coaching', []


def qaf_mob(c, route):
    if route != 'continue_coaching':
        return {'status': 'withheld', 'exercise_prescribed': False,
                'action': 'No inicies ni aumentes ejercicios con estas señales; primero solicita valoración profesional.'}
    if c['professional_plan_note']:
        return {'status': 'support_existing_plan', 'exercise_prescribed': False,
                'action': 'Sigue los límites de tu plan profesional. Registra actividad y síntomas; consulta antes de cambiarlo.'}
    return {'status': 'education_only', 'exercise_prescribed': False,
            'action': 'El movimiento y el fortalecimiento adaptados pueden ayudar. Pide a tu médico o fisioterapeuta un plan ajustado a tu articulación y tolerancia.'}


def qaf_pain_map(c, history):
    # Records remain descriptive: one coincidence never becomes a causal trigger.
    rows = []
    for row in history[-29:]:
        result = row.get('result') if isinstance(row, dict) else None
        observation = (result or {}).get('check_in') if isinstance(result, dict) else None
        if (isinstance(observation, dict) and observation.get('joint') == c['joint']
                and isinstance(observation.get('pain_0_10'), (float, int))):
            rows.append({'saved_at': row.get('saved_at'), 'pain_0_10': observation['pain_0_10'],
                         'trigger_note': observation.get('trigger_note', '')})
    previous = rows[-1]['pain_0_10'] if rows else None
    return {'status': 'descriptive_only', 'previous_records': len(rows),
            'pain_change_since_previous': c['pain_0_10'] - previous if previous is not None else None,
            'causal_trigger': None, 'flare_prediction': None,
            'note': 'Las coincidencias declaradas no demuestran causas ni predicen brotes.'}


def evaluate_osteoarthritis(data):
    c = normalize_context(data.get('osteoarthritis_context'))
    route, flags = qaf_osteo_rr(c)
    mobility = qaf_mob(c, route)
    pain_map = qaf_pain_map(c, data.get('_history') or [])
    nutrition = {'status': 'refer_to_primary_nutrition_service', 'new_diet_or_supplements': False,
                 'action': 'Si quieres revisar tu alimentación, usa tu plan nutricional y el servicio de nutrición; este registro no prescribe suplementos ni una dieta para tratar artrosis.'}
    next_action = ('Busca atención médica urgente. Si no puedes apoyar la articulación, hubo una lesión grave o pierdes sensibilidad, acude a urgencias.'
                   if route == 'urgent_medical_attention' else
                   'Solicita revisión con tu médico o fisioterapeuta por las señales registradas.'
                   if route == 'professional_review' else mobility['action'])
    limits = ['Acompañamiento educativo y registro autoinformado; no confirma artrosis ni sustituye evaluación médica.',
              'Sin cambios de medicación, suplementos, diagnóstico, predicción de brotes ni programa automático de rehabilitación.',
              'La escala de dolor es numérica autoinformada; no es WOMAC, KOOS ni una medida de daño articular.',
              'Los límites numéricos de seguridad son reglas prudentes del producto, no un clasificador clínico validado.']
    algorithms = {
        'QAF-OSTEO-RR': {'route': route, 'risk_flags': flags, 'source_refs': [PAIN_SOURCE]},
        'QAF-MOB': {**mobility, 'source_refs': [SUPPORT_SOURCE]},
        'QAF-ANTI': nutrition,
        'QAF-PAIN-MAP': pain_map,
        'QAF-CCC': {'status': 'evidence_only', 'semantic_writer': 'existing_svmca_reducer',
                    'action': 'Ofrecer estos registros al Coach; no escribir estado conversacional ni enviar recordatorios.'},
    }
    return OsteoarthritisResult({'experience_id': SERVICE_ID, 'schema_version': 'osteoarthritis_result_v1',
        'model_version': VERSION, 'assessment_status': route, 'goal': c['goal'],
        'priority_focus': 'Seguridad, dolor y movimiento en tu vida diaria', 'check_in': c,
        'reading': 'Registro de dolor y actividad con orientación según las señales que declaraste.',
        'algorithms': algorithms, 'selected_agents': list(algorithms),
        'session_plan': None, 'plan_patch': None, 'risk_flags': flags,
        'next_best_action': next_action, 'limitations': limits,
        'data_quality': {'source': 'self_report', 'diagnosis_inferred': False, 'prediction_basis': 'not_performed'},
        'evidence_refs': [PAIN_SOURCE, SUPPORT_SOURCE]})


def render_professional_summary(result):
    c = result['check_in']
    lines = ['**Osteoartritis · dolor y movimiento**',
             f"Tu objetivo: {c['goal']}. Registro de {c['joint']}: dolor declarado {c['pain_0_10']:g}/10; actividad {c['activity_minutes']:g} min.",
             result['next_best_action']]
    change = result['algorithms']['QAF-PAIN-MAP']['pain_change_since_previous']
    if change is not None:
        lines.append(f'Diferencia frente al registro anterior: {change:+g} puntos de dolor. Esta comparación no identifica la causa ni mide el daño articular.')
    if result['assessment_status'] == 'continue_coaching':
        lines.append('Para tu siguiente registro, anota cómo te fue con tu plan habitual, qué actividad realizaste y cómo dormiste. Puedes compartir el registro con tu profesional.')
    lines.append('**Alcance:** ' + ' '.join(result['limitations']))
    return '\n\n'.join(lines)

