from api.specialist_inputs import number, text, choice, yes_no

SERVICE_ID = 'exp-019_osteoarthritis'
VERSION = 'qaf_osteo_rules_v1'


def normalize_context(value):
    if not isinstance(value, dict):
        raise ValueError('osteoarthritis_context')
    allowed = {'goal', 'joint', 'pain_0_10', 'pain_duration_days', 'morning_stiffness_minutes',
               'sleep_hours', 'activity_minutes', 'trigger_note', 'professional_plan_note', 'diagnosis_confirmed',
               'hot_swollen_joint', 'fever_or_unwell', 'unable_to_bear_weight', 'recent_injury', 'new_numbness',
               'worsening', 'daily_life_affected'}
    if set(value) - allowed:
        raise ValueError('unexpected_osteoarthritis_input')
    result = {'goal': text(value, 'goal'),
              'joint': choice(value, 'joint', {'rodilla', 'cadera', 'mano', 'otra'}),
              'pain_0_10': number(value, 'pain_0_10', 0, 10),
              'pain_duration_days': number(value, 'pain_duration_days', 0, 36500),
              'morning_stiffness_minutes': number(value, 'morning_stiffness_minutes', 0, 1440),
              'sleep_hours': number(value, 'sleep_hours', 0, 24),
              'activity_minutes': number(value, 'activity_minutes', 0, 1440),
              'trigger_note': text(value, 'trigger_note', optional=True),
              'professional_plan_note': text(value, 'professional_plan_note', optional=True)}
    for key in ('diagnosis_confirmed', 'hot_swollen_joint', 'fever_or_unwell', 'unable_to_bear_weight',
                'recent_injury', 'new_numbness', 'worsening', 'daily_life_affected'):
        result[key] = yes_no(value, key)
    return result


def context_complete(value):
    try:
        normalize_context(value)
        return True
    except ValueError:
        return False

