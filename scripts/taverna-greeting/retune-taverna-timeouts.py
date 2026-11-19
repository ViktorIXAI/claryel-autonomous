"""Retune the taverna timeouts in /config/configuration.yaml (runs inside the HA container):

- the motion sensor hold that switches the LAMP off: 5 min -> 3 min after the last motion;
- a second template sensor with the same source but a 2 min hold, so the radio can stop earlier
  than the light (operator: music after 2 quiet minutes, light after 3).

Only prints which anchors were hit; never dumps the file (it holds loopback secrets).
"""
import shutil
import sys

CFG = "/config/configuration.yaml"
src = open(CFG).read()
shutil.copyfile(CFG, CFG + ".bak-timeouts-20261119")

SENSOR_OLD = '''      - name: "TAVERNA motion"
        unique_id: tavern_motion
        device_class: motion
        icon: mdi:motion-sensor
        state: "{{ is_state('input_boolean.tavern_motion_now', 'on') }}"
        delay_on: "00:00:01"
        delay_off: "00:05:00"
'''
SENSOR_NEW = '''      - name: "TAVERNA motion"
        unique_id: tavern_motion
        device_class: motion
        icon: mdi:motion-sensor
        state: "{{ is_state('input_boolean.tavern_motion_now', 'on') }}"
        delay_on: "00:00:01"
        delay_off: "00:03:00"
#      [EN] 2026-11-19: hold cut from 5 min to 3 min on the operator's request - the lamp goes
#      out 3 minutes after the last motion. The radio stops earlier, on tavern_motion_quiet.
      - name: "TAVERNA motion quiet"
        unique_id: tavern_motion_quiet
        device_class: motion
        icon: mdi:motion-sensor
        state: "{{ is_state('input_boolean.tavern_motion_now', 'on') }}"
        delay_on: "00:00:01"
        delay_off: "00:02:00"
'''
MUSIC_OLD = '''    mode: single
    triggers:
      - trigger: state
        entity_id: switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1
        to: "off"
    actions:
      - action: rest_command.taverna_greeting_stop
'''
MUSIC_NEW = '''    mode: single
    triggers:
      - trigger: state
        entity_id: binary_sensor.taverna_motion_quiet
        to: "off"
      - trigger: state
        entity_id: switch.taverna_taverna_basicr4_sonoff_1002bd4e01_1
        to: "off"
    actions:
      - action: rest_command.taverna_greeting_stop
'''
DESC_OLD = '''      Music ends with the lamp, so an unattended stream cannot keep playing.'''
DESC_NEW = '''      Music ends 2 minutes after the last motion (taverna_motion_quiet), and also whenever the
      lamp itself goes out, so an unattended stream cannot keep playing. The lamp itself stays
      lit for 3 quiet minutes (taverna_motion).'''
LIGHT_DESC_OLD = '''      Шаблонный сенсор tavern_motion держится включённым 5 минут после последнего движения;
      при его переходе в off свет выключается.'''
LIGHT_DESC_NEW = '''      Шаблонный сенсор tavern_motion держится включённым 3 минуты после последнего движения
      (с 2026-11-19, по указанию владельца); при его переходе в off свет выключается. Радио
      обрывается раньше - через 2 минуты, по сенсору taverna_motion_quiet.'''
COMMENT_OLD = '''# [EN] state = "is the camera seeing motion right now"; delay_off keeps it on for 5 minutes'''
COMMENT_NEW = '''# [EN] state = "is the camera seeing motion right now"; delay_off keeps it on for 3 minutes'''

out = src
hits = []
for name, old, new in (("lamp hold 5->3 min + quiet sensor", SENSOR_OLD, SENSOR_NEW),
                       ("music_off trigger on quiet sensor", MUSIC_OLD, MUSIC_NEW),
                       ("music_off description", DESC_OLD, DESC_NEW),
                       ("light automation description", LIGHT_DESC_OLD, LIGHT_DESC_NEW),
                       ("header comment", COMMENT_OLD, COMMENT_NEW)):
    if old in out:
        if out.count(old) != 1:
            sys.exit("anchor not unique: %s (%d hits)" % (name, out.count(old)))
        out = out.replace(old, new)
        hits.append(name)
    else:
        hits.append("MISSING ANCHOR: " + name)

if "tavern_motion_quiet" not in src:
    open(CFG, "w").write(out)
    print("written; anchors: " + ", ".join(hits))
else:
    print("quiet sensor already present, nothing written; anchors: " + ", ".join(hits))
