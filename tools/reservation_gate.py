"""Fail-closed access authorization, outside the frozen predictive model."""
import json
import re
import unicodedata
from pathlib import Path

POLICY = Path(__file__).resolve().parents[1] / 'data/access/reservations.json'
REQUIRED_RESERVED = {'italy_2023', 'hungary_2024', 'bahrain_2025', 'russia_2021', 'netherlands_2023', 'canada_2024'}
PURPOSES = {'evaluation', 'archive', 'geometry', 'adapter', 'prior'}
SESSIONS = {'R': 'R', 'RACE': 'R', 'Q': 'Q', 'QUALIFYING': 'Q', 'FP1': 'FP1', 'PRACTICE1': 'FP1', 'FP2': 'FP2', 'PRACTICE2': 'FP2', 'FP3': 'FP3', 'PRACTICE3': 'FP3'}

class AccessDenied(ValueError):
    pass

def normalize(value):
    if not isinstance(value, str) or not value.strip():
        raise AccessDenied('Nonempty canonical identity required')
    value = unicodedata.normalize('NFKD', value).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'[^a-z0-9]', '', value)

def read_policy(path=None):
    try:
        policy = json.loads(Path(path or POLICY).read_text(encoding='utf-8'))
        if set(policy) != {'schema_version', 'reserved', 'allowed'} or type(policy['schema_version']) is not int or policy['schema_version'] != 1:
            raise ValueError('Unsupported policy schema')
        seen, reserved = set(), set()
        aliases, rounds = set(), set()
        for section in ('reserved', 'allowed'):
            if not isinstance(policy[section], list):
                raise ValueError('Policy entries must be lists')
            for e in policy[section]:
                if set(e) != {'key', 'year', 'event', 'round', 'aliases', 'purposes'}:
                    raise ValueError('Malformed policy entry')
                if type(e['year']) is not int or type(e['round']) is not int or e['round'] < 1:
                    raise ValueError('Malformed year/round')
                if not isinstance(e['aliases'], list) or not isinstance(e['purposes'], list):
                    raise ValueError('Malformed aliases/purposes')
                if not set(e['purposes']) <= PURPOSES or (section == 'reserved' and e['purposes']) or (section == 'allowed' and not e['purposes']):
                    raise ValueError('Malformed permission')
                if e['key'] != e['event'].lower().replace(' ', '_') + '_' + str(e['year']):
                    raise ValueError('Noncanonical key')
                if e['key'] in seen or (e['year'], e['round']) in rounds:
                    raise ValueError('Duplicate identity')
                seen.add(e['key']); rounds.add((e['year'], e['round']))
                for a in {normalize(e['key']), normalize(e['event']), *map(normalize, e['aliases'])}:
                    if (e['year'], a) in aliases:
                        raise ValueError('Ambiguous alias')
                    aliases.add((e['year'], a))
                if section == 'reserved': reserved.add(e['key'])
        if reserved != REQUIRED_RESERVED:
            raise ValueError('Reservation set incomplete or changed without gate revision')
        return policy
    except (OSError, ValueError, TypeError, KeyError) as exc:
        raise AccessDenied(f'Reservation policy unavailable or malformed: {exc}') from exc

def authorize(year=None, event=None, *, key=None, purpose, session='R', policy_path=None):
    """Validate before touching a session, network or race cache. No override flag."""
    policy = read_policy(policy_path)
    if purpose not in PURPOSES:
        raise AccessDenied('Unknown access purpose')
    if key is not None:
        if year is not None or event is not None:
            raise AccessDenied('Use key or year/event, not both')
        identity = normalize(key)
        matches = [(section, e) for section in ('reserved', 'allowed') for e in policy[section] if normalize(e['key']) == identity]
    else:
        if type(year) is not int or isinstance(event, bool):
            raise AccessDenied('Explicit integer season required')
        matches = [(section, e) for section in ('reserved', 'allowed') for e in policy[section]
                   if e['year'] == year and ((type(event) is int and e['round'] == event) or
                       (isinstance(event, str) and normalize(event) in {normalize(e['event']), normalize(e['key']), *map(normalize, e['aliases'])}))]
    if len(matches) != 1 or matches[0][0] == 'reserved':
        raise AccessDenied('Reserved, unknown or ambiguous race: access denied before session/cache access')
    entry = matches[0][1]
    token = normalize(session).upper()
    if token not in SESSIONS or purpose not in entry['purposes']:
        raise AccessDenied('Session or purpose not authorized')
    canonical_session = SESSIONS[token]
    if purpose == 'geometry' and canonical_session not in {'Q', 'FP1', 'FP2', 'FP3'}:
        raise AccessDenied('Geometry requires a pre-race session from an evaluated weekend')
    return {**entry, 'session': canonical_session}

def guarded_session(year, event, *, purpose, session='R', cache_dir, offline=False):
    """The common gate precedes even FastF1 import and cache-directory creation."""
    entry = authorize(year, event, purpose=purpose, session=session)
    import fastf1
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))
    fastf1.Cache.offline_mode(offline)
    return fastf1.get_session(entry['year'], entry['event'], entry['session'])

def archive_path(path, *, purpose='archive'):
    path = Path(path)
    # Archive paths must declare identity before their contents are read.
    authorize(key=path.parent.name, purpose=purpose)
    return path
