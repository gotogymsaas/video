"""Pure football curriculum engine; storage and conversation belong to ExperienceTask."""
from dataclasses import dataclass
from .catalog import AGENTS, SERVICE_ID, VERSION
from .contracts import normalize_context
from .planner import solve

@dataclass(frozen=True)
class FootballResult:
    payload: dict


def evaluate_football_intelligence(data):
    context = normalize_context(data.get('football_context', data))
    key = context['specialist']
    primary = AGENTS[key]
    # Explicit role selection; no keyword inference of medical or psychological state.
    support = ('fc.referee_review' if primary.group == 'referee' else
               'fc.session_designer' if primary.group == 'staff' else 'fc.psychology_daily_life')
    selected_keys = list(dict.fromkeys((key, support)))
    previous = data.get('_previous_result') or {}
    previous_ids = [b.get('id') for b in (previous.get('session_plan') or {}).get('blocks', []) if isinstance(b,dict)]
    candidates, packets = [], {}
    for agent_key, spec in AGENTS.items():
        selected = agent_key in selected_keys
        packet = {'agent_key':agent_key, 'label':spec.label, 'schema_version':'football_insight_v1',
                  'execution_status':'executed' if selected else 'not_selected',
                  'reason':'explicit_specialist_or_support' if selected else 'outside_current_goal',
                  'observations':[], 'hypotheses':[], 'candidate_actions':[],
                  'missing_inputs':[], 'evidence_refs':[], 'model_version':VERSION}
        if selected:
            # These are design tasks, with no contact, maximal effort or body inference.
            definitions = (
                ('understand', 5, 'Comprender: '+spec.objective,
                 'Relaciona tu objetivo con esta pregunta: '+spec.observation),
                ('practice', 10 if context['level'] != 'principiante' else 8,
                 'Aplicar: '+spec.label, spec.practice),
                ('reflect', 5, 'Revisar y decidir',
                 'Escribe qué observaste, qué cambiarías y qué consultarías. '+spec.observation),
            )
            for kind, duration, title, instruction in definitions:
                item = {'id':agent_key+':'+kind,'agent_key':agent_key,'kind':kind,
                        'minutes':duration,'title':title,'instructions':instruction,
                        'physical_load':'none','source_ref':spec.source,
                        'metric':spec.observation}
                packet['candidate_actions'].append(item['id'])
                candidates.append(item)
            packet['observations'] = [{'kind':'self_report','metric':'declared_goal',
                                       'value':context['goal'],'source_ref':'task_input:football_context'}]
            packet['evidence_refs'] = [spec.source, 'task_input:football_context']
            packet['recommendation'] = spec.practice
        packets[agent_key] = packet
    blocks, diagnostics = solve(candidates, context['session_minutes'], key, previous_ids)
    # Always revalidate the delivered schedule independently of solver diagnostics.
    if (not blocks or sum(b['minutes'] for b in blocks) > context['session_minutes']
            or not any(b['agent_key'] == key for b in blocks)):
        raise ValueError('football_plan_infeasible')
    total = sum(b['minutes'] for b in blocks)
    limits = ['Propuesta educativa y de planificación; no prescribe carga física ni modifica tu plan aceptado.',
              'No analiza videos o medidas corporales ni emite diagnósticos, altas o decisiones arbitrales oficiales.',
              'El rol elegido no concede acceso a información de compañeros, jugadores o árbitros.']
    if primary.group == 'referee':
        limits.append('Material de estudio IFAB 2026/27: confirma reglamento y protocolos de tu competición antes de aplicarlo.')
    return FootballResult({
        'experience_id':SERVICE_ID,'schema_version':'football_result_v1','model_version':VERSION,
        'assessment_status':'educational_guidance','workflow_kind':context['mode'],
        'football_context':context,'priority_focus':primary.objective,'goal':context['goal'],
        'agents':packets,'selected_agents':selected_keys,
        'omitted_agents':[k for k in AGENTS if k not in selected_keys],
        'session_plan':{'status':'proposed','kind':'educational','total_minutes':total,
                        'available_minutes':context['session_minutes'],'blocks':blocks},
        'candidate_actions':candidates,'solver_diagnostics':diagnostics,
        'recommended_drills':[], 'risk_flags':[], 'plan_patch':None,
        'next_best_action':blocks[0]['instructions'],
        'data_quality':{'guidance_kind':'educational_guidance','defaults_are_measurements':False,
                        'prediction_basis':'not_performed'},
        'evidence_refs':sorted({AGENTS[k].source for k in selected_keys}),
        'continuity':{'previous_result_used':bool(previous_ids),
                      'feedback':context.get('previous_feedback',''),
                      'previous_activities':previous_ids},
        'limitations':limits,
    })


def render_professional_summary(result):
    context = result['football_context']
    label = AGENTS[context['specialist']].label
    lines = [f'**Fútbol · {label}**', f"Tu objetivo: {context['goal']}",
             f"Te propongo {result['session_plan']['total_minutes']} minutos de aprendizaje y planificación. Puedes aceptar, adaptar o pausar esta propuesta."]
    if result['continuity']['previous_result_used']:
        lines.append('Tu resultado anterior se tuvo en cuenta para reducir la repetición de actividades.')
    for index, block in enumerate(result['session_plan']['blocks'],1):
        lines.append(f"{index}. **{block['title']} ({block['minutes']} min).** {block['instructions']}\nQué observar: {block['metric']}")
    lines.append('Al terminar, cuéntame qué te resultó útil y qué necesitas ajustar.')
    lines.append('**Alcance:** '+' '.join(result['limitations']))
    lines.append('**Fuentes de consulta:**\n'+'\n'.join('- '+url for url in result['evidence_refs']))
    return '\n\n'.join(lines)

