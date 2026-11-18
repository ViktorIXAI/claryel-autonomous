#!/usr/bin/env python3
# Does HA record a fresh timestamp when the hook re-posts input_boolean.turn_on on an
# already-on entity? That decides how the watchdog detects a lost Motion 'end' event.
import json, subprocess, time

T = open('/home/viktor/.config/motion/hass-token').read().strip()
HA = 'http://127.0.0.1:8123'
BOOL = 'input_boolean.tavern_motion_now'

def req(path, data=None):
    cmd = ['curl', '-s', '-m', '8', '-H', f'Authorization: Bearer {T}']
    if data is not None:
        cmd += ['-X', 'POST', '-H', 'Content-Type: application/json', '-d', json.dumps(data),
                f'{HA}/api/services/{path}']
    else:
        cmd.append(f'{HA}/api/{path}')
    return subprocess.run(cmd, capture_output=True, text=True).stdout

states = json.loads(req('states'))
autos = [s['entity_id'] for s in states if s['entity_id'].startswith('automation.') and 'tavern' in s['entity_id']]
print('tavern automations:', autos)

on_auto = [a for a in autos if 'dvizhenie' in a or 'vkliuch' in a] or autos[:1]
print('disabling (for the test):', on_auto)
for a in on_auto:
    req(f'automation/turn_off', {'entity_id': a})

def snap(tag):
    d = json.loads(req(f'sates'.replace('sates', f'states/{BOOL}')))
    st = d['state']
    print(f'{tag}: state={st} last_changed={d.get("last_changed")} last_updated={d.get("last_updated")} last_reported={d.get("last_reported")}')
    return d

req('input_boolean/turn_on', {'entity_id': BOOL})
a = snap('after first turn_on ')
time.sleep(20)
req('input_boolean/turn_on', {'entity_id': BOOL})
b = snap('after re-post (20 s) ')

same_state = a['state'] == b['state'] == 'on'
print('state stayed on:', same_state)
print('last_changed moved:', a['last_changed'] != b['last_changed'])
print('last_updated moved:', a['last_updated'] != b['last_updated'])
print('last_reported moved:', a.get('last_reported') != b.get('last_reported'))

req('input_boolean/turn_off', {'entity_id': BOOL})
for a_ in on_auto:
    req(f'automation/turn_on', {'entity_id': a_})
print('latch cleared, automations re-enabled:', autos)
