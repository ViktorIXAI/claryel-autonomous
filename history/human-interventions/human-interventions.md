# Human interventions — recorded completely

What the human actually did across the whole chain (2026-10-30 → 11-01):

1. **Set the goal** (Human-directed): benchmark this local model; build a
   repeatable suite.
2. **Standing rules** (paraphrase; RU originals in operator notes):
   - never stop when idle — continue the measure→diagnose→version→compare loop;
   - reports to a human: verdict first ("fine / middling / bad"), numbers
     only where not fine; alerts only on events;
   - don't reboot hosts; don't touch credentials; dangerous ops stay isolated;
   - software touching system Python goes into containers, not sudo.
3. **Infrastructure ownership**: machines, power, network — the agent never
   controlled these; no host was rebooted, no config changed, by this chain.
4. **Morning report reviews** (human read; no veto recorded because the
   agent had already rejected the weak versions — the adoption gate was
   asymmetric by design: hard to adopt, easy to reject).
5. **Publication decision** (2026-11-01, this repo): human commissioned the
   publication pass; human chose account, visibility and what stays private
   (agent session transcripts withheld — documented in `docs/limitations.md`).

What the human did **not** do: write contour code, edit validators, choose
version verdicts, or override an agent rejection. There is no recorded
instance of any of these. If one had occurred it would live here — its
absence is a claim we can support with session logs (attribution level:
session, see limitations).
