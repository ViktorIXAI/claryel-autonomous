"""Harbor agent arms for comparing bare, Hermes, and verified-Hermes runs.

The arms deliberately share one inference endpoint. Only the agent loop and
post-run verification layer change, so score deltas measure the harness.
"""

import shlex
import yaml
from typing import Any, override

from harbor.agents.installed.hermes import Hermes
from harbor.environments.base import BaseEnvironment
from harbor.models.agent.context import AgentContext


_VERIFICATION_PROMPT = """
You are now in the verification phase for the same task. The task container and
files are unchanged since the previous agent phase.

Work autonomously and make changes directly. Do not ask for clarification.

Protocol:
1. Re-read the original instruction and every visible task file.
2. Enumerate each concrete deliverable, file, format, command, and output.
3. Run the project's relevant tests, linters, build steps, and realistic smoke
   commands. If there is no visible test, construct a focused local check.
4. Compare observed behavior with the instruction. Do not trust the previous
   agent's claim that it finished.
5. Repair any missing, wrong, stale, unreadable, or misformatted deliverable.
6. Re-run the checks after every repair.
7. Finish only when all visible evidence is consistent with the instruction.

Hard limits:
- Never search for, download, or read an official solution or answer key.
- Never read hidden verifier files. If a path such as /tests is not already
  visible in the task workspace, do not create, request, or infer its contents.
- Never fabricate outputs.
- Stay inside the task container and task workspace.
"""


class HermesBenchmark(Hermes):
    """Open-source Hermes arm with a release-compatible bootstrap."""

    @staticmethod
    @override
    def name() -> str:
        return "hermes_benchmark"

    @override
    def get_version_command(self) -> str | None:
        return 'export PATH="$HOME/.local/bin:$PATH"; hermes --version'

    @override
    async def install(self, environment: BaseEnvironment) -> None:
        await self.ensure_system_dependencies(
            environment, ("curl", "git", "ripgrep", "xz")
        )
        branch_flag = f" --branch {self._version}" if self._version else ""
        await self.exec_as_agent(
            environment,
            command=(
                "set -euo pipefail; "
                "curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/"
                f"main/scripts/install.sh | bash -s -- --skip-setup{branch_flag} && "
                'export PATH="$HOME/.local/bin:$PATH" && '
                'export HERMES_HOME="${HERMES_HOME:-/tmp/hermes}" && '
                'mkdir -p "$HERMES_HOME" "$HERMES_HOME/sessions" "$HERMES_HOME/skills" '
                '"$HERMES_HOME/memories" && '
                'hermes pm repair && '
                "hermes --version"
            ),
        )

    def _build_config_yaml(
        self,
        model: str,
        max_turns: int | None = None,
        *,
        connection: Any | None = None,
    ) -> str:
        config = yaml.safe_load(
            super()._build_config_yaml(model, max_turns, connection=connection)
        )
        config.setdefault("agent", {})["max_turns"] = max_turns or 180
        config.setdefault("terminal", {})["timeout"] = 300
        return yaml.dump(config, default_flow_style=False)


class VerifiedHermes(HermesBenchmark):
    """Hermes plus one bounded self-audit and repair pass."""

    @staticmethod
    @override
    def name() -> str:
        return "verified_hermes"

    async def _copy_phase_artifacts(self, environment: BaseEnvironment, phase: int) -> None:
        target = shlex.quote(f"/logs/agent/hermes-phase-{phase}")
        await self.exec_as_agent(
            environment,
            command=(
                f"mkdir -p {target} && "
                "if [ -f /logs/agent/hermes.txt ]; then "
                f"cp /logs/agent/hermes.txt {target}/stdout.txt; fi && "
                "if [ -f /logs/agent/hermes-session.jsonl ]; then "
                f"cp /logs/agent/hermes-session.jsonl {target}/session.jsonl; fi"
            ),
            timeout_sec=15,
        )

    @override
    async def run(
        self,
        instruction: str,
        environment: BaseEnvironment,
        context: AgentContext,
    ) -> None:
        # Phase 1: normal Hermes attempt.
        self._resume = False
        await super().run(instruction, environment, context)
        await self._copy_phase_artifacts(environment, 1)

        # Phase 2: resume the same native session with a verifier prompt.
        if not getattr(self, "_native_session_id", None):
            return
        self._resume = True
        try:
            await super().run(_VERIFICATION_PROMPT, environment, context)
        finally:
            self._resume = False
            await self._copy_phase_artifacts(environment, 2)
