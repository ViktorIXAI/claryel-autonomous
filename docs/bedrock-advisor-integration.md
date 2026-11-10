# Amazon Bedrock / Claude Fable 5.2 advisor lane

Status: **wired on the AWS side, model access still gated**. Written 2026-11-10 after an
infrastructure pass. The dated section at the end of this file (same day, account pass through
CloudShell) supersedes the "nothing was applied" framing of the paragraph below: an IAM user, a
least-privilege policy and one access key in the Hermes profile env file now exist, and real
invoke attempts were made — they all stop at the Anthropic agreement gate, so no model output
has been produced and no percentage is quotable.
Nothing in this document was applied to the running brain: no credentials, no
`.env` edit, no `config.yaml` change, no LiteLLM route change, no Bedrock API
call, no gateway restart. The only state change made on the controller host is
the declared PM extra `bedrock` (boto3), which is inert until a key exists.

## What was verified on this host (2026-11-10, real commands)

| Check | Result |
|---|---|
| `hermes pm install --extra bedrock` | ok, receipt `feature_list` now contains `bedrock`, boto3 1.43.115 |
| environment selected for **new** Hermes processes | `…/environments/208adc8c…/venv` — has boto3 |
| environment the **running gateway** uses (started 03:03) | `…/environments/e7dc190a…/venv` — no boto3 → needs a restart |
| `is_anthropic_bedrock_model("global.anthropic.claude-fable-5-2")` | `True` (Hermes picks the Anthropic-on-Bedrock path) |
| `bedrock_model_routable_from_region(…, us-east-1 / us-west-2 / eu-west-1)` | `True` for all three; geo prefixes `us.` / `eu.` / `global.` |
| `has_aws_credentials()` | `False` — no `~/.aws`, no `AWS_*` in the environment |
| TLS egress `bedrock-runtime.<region>.amazonaws.com` | HTTP 404 from AWS (path open, unauthenticated): us-east-1 0.39 s, us-west-2 0.56 s, eu-west-1 0.22 s |
| effort on the wire | `_claude_converse_reasoning()` emits `{"thinking": {"type": "adaptive", "display": "summarized"}, "output_config": {"effort": "high"}}` inside `additionalModelRequestFields` |

## Vendor facts that change the requested configuration

Sources: AWS Bedrock model card for Claude Fable 5.2, AWS ML blog post
"Introducing Claude Fable 5.2 on AWS", Amazon Bedrock data-retention page,
Anthropic model card. Checked 2026-11-10.

1. **Model IDs.** Base `anthropic.claude-fable-5-2`, US Geo CRIS
   `us.anthropic.claude-fable-5-2`, Global CRIS
   `global.anthropic.claude-fable-5-2`. The model is offered through Geo and
   Global inference profiles; the requested `global.` ID is valid. Model access
   belongs to AWS Marketplace product `prod-m733do2vrmi3o`, which has to be
   enabled in the account and region first.
2. **Data retention is mandatory, not optional.** Claude Fable 5, 5.1 and 5.2
   on Bedrock require human review: the account or project must explicitly be
   set to `aws_review` (or the legacy `provider_data_share`) **before these
   models can be invoked at all**. Prompts and completions are retained inside
   the AWS boundary for up to 30 days and may be reviewed by AWS. Content is not
   shared with Anthropic. There is no per-call opt-out. This is an
   account-level governance decision and the main blocker in this task.
3. **Sampling is constrained.** `temperature` must be `1.0` or unset, `top_p`
   must be `0.99` or unset, the two cannot be sent together, `top_k` is not
   supported. Our public benchmark legs send `temperature=0.7` and contour legs
   add `chat_template_kwargs.enable_thinking`, so a Fable arm has to strip both
   or every request is rejected.
4. **Adaptive thinking is always on** and the API default effort is already
   `high`. Asking for `effort: "high"` is a guarantee, not a boost; the usable
   lever is *lowering* effort (`low` / `medium`) for the cheap lane. `max_tokens`
   1200 — the shape of every published public arm — truncates a thinking model;
   a Fable arm needs the same care the GPQA contour arm needed after the
   shape fix.
5. **Preserved thinking.** Thinking blocks are bound to the model and the exact
   conversation prefix; replaying them against a changed prefix returns 400.
   The Hermes Converse adapter already seals and strips redacted reasoning
   blocks for this case (`agent/bedrock_adapter.py`, redacted-reasoning
   recovery), so the risk is handled on our side.
6. **Prompt caching.** Minimum cached prefix 512 tokens, at most 4 checkpoints,
   TTL 5 minutes or 1 hour. Prices per MTok: input $8.00, output $40.00, cache
   write $10.00 (5 min) / $16.00 (1 h), cache read $0.20. Region premium: US Geo
   $8.80 / $44.00, EU cross-region $8.80 / $44.00, Global $8.00 / $40.00.
7 **Consequence for the "$0.20/1M" target.** It is the *cache read* rate, not
   the input rate. It only pays where a long stable prefix is re-read — our
   agent sessions (system prompt + tools), not our benchmark legs, whose
   prompts are 98–620 tokens each.

## Measured price of one Fable column on our own public suite

Token counts were read back from the published answer bytes
(`benchmarks/public/arms/*-basalt-answers.jsonl`, fields `ptok` / `ctok`), so
this is our real request shape, not an estimate: 7,685 calls, 1,443,741 input
tokens, 2,040,042 output tokens.

| Set | calls | in tok | out tok | $ at face | $ with output ×3 (thinking) |
|---|---:|---:|---:|---:|---:|
| ARC-Challenge | 1172 | 143,821 | 127,706 | 6.26 | 16.48 |
| ARC-Easy | 2376 | 267,593 | 214,377 | 10.72 | 27.87 |
| BFCL | 1240 | 482,672 | 227,379 | 12.96 | 31.15 |
| GPQA-Diamond | 198 | 56,234 | 158,848 | 6.80 | 19.51 |
| GSM8K | 1319 | 173,082 | 360,442 | 15.80 | 44.64 |
| HumanEval | 164 | 31,488 | 98,892 | 4.21 | 12.12 |
| IFEval | 541 | 53,378 | 359,377 | 14.80 | 43.55 |
| MMLU-Pro | 500 | 126,651 | 186,601 | 8.48 | 23.41 |
| LiveCodeBench | 175 | 108,822 | 306,420 | 13.13 | 37.64 |
| **total** | **7685** | **1,443,741** | **2,040,042** | **93.15** | **256.35** |

Output at ×6 would be $501. Input is 4.5% of the bill, so caching does not make
a benchmark column cheap — output length does. The same legs run on the local
brain for tens of watt-hours (a few eurocents). Any decision to add a paid cloud
column is therefore a budget decision first, a quality decision second.

## Advisor routing on the surfaces that exist today

Requested pattern: routine steps cheap, planning/debug steps expensive.

* Cheap lane stays local by default (`qwen3.8-flash-next-iq3_s-basalt` on the
  benchmark box). If a cloud cheap lane is wanted, use Sonnet 5.5 through
  Global CRIS `global.anthropic.claude-sonnet-5-5`.
* Hard lane: `delegation.provider: bedrock` plus
  `delegation.model: global.anthropic.claude-fable-5-2` — verified keys in the
  config defaults, empty means "inherit parent", so delegated children can be
  pinned without touching the main brain.
* Per-task side-LLM pins under `auxiliary:` (`provider`, `model`,
  `reasoning_effort`) for compression, curator, session_search and title work —
  that is where a stable long prefix exists and where the $0.20 cache read
  actually applies.
* `hermes fallback` gives the failure chain (local ↔ cloud) without code.
* Anthropic's own **Advisor tool** (one model advising another inside a single
  tool loop) is a Beta Messages feature and is not part of the Converse path
  Hermes uses for Bedrock. Today the equivalent we can run is the delegation and
  auxiliary pinning above; a true advisor loop needs its own contract and
  version before it can be claimed.

## Apply sequence, held until the owner says go

1. Credentials are entered by the owner on the machine, never through chat:
   `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` in `~/.hermes/.env` (secrets
   file, mode 600) or a named profile in `~/.aws/credentials`. Region is not a
   secret and belongs in `config.yaml` under `bedrock.region`.
2. IAM: scope the key to `bedrock:InvokeModelForInferenceProfiles` on the two
   inference-profile ARNs and nothing else. No account-wide `InvokeModel`, no
   admin key.
3. Bedrock console / API: enable model access for product
   `prod-m733do2vrmi3o`, then set the account/project data-retention mode to
   `aws_review`. Step 3 is the point of no return for privacy and must be an
   explicit owner decision (GitHub issue #55).
4. `hermes config set bedrock.region <region>`; do not switch
   `model.provider` before a smoke call passes.
5. Restart the gateway so the runtime picks the environment that contains boto3
   (the live process still runs the pre-bedrock environment). Restart is
   deliberately deferred: see the deployment hold in
   `benchmarks/public/PUB-PLAN.md` (issue #43).
6. Smoke and measure: one `hermes chat --provider bedrock --model
   global.anthropic.claude-fable-5-2 -q …`, then confirm the response carries no
   `temperature`/`top_p`, that `usage` reports cache read/write tokens, and that
   the billed amount matches the table above.
7. Only after 1–6: decide whether Fable becomes a fifth column in the public
   table (matched shape, sampling parameters corrected, cost per set from the
   table) or stays an advisor lane for hard steps only.

## Do not do

* Do not put AWS keys in this repository, in a chat message, or in a LiteLLM
  config file that is world-readable.
* Do not send personal documents to a covered model while the retention mode is
  under discussion; the private-data line stays on hold (issue #44).
* Do not report a Fable percentage before a matched-shape arm exists; the
  published arms keep one request shape for every column.

## Account pass, 2026-11-10 13:20–13:45 CET (account `claryel`, us-east-1)

Everything in this section is read from live AWS calls, not from documentation. The Bedrock and
IAM console sub-routes render only the shell with "Unable to load content" — their bundle assets
come back HTTP 403 from `a.b.cdn.console.awsstatic.com` with `server: AmazonS3`, which is an
AWS-side bundle problem, not our network (clearing console storage and switching to eu-west-1 do
not change it). The console shell and **CloudShell** work, so the work ran through the CLI.

Applied on the account:

* IAM user `hermes-bedrock`, inline policy `bedrock-invoke-three-claude-profiles`:
  `bedrock:InvokeModel`, `bedrock:InvokeModelForInferenceProfiles`,
  `bedrock:GetInferenceProfile` on the three inference-profile ARNs in us-east-1 plus the
  matching foundation-model ARNs. The ARN shape matters and cost two iterations: a
  `global.anthropic.*` profile authorizes against `arn:aws:bedrock:::foundation-model/<fm>`
  (empty region and account), and a `us.anthropic.*` profile fans out across regions (the
  us-east-1 profile resolved to a us-east-2 foundation-model ARN), so the policy uses
  `arn:aws:bedrock:*::foundation-model/anthropic.claude-<model>` for the named models only.
* One access key for that user, written into the Hermes profile env file with 0600 permissions.
  The secret value never entered this repository, a chat message, or a log. Two earlier keys were
  created and deleted when the capture step failed; `list-access-keys` now reports exactly one.
* Hermes profile `bedrock` pins `global.anthropic.claude-haiku-5-5` with `reasoning_effort: low`
  and `delegation.reasoning_effort: low`; `model.key_env` is unset so the AWS SDK chain is used.

Verified state (the four gates read off `get-foundation-model-availability`, for
`anthropic.claude-haiku-5-5`, `anthropic.claude-haiku-4-5-20251001-v1:0` and
`anthropic.claude-fable-5-2`): `authorizationStatus AUTHORIZED`, `entitlementAvailability
AVAILABLE`, `regionAvailability AVAILABLE`, `agreementAvailability NOT_AVAILABLE`. Every invoke
fails with `anthropic.claude-<model> is not available for this account`, and the older models
instead report `Model use case details have not been submitted for this account`, confirmed by
`get-use-case-for-model-access` → `ResourceNotFoundException: You have not filled out the request
form`.

So the single blocker is paper, not plumbing:

1. The Anthropic first-time-use form (`put-use-case-for-model-access`) has never been filed for
   this account. Its content **is shared with Anthropic**, so filing it is an owner disclosure
   decision, not a configuration step; the draft text is in issue #55 and has not been sent.
2. After the form, the SaaS agreement is auto-created by the **first invoke from an identity that
   holds `aws-marketplace:Subscribe` / `ViewSubscriptions`** (the console identity here). The
   invoke-only user starts working after that, no policy change needed.

Retention, checked rather than assumed: `get-account-data-retention` returns `mode: inherit`, and
the only lever is `put-account-data-retention`, which is **account-wide**. The
`anthropic.claude-fable-5-2` model card states that using it requires opting in to AWS review
(`aws_review`); the Haiku 5.5 card has no such clause. `aws_review` was not enabled.

Cost re-quote, because availability changes the cheap lane: if Haiku 5.5 ($0.10/$0.50 per MTok)
stays unentitled on this account, the nearest Claude that only needs the form is Haiku 4.5 at
$1.00/$5.00 per MTok — $11.64 for the published public-suite token mix (1 443 741 in / 2 040 042
out), against 0.64 kWh of measured local GPU energy for the same work, i.e. €0.16 at the owner's
0.25 €/kWh tariff. The ranking (electricity ≪ cheap cloud ≪ mid ≪ frontier) does not change;
the gap to the cheap lane goes from ~6× to ~70×.

Not done, and deliberately left for the owner: filing the form, `aws_review`, and the gateway
restart that lets the running brain see boto3 (the process predates the PM environment that
carries it — see the environment mismatch note above).
