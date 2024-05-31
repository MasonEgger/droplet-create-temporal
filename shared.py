from dataclasses import dataclass

TASK_QUEUE_NAME = "droplet-tasks"


@dataclass
class DropletSpec:
    text: str


@dataclass
class DropletResult:
    text: str
