# Amazon Bedrock / Claude Fable 5.2 advisor lane

Status: **local side verified end-to-end, AWS model access still gated**. Written 2026-11-10 after an
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

1. The Anthropic first-time-use form (`put-use-case-for-model-access`) was **filed on
   2026-11-10 13:52 CET** after the owner's go-ahead; the stored form reads back as company
   `CLARYEL`, website `https://claryel.com`, industry `Technology`, users = owner, operators and
   developers, intended use = public-benchmark harness for local quantized LLMs, code
   generation/review/debugging, log and energy analysis on owned servers, no third-party personal
   data. Filing it is an owner disclosure decision: its content is shared with Anthropic.
2. After the form, the SaaS agreement is auto-created by the **first invoke from an identity that
   holds `aws-marketplace:Subscribe` / `ViewSubscriptions`** (the console identity here). The
   invoke-only user starts working after that, no policy change needed.

Re-check after the form, `2026-11-10 14:02–14:05 CET`: `agreementAvailability` is still
`NOT_AVAILABLE` for `anthropic.claude-haiku-5-5`, `anthropic.claude-haiku-4-5-20251001-v1:0` and
`anthropic.claude-sonnet-4-5-20250929-v1:0`. First invoke from the console (root) identity: Haiku
5.5 -> `AccessDeniedException` — "anthropic.claude-haiku-5-5 is not available for this account ...
contact AWS Sales"`; Haiku 4.5 -> `ThrottlingException: "Too many tokens per day"`. Service Quotas
lists the effective cross-region TPM for both Haiku 4.5 and 5.5 as `0.0` while the requestable
*default* is `5,000,000` (an increase request below the default is rejected) — the zero is a
symptom of the missing model access, not a capacity ceiling, so quota tickets are not the fix.
Conclusion: what is left is account-level AWS enablement (agreement/auto-provisioning, possibly an
AWS Sales step for the Claude 5 family), not our IAM, network, SDK or routing. The gate is cheap to
re-check (`get-foundation-model-availability` plus a 1-token `converse`); until it clears, the
local brain stays the production lane and no Bedrock arm is published.

Later the same day (`2026-11-10 15:40 CET`), after the owner reported an AWS e-mail confirming a
signed model agreement, the control-plane read moved: **Haiku 4.5 `agreement: AVAILABLE`**, Haiku
5.5 still `NOT_AVAILABLE`, and the effective cross-region TPM is still `0.0` for **both**, including
the model whose agreement just opened (quota codes `L-58BE175A`/`L-9A11C666` for 4.5,
`L-47520EB7` for 5.5). Owner decision recorded with that read: **no benchmark arm, smoke test or
any inference workload runs on the 4.5 lane** — the pin stays Haiku 5.5, and the cheaper model is
never swapped in to make a number.

Money state, read from the live console Credits page (the Credits widget renders even though other
billing sub-pages do not): credit (id withheld), type **AWS Activate — FOUNDERS**, **$1,000.00**,
valid `10/01/2026 → 10/31/2028`, status **Active**, used **$0.00**, remaining **$1,000.00**; total
remaining $1,000.00, total used $0.00. So the block is not "no money": the money is there and
unspent. The one payment input we still cannot read is the attached payment method — the Payments
sub-page returns "Unable to load content" like the other broken micro-frontends, and no CLI verb in
CloudShell's `aws-cli/2.39.5` exposes it. An account holding only Activate credits and no payment
method would explain the pattern we saw (agreement `AVAILABLE`, TPM `0.0`, invoke throttled with
"Too many tokens per day"), and it is owner-checkable in a minute at Billing → Payments.
Cost Explorer still reports **no spend in the trailing 90 days**, and the monthly COST budget
`claryel-monthly-cost` ($100) exists so the first real metering is visible. Email notifications for
it were rejected by the CLI (subscriber verification is owner-side), so the alarm is dashboard-only
until the owner attaches a verified address.

Credit applicability, read from the account rather than from the rules text: the Activate grant's
"Applicable products" list was scrolled to completion in the console (the widget virtualizes its
list, so a copy/paste of it reads alphabetically truncated and can look like it is missing lines —
the owner's paste started mid-alphabet). Full list: **267 entries**, containing `Amazon Bedrock`,
`Amazon Bedrock Service`, `AmazonBedrockFoundationModels`, `Amazon Bedrock AgentCore`,
`Amazon Bedrock Managed Knowledge Base`, and **no** entry for `Anthropic`, `Claude` or
`AWS Marketplace`. Read of that fact: the list authorises the Bedrock service lines but names
neither the provider nor Marketplace, while Anthropic models on Bedrock are sold as a Marketplace
product and appear on the bill under the provider. Activate terms do allow that spend ("Bedrock 3P
Model Spend"), so the coverage question is settled only empirically: after the first paid call on
`bedrock-runtime` (not `bedrock-mantle`, which bills in Consumption Units and is not named in the
terms), check the next day whether *Credits Applied* reduces the **provider** line in Cost
Explorer. Provider line charged as cash = the credit does not reach Claude, and the credit should be
spent on EC2/S3 instead. Re-checked at `15:46 CET` after the owner confirmed the payment method:
Haiku 5.5 still answers `AccessDeniedException`, so that test cannot run yet.

Payment and gate state after the owner re-verified the card (a 1 EUR hold that returned, so the
payment method is live): `agreementAvailability` for `anthropic.claude-haiku-5-5` is `NOT_AVAILABLE`
in **us-east-1, us-east-2, eu-west-1 and eu-central-1** — the block is account-wide, not a regional
rollout, so switching region or endpoint shape will not fix it. In the same window
`anthropic.claude-haiku-4-5-20251001-v1:0` reads `AVAILABLE`, which proves the account can hold an
Anthropic agreement; the Claude 5 family is the part AWS has not opened. Cross-region TPM stays `0.0`
for both. Note the shape difference in the errors: from our invoke-only key, a call in a region whose
inference-profile ARNs the policy does not list fails as an IAM denial naming the user ARN, while the
model gate fails naming the model — the two must not be conflated when reading a probe.

## The missing step: the model offer has to be accepted explicitly

The whole blocker was one API call we had not made. Bedrock publishes a paid-model **offer** per
foundation model and the account must accept it:

```bash
aws bedrock list-foundation-model-agreement-offers --model-id anthropic.claude-haiku-5-5
# -> offerId offer-u3aih6zr7uw5u + an opaque offerToken
aws bedrock create-foundation-model-agreement --model-id anthropic.claude-haiku-5-5 \
    --offer-token "$(jq -r '.offers[0].offerToken' offers.json)"
```

Observed at `16:3x CET`: filing the use-case form alone did nothing for **3+ hours**; accepting the
offer flipped `agreementAvailability` `NOT_AVAILABLE -> PENDING -> AVAILABLE` inside a few minutes.
`anthropic.claude-haiku-4-5-20251001-v1:0` already had its agreement because the same offer had been
accepted earlier (that is the AWS e-mail the owner saw). Service Quotas then stopped reporting `0.0`
for the Haiku 5.5 cross-region token quota — the quota only becomes visible/requestable after the
agreement exists, and its default turned out to be **10,000,000 TPM**, so no quota request is needed.
Sequence for any future Bedrock model on this account: use-case form (once) -> list offers ->
`create-foundation-model-agreement` -> wait for `AVAILABLE` -> only then talk about quotas or cost.
Invoke still returned `AccessDeniedException` minutes after the flip, i.e. entitlement propagation
lags the control-plane flag; re-probe before concluding anything is broken.

## Contracted but not cleared: Claude Fable 5.2

The owner's rule for the expensive lane: **заключаем договор, но не подключаем** — accept the offer so
the contract exists, keep the model out of any runtime path until he clears it. Done at `18:1x CET`:

```bash
aws bedrock list-foundation-model-agreement-offers --model-id anthropic.claude-fable-5-2   # offer-agsprgw6z3dg6
aws bedrock create-foundation-model-agreement --model-id anthropic.claude-fable-5-2 --offer-token "$TOK"
```

`agreementAvailability` reached `AVAILABLE`. Nothing else was touched: **no invoke, no smoke call, no
endpoint, no quota request**, and the account data-retention mode stays `inherit` — Fable's model card
requires opting into `aws_review` (30-day review-required retention, an account-wide lever), which is an
owner decision and has not been made. The gate monitor now reads the Fable flag from the control plane
(`control_only/agreement=...`, zero tokens) so a flip is visible without spending anything.

Lanes are pre-wired but inert — `~/.hermes/scripts/bedrock_lane.sh` writes profile config only, it never
calls a model:

| Lane | Model ID | Effort | Price $/1M in-out | Full public suite (1.44M in / 2.04M out) |
|---|---|---|---|---|
| `haiku-low` (pinned default) | `global.anthropic.claude-haiku-5-5` | low | 0.10 / 0.50 | $1.16 |
| `haiku-high` | same | high | 0.10 / 0.50 | ~$3.20 (thinking ≈ ×3 output) |
| `sonnet-low` / `sonnet-high` | `global.anthropic.claude-sonnet-5-5` | low/high | 2.00 / 10.00 | $23.29 / ~$64 |
| `fable-low` / `fable-high` | `global.anthropic.claude-fable-5-2` | low/high | 8.00 / 40.00 | $93.15 / ~$256 |

`bedrock_lane.sh fable-*` exits `3` with a warning unless `--i-know` is passed after the owner clears
Fable; that guard exists because Fable is 80× Haiku 5.5 per token and also rejects our benchmark request
shape (`temperature=1.0` or omitted, never 0.7). The middle lane (Sonnet 5.5) was accepted right after —
see the contract table below — and the older/other Anthropic rows are listed there with their live flags.

**Update `18:3x CET`: the Sonnet 5.5 contract has since been accepted** (`offer-5fu2rhus3byrs`), its flag
went straight to `AVAILABLE`. It is still not used: the pinned lane remains `haiku-low`, the monitor only
reads its control-plane flag, and clearing a lane for inference stays an owner decision.

### Anthropic catalogue on this account (16 models, live agreement flags, 18:37 CET)

Contracts cost nothing until a token is generated; the flag below says only whether the paperwork exists.

| Model | Agreement | $/1M in-out (published rates) |
|---|---|---|
| `claude-haiku-5-5` | **AVAILABLE** (lane pin, effort low) | 0.10 / 0.50 |
| `claude-haiku-4-5-20251001-v1:0` | AVAILABLE — owner bars all inference, EOL past | 1.00 / 5.00 |
| `claude-sonnet-5-5` | **AVAILABLE** (contracted, not cleared) | 2.00 / 10.00 |
| `claude-fable-5-2` | **AVAILABLE** (contracted, not cleared, needs `aws_review`) | 8.00 / 40.00 |
| `claude-sonnet-5` | NOT_AVAILABLE (no contract) | 2.00 / 10.00 |
| `claude-sonnet-4-6`, `claude-sonnet-4-5-20250929-v1:0` | NOT_AVAILABLE | 3.00 / 15.00 (4.6) |
| `claude-opus-5-5` | **AVAILABLE→** contract accepted `18:5x CET` (`offer-7sp77cpl4rveu`), flag was `PENDING` at read time | 4.00 / 20.00 |
| `claude-opus-5` | NOT_AVAILABLE | 5.00 / 25.00 |
| `claude-opus-4-8`, `-4-7`, `-4-6-v1`, `-4-5`, `-4-1` | NOT_AVAILABLE | 5.00 / 25.00 (4.8) |
| `claude-fable-5`, `claude-fable-5-1` | NOT_AVAILABLE | 10.00 / 50.00 (5.1) |

Catalogue-wide the account can see **126 foundation models**: `amazon` 21 (Nova), `anthropic` 16,
`openai` 14, `stability` 13, `mistral` 13, `meta` 7, `cohere` 6, `qwen` 5, `zai` 4 (GLM), `twelvelabs` 4,
`nvidia` 3, `writer` 3. Non-Anthropic rows generally need no Marketplace contract, so a cheap second
opinion lane (Qwen / GLM / gpt-oss / Nova) is an availability question, not a paperwork question. Rates
for Anthropic rows come from the model cards plus published Bedrock rate tables; treat them as quoted
until a real invoice confirms them.

### One-character invoke audit, `18:55 CET`

Owner asked for the cheapest possible proof of invokability: one short question, answer capped at one
character, `maxTokens=8`, every contracted lane at once (`~/.hermes/cache/scratch/brping.py`).

| Lane | Result |
|---|---|
| `global.anthropic.claude-haiku-5-5` | `AccessDeniedException` |
| `global.anthropic.claude-sonnet-5-5` | `AccessDeniedException` |
| `global.anthropic.claude-opus-5-5` | `AccessDeniedException` |
| `global.anthropic.claude-fable-5-2` | `AccessDeniedException` |
| **spend** | **in=0 out=0 tokens, $0.00** |

Haiku 4.5 was deliberately not pinged (owner bar on that model; a one-character ping there would cost
≈ $0.00004). What this rules out: the request shape, the credentials, the region and the SDK are fine —
the same code path against 4.5 earlier produced `ThrottlingException`, i.e. an *entitled* model answers
and only the rate limit stopped it. What it does not yet separate: (a) entitlement propagation still
running for the 5-generation models, or (b) their per-model token quota is provisioned at 0/unknown the
way 4.5's was. The next cheap discriminator is a quota read per model (control plane, free) plus the
periodic re-probe; if the quota reads a real default, (b) is dead and only time is left.

**Discriminator read at `19:0x CET` — the two layers are now separated.** Invoking Haiku 5.5 from the
**CloudShell admin identity** (the same identity that creates IAM users, keys and budgets, so it cannot be
an IAM problem) returns the model-level sentence:

```
AccessDeniedException when calling the Converse operation:
  model `anthropic.claude-haiku-5-5` is not available for this account.
  You can explore other available models on Amazon Bedrock. For additional access options,
  contact AWS Sales
```

while Haiku 4.5 — whose agreement is older — returns `ThrottlingException: Too many tokens per day`. Those
two sentences are different layers: **throttle = access granted, capacity zero; not-available = access not
served yet.** Consequences that follow directly from the readings:

- The `10,000,000 TPM` figure is a **rate ceiling, not an allowance or a balance**. A model can have a
  healthy ceiling and still be unreachable (Haiku 5.5), and a model can be reachable and still unusable
  because its ceiling is `0.0` (Haiku 4.5). Raising quotas cannot fix a `not available` error.
- Conversely the models whose quota reads null/unknown are not "out of tokens" — their quota simply is not
  provisioned until AWS serves the entitlement, which is why the number never appeared.
- `list-marketplace-model-endpoints` returns `[]` and Haiku 4.5 invokes without one, so a Marketplace model
  **endpoint** is not the missing piece either — and creating one would mean a dedicated (paid) deployment,
  so that path stays closed.
- No other enablement verb exists in this API surface (`create/delete-foundation-model-agreement`,
  `list-foundation-model-agreement-offers`, use-case form, availability read, inference profiles,
  marketplace endpoints). Filing the agreement is the whole CLI-side sequence; the rest is AWS-side.

So the remaining lever is time plus AWS itself: if the runtime flag has not caught up by the next morning
(~15 h after acceptance), the ask goes to AWS Support/Sales, which cannot be filed from this CLI (`support
describe-creates` is absent in this build, so category codes are unavailable) and the Support console page is
another broken micro-frontend — the case text is ready in `~/.hermes/cache/scratch/c53.txt` for the owner to
paste. Every denied attempt costs **$0**, so waiting is free.

## Credential hygiene: what must never reach GitHub

The lane credentials are exactly the thing that must not leak into a repository, an issue comment or a
screenshot. Standing rules, in force for every Bedrock step on this account:

1. **One home for secrets.** AWS access key id + secret live only in `~/.hermes/profiles/bedrock/.env`
   (mode `600`, outside the repo). `~/.aws/credentials` is not used. Nothing else on the machine holds
   them, and the values are never printed — tooling prints masked confirmations only.
2. **Never commit or paste:** access key id / secret, `offerToken` blobs, session tokens, account id,
   model-ARN dumps that embed the account id, full `config.yaml`/`.env` listings, console screenshots of
   the Access keys or Billing pages.
3. **Commands are written so secrets cannot be inline.** Offer tokens are read into a shell variable from
   a file (`TOK=$(jq -r '.offers[0].offerToken' file.json)`) and documented as `"$TOK"`; the repo shows the
   shape of the command, never the value. Same rule for key creation output: captured programmatically into
   `.env`, then the CloudShell buffer is cleared and its temp files deleted on the AWS side.
4. **Machine check before every publish:** `scripts/security/secret_scan.py --git --pre-publish` (also runs
   in the pre-push guard). A non-zero result blocks the push; nothing is pushed "because it was urgent".
5. **Audit, `2026-11-10 18:55 CET`:** tracked files — no AKIA-shaped id, no secret-assignment pattern, no
   `AQICAH…` offer-token blob. Full history — one AKIA-shaped literal, commit `2535841` (Gitleaks controls),
   hash `619e3cc6…`, which is **not** the live key (`4393ce4a…`); it is the AWS documentation example.
   Issue #55 comments — zero matches for key id / offer token / secret patterns. Local scratch files — zero
   raw material, because the key went straight from CloudShell into `.env`. CloudShell scrollback — no key
   or token shapes; the temp files holding offer tokens were deleted on the AWS side.
6. **Rotation is a two-step edit, not an echo:** delete the old key in IAM, create the replacement, write it
   into `.env` programmatically, confirm masked. Never `echo`/`cat` the value in a shell that is recorded.
7. `model.key_env` stays unset for the `bedrock` provider: the profile authenticates through the AWS
   credential chain, so no Strata or gateway key is ever attached to a Bedrock lane.

Verified on this machine, `2026-11-10 14:37 CET`: the `bedrock` PM extra is installed
(`boto3 1.43.115`, `botocore 1.43.118`) and is reachable through the runtime bootstrap, and the
`hermes-gateway` service was restarted (old main PID 519209 from 03:03 ran on a superseded
interpreter tree that predated the install; new main PID 3095687). A fresh-process probe with the
profile's own credentials imports the SDK, recognises `global.anthropic.claude-haiku-5-5` as a
Bedrock Anthropic model, and gets the same AWS-side answer as CloudShell
(`AccessDeniedException` for 5.5, `ThrottlingException` for 4.5). That closes the local half:
SDK, credentials, region, profile pin and routing all work; only AWS enablement is missing.

Retention, checked rather than assumed: `get-account-data-retention` returns `mode: inherit`, and
the only lever is `put-account-data-retention`, which is **account-wide**. The
`anthropic.claude-fable-5-2` model card states that using it requires opting in to AWS review
(`aws_review`); the Haiku 5.5 card has no such clause. `aws_review` was not enabled.

Cost re-quote, because availability changes the cheap lane: the pinned default stays
`global.anthropic.claude-haiku-5-5` at $0.10/$0.50 per MTok — the cheapest Claude on the lane, with
`reasoning_effort: low`. Haiku 4.5 is **not** the connected model and was never configured as one;
it only appears in probes and in this re-quote because AWS answers 5.5 with "not available for this
account", and 4.5 is the nearest Claude whose gate is the use-case form alone. If 4.5 ever becomes
the lane, it costs 10x per token, not less. The two numbers for the published public-suite token
mix (1 443 741 in / 2 040 042 out): Haiku 5.5 $1.16, Haiku 4.5 $11.64 — against 0.64 kWh of measured
local GPU energy for the same work, i.e. €0.16 at the owner's
0.25 €/kWh tariff. The ranking (electricity ≪ cheap cloud ≪ mid ≪ frontier) does not change;
the gap to the cheap lane goes from ~6× to ~70×.

Not done, and deliberately left for the owner: filing the form, `aws_review`, and the gateway
restart that lets the running brain see boto3 (the process predates the PM environment that
carries it — see the environment mismatch note above).
