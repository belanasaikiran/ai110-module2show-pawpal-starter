from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str          # "low" | "medium" | "high"
    category: str          # "walk" | "feeding" | "meds" | "grooming" | "enrichment"
    completed: bool = False

    def is_feasible(self, available_minutes: int) -> bool:
        """Returns True if this task fits within the remaining time budget."""
        pass


@dataclass
class Pet:
    name: str
    species: str           # "dog" | "cat" | "other"
    owner: Owner = field(repr=False)
    _tasks: list[Task] = field(default_factory=list, init=False, repr=False)

    def get_tasks(self) -> list[Task]:
        """Returns the list of tasks associated with this pet."""
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: dict      # e.g. {"time_of_day": "morning", "avoid": "late_feeding"}
    _pets: list[Pet] = field(default_factory=list, init=False, repr=False)

    def get_available_time(self) -> int:
        """Returns how many minutes are free for tasks."""
        pass

    def add_pet(self, pet: Pet) -> None:
        """Adds a pet to this owner's list."""
        pass


@dataclass
class DailyPlan:
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    total_duration: int = 0
    explanations: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Formats the plan for display in the UI."""
        pass


class Scheduler:
    def __init__(self, owner: Owner, pet: Pet, tasks: list[Task]) -> None:
        self.owner = owner
        self.pet = pet
        self.tasks = tasks

    def build_plan(self) -> DailyPlan:
        """Selects and orders tasks within the owner's time budget."""
        pass

    def explain_plan(self) -> list[str]:
        """Returns reasoning for why each task was included or skipped."""
        pass
