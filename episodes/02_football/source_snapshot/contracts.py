"""Strict bounded capture: no supplied identity, measurements or result authority."""
import math
from .catalog import AGENTS, LABEL_TO_KEY

MODES = ('Aprendizaje individual', 'Preparar una sesión', 'Formación arbitral')
FIELDS = {'specialist','mode','goal','session_minutes','level','context','previous_feedback'}

def normalize_context(value):
    if not isinstance(value, dict):
        raise ValueError('football_context_required')
    # Refuse forged result/third-party material instead of silently consuming it.
    if set(value) - FIELDS:
        raise ValueError('football_unknown_fields')
    result = dict(value)
    key = LABEL_TO_KEY.get(result.get('specialist'), result.get('specialist'))
    if key not in AGENTS:
        raise ValueError('football_specialist_required')
    result['specialist'] = key
    if result.get('mode') not in MODES:
        raise ValueError('football_mode_required')
    if result.get('level') not in ('principiante','intermedio','competitivo'):
        raise ValueError('football_level_required')
    goal = result.get('goal')
    if not isinstance(goal, str) or not 3 <= len(goal.strip()) <= 500:
        raise ValueError('football_goal_required')
    result['goal'] = goal.strip()
    minutes = result.get('session_minutes')
    if isinstance(minutes, bool):
        raise ValueError('football_time_invalid')
    try:
        minutes = float(minutes)
    except (TypeError, ValueError, OverflowError):
        raise ValueError('football_time_invalid') from None
    if not math.isfinite(minutes) or not 5 <= minutes <= 60 or minutes != int(minutes):
        raise ValueError('football_time_invalid')
    result['session_minutes'] = int(minutes)
    for field in ('context','previous_feedback'):
        text = result.get(field, '')
        if not isinstance(text, str) or len(text) > 1500:
            raise ValueError('football_text_invalid')
        result[field] = text.strip()
    # An educational mode is not permission to access team members or health.
    if result['mode'] == 'Formación arbitral' and AGENTS[key].group != 'referee':
        raise ValueError('football_referee_specialist_required')
    return result

def context_complete(value):
    try:
        normalize_context(value)
        return True
    except (ValueError, TypeError):
        return False

