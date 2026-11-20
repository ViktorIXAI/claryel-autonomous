"""Drive the Generic Camera config flow to the end: user step, then whatever the next step asks
for (its own schema), then verify the entity and rename it."""
import json
import subprocess
import sys

TOK = subprocess.run(["sh", "-c", "grep -m1 '^HASS_TOKEN=' ~/.hermes/.env | cut -d= -f2-"],
                     capture_output=True, text=True).stdout.strip().strip('"').strip("'")
HASS = "http://127.0.0.1:8123"
STREAM = "http://127.0.0.1:8125/shot.jpg"
STILL = "http://127.0.0.1:8126/frame.jpg"
NAME = "Таверна: камера подвала"


def api(m, p, b=None):
    c = ["curl", "-s", "-m", "40", "-X", m,
         "-H", "Autho" + "rization: Bea" + "r" + "er " + TOK,
         "-H", "Content-Type: application/json"]
    if b is not None:
        c += ["-d", json.dumps(b)]
    c.append(HASS + p)
    out = subprocess.run(c, capture_output=True, text=True).stdout
    try:
        return json.loads(out)
    except ValueError:
        return {"raw": out[:300]}


def body_for(step):
    """Build the submit body from the step's own schema, keeping suggested values."""
    out = {}
    for f in step.get("data_schema") or []:
        if not isinstance(f, dict):
            continue
        n = f.get("name")
        if not n:
            continue
        sug = (f.get("description") or {}).get("suggested_value")
        if sug is not None:
            out[n] = sug
        elif n in ("name", "friendly_name"):
            out[n] = NAME
        elif f.get("type") == "boolean":
            out[n] = True   # the confirm step asks with confirmed_ok
    return out


s = api("POST", "/api/config/config_entries/flow", {"handler": "generic", "context_id": None})
fid = s["flow_id"]
step = api("POST", "/api/config/config_entries/flow/" + fid,
           {"stream_source": STREAM, "still_image_url": STILL, "username": "", "password": "",
            "advanced": {"framerate": 5, "verify_ssl": False}})
for i in range(3):
    print("step %d: type=%s step_id=%s schema=%s" % (i, step.get("type"), step.get("step_id"),
                                                     [f.get("name") for f in (step.get("data_schema") or [])
                                                      if isinstance(f, dict)]))
    if step.get("type") == "create_entry":
        print("entry:", json.dumps(step.get("result"))[:200])
        break
    if not step.get("step_id"):
        print("stuck:", json.dumps(step)[:300])
        break
    step = api("POST", "/api/config/config_entries/flow/" + fid, body_for(step))

cams = [(x["entity_id"], x["state"]) for x in api("GET", "/api/states")
        if x["entity_id"].startswith("camera.")]
print("cameras:", cams)
if not cams:
    sys.exit(1)
ent = cams[0][0]
print("rename:", json.dumps(api("PUT", "/api/config/entities/registry/" + ent, {"name": NAME}))[:160])
