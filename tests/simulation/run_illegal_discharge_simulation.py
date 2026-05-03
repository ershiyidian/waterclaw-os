from __future__ import annotations

from tests.fixtures.agent_events.illegal_discharge_agent_events import ILLEGAL_DISCHARGE_AGENT_EVENT_FRAMES
from tests.simulation.agent_event_protocol import encode_sse_event, parse_sse_events, validate_formal_agent_sequence


def build_illegal_discharge_sse_fixture() -> str:
    return "".join(encode_sse_event(frame) for frame in sorted(ILLEGAL_DISCHARGE_AGENT_EVENT_FRAMES, key=lambda item: item["at"]))


def validate_illegal_discharge_fixture() -> list[str]:
    return validate_formal_agent_sequence(parse_sse_events(build_illegal_discharge_sse_fixture()))


if __name__ == "__main__":
    errors = validate_illegal_discharge_fixture()
    if errors:
        raise SystemExit("\n".join(errors))
    print("illegal-discharge AgentEvent simulation fixture is valid.")
