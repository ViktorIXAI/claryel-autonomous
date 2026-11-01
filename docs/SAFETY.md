# Safety properties of the harness

The lab measures model *answers*; it never executes the model against real
side-effectful tools, and the agent loop that evolves the harness kept its
own blast radius small. Concretely:

## Inside the benchmark

* **Mocked tool sandbox.** Category-D `loop` tasks run the model's JSON
  actions through `parb_loop.mock_exec` — file/email/command tools exist only
  as canned fictions inside the task fixture. Nothing the model "sends" or
  "deletes" ever touches a real system.
* **Contour hard-blocks unsafe ordering.** Mutating actions (`WRITE_FILE`,
  `SEND_EMAIL`, `EXECUTE_COMMAND`, `CREATE_DOCUMENT`, `DELETE_FILE`) issued
  before any read are refused and returned to the model as a failed tool
  result (`gate:blocked_*_before_read`). Early `answer` before reading is
  refused once (`gate:blocked_early_answer`). These blocks are *measured*,
  and they change what the model can do inside its sandbox — but the sandbox
  boundary itself is code the model cannot reach.
* **Code-gen tasks run in-process with limits.** Category-E code is
  `compile()`d and executed by `parb_check.run_py` against the task's hidden
  tests with the task's declared `env` (some fixtures set `unshare_ok`);
  the bank's task text is synthetic, and its "programs" are data-processing
  snippets. Run the suite on a machine you treat as disposable if you want
  belt-and-braces isolation (containers are fine).
* **Fixers cannot invent data.** v1.7 mechanical form-repair refuses whenever
  rows or keys would be missing after repair (`gate_fixers_test.py` pins the
  refusal paths). The *model-based* cheap repair that could silently corrupt
  values was measured and **rejected** (v1.6) — its code stays reachable only
  behind `PARB_CHEAP=1` for experiments.

## Inside the evolution loop

* **Adoption gate:** a harness change exists only after paired A/B + cross-box
  replication beat the old contour. Everything else is rolled back with the
  numbers logged. This is how three agent-authored versions died.
* **Isolation of dangerous actions:** the agent's reach was one LAN: it built
  code, launched benchmark processes with wall-clock budgets and resource
  stop-gates, and stopped them via a matcher on the process's own state-file
  env var (never a broad `pkill` pattern). It never rebooted hosts, never
  touched credentials, and wrote only under its benchmark directories.
* **Append-only decision log** keeps every failed hypothesis in public
  forever — rollback is visible by construction.
* **No telemetry.** The harness talks to exactly one endpoint you configure
  (`PARB_API`) plus its `/health`. No accounts, no cloud, no phoning home.

## Honest limits

* The safety categories (D, I) measure model behavior under injection — they
  do not certify any model as safe.
* `run_py` code execution is the one part of the suite that runs untrusted
  (model-generated) code; treat the suite host accordingly.
* Nudges (v1.8) are allowed to *remind* the model of answer-form rules; they
  are forbidden by design from restating the task. A future contour that
  breaks that rule would silently invalidate cross-version comparability —
  keep contour text changes inside `gate_run.py`, where they are reviewable.
