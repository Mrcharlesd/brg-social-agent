import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

_STATE_FILE = "distributed.json"


@dataclass(frozen=True)
class DistributionState:
    post_id: str
    platforms: dict[str, str] = field(default_factory=dict)

    def is_distributed_to(self, platform: str) -> bool:
        return platform in self.platforms

    def mark_distributed(self, platform: str) -> "DistributionState":
        updated = {**self.platforms, platform: datetime.now(timezone.utc).isoformat()}
        return DistributionState(post_id=self.post_id, platforms=updated)


def load_state(post_dir: Path) -> DistributionState:
    state_path = post_dir / _STATE_FILE
    if not state_path.exists():
        return DistributionState(post_id=post_dir.name)
    data = json.loads(state_path.read_text(encoding="utf-8"))
    return DistributionState(
        post_id=data["post_id"],
        platforms=data.get("platforms", {}),
    )


def save_state(state: DistributionState, post_dir: Path) -> None:
    state_path = post_dir / _STATE_FILE
    state_path.write_text(
        json.dumps({"post_id": state.post_id, "platforms": state.platforms}, indent=2),
        encoding="utf-8",
    )
