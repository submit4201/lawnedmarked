from dataclasses import dataclass

from core.commands import Command, CommandPayload
from core.command_payloads import InjectWorldEventPayload


@dataclass
class InjectWorldEventCommand(Command):
    """God-tool style command used by GM/Judge LLMs to inject a single immutable event."""

    command_type: str = "INJECT_WORLD_EVENT"
    payload_type: type[CommandPayload] = InjectWorldEventPayload


__all__ = ["InjectWorldEventCommand"]
