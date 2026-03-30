from __future__ import annotations
from dataclasses import dataclass, field

PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str           # "low" | "medium" | "high"
    category: str           # "walk" | "feeding" | "meds" | "grooming" | "enrichment"
    frequency: str = "daily"  # "daily" | "weekly" | "as_needed"
    completed: bool = False

    def is_feasible(self, available_minutes: int) -> bool:
        """Returns True if this task fits within the remaining time budget."""
        return self.duration_minutes <= available_minutes

    def mark_complete(self) -> None:
        """Marks this task as done."""
        self.completed = True


@dataclass
class Pet:
    name: str
    species: str            # "dog" | "cat" | "other"
    owner: Owner = field(repr=False)
    _tasks: list[Task] = field(default_factory=list, init=False, repr=False)

    def get_tasks(self) -> list[Task]:
        """Returns all tasks associated with this pet."""
        return list(self._tasks)

    def add_task(self, task: Task) -> None:
        """Adds a task to this pet's task list."""
        self._tasks.append(task)


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: dict       # e.g. {"time_of_day": "morning", "avoid": "late_feeding"}
    _pets: list[Pet] = field(default_factory=list, init=False, repr=False)

    def get_available_time(self) -> int:
        """Returns the owner's total daily time budget in minutes."""
        return self.available_minutes

    def add_pet(self, pet: Pet) -> None:
        """Registers a pet under this owner."""
        self._pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Returns all pets belonging to this owner."""
        return list(self._pets)

    def get_all_tasks(self) -> list[Task]:
        """Collects and returns every task across all of this owner's pets."""
        tasks = []
        for pet in self._pets:
            tasks.extend(pet.get_tasks())
        return tasks


@dataclass
class DailyPlan:
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    total_duration: int = 0
    explanations: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Formats the plan as a readable string for display in the UI."""
        lines = [f"=== Daily Plan | {self.total_duration} min scheduled ===", ""]

        lines.append("Scheduled:")
        for task in self.scheduled_tasks:
            lines.append(f"  [x] {task.title} — {task.duration_minutes} min ({task.priority})")

        if self.skipped_tasks:
            lines.append("\nSkipped:")
            for task in self.skipped_tasks:
                lines.append(f"  [ ] {task.title} — {task.duration_minutes} min ({task.priority})")

        if self.explanations:
            lines.append("\nReasoning:")
            for note in self.explanations:
                lines.append(f"  - {note}")

        return "\n".join(lines)


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    def build_plan(self) -> DailyPlan:
        """
        Retrieves all incomplete tasks from every pet the owner has,
        sorts them high-to-low priority, then greedily fits them
        into the owner's available time budget.
        """
        plan = DailyPlan()
        remaining = self.owner.get_available_time()

        # Gather incomplete tasks across all pets, highest priority first
        candidates = [t for t in self.owner.get_all_tasks() if not t.completed]
        candidates.sort(key=lambda t: PRIORITY_ORDER.get(t.priority, 0), reverse=True)

        for task in candidates:
            if task.is_feasible(remaining):
                plan.scheduled_tasks.append(task)
                plan.total_duration += task.duration_minutes
                remaining -= task.duration_minutes
                plan.explanations.append(
                    f"'{task.title}' scheduled — {task.duration_minutes} min used, "
                    f"{remaining} min remaining."
                )
            else:
                plan.skipped_tasks.append(task)
                plan.explanations.append(
                    f"'{task.title}' skipped — needs {task.duration_minutes} min, "
                    f"only {remaining} min left."
                )

        return plan

    def explain_plan(self) -> list[str]:
        """Returns only the reasoning notes from the built plan."""
        return self.build_plan().explanations
