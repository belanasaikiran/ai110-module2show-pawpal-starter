from __future__ import annotations
from dataclasses import dataclass, field, replace
from datetime import date, timedelta
from itertools import combinations

PRIORITY_ORDER = {"high": 3, "medium": 2, "low": 1}


def sort_by_time(tasks: list[Task]) -> list[Task]:
    """
    Returns a new list of tasks sorted by their scheduled_time ("HH:MM").
    Tasks without a scheduled_time are placed at the end.

    How the lambda key works
    ------------------------
    sorted(..., key=lambda t: ...)
      - `lambda t` receives one Task at a time.
      - We split "HH:MM" on ":" → ["HH", "MM"], convert each part to int,
        then combine into total minutes-since-midnight so "09:30" → 570.
      - Lexicographic string comparison ("09:30" < "10:00") also works for
        zero-padded strings, but the int conversion is explicit and safe.
      - Tasks with no scheduled_time return 9999 (a sentinel that sorts last).

    Example
    -------
    "14:00" → 14*60 + 0  = 840
    "09:30" → 9*60  + 30 = 570   ← comes first
    None    → 9999               ← sorted to the end
    """
    return sorted(
        tasks,
        key=lambda t: (
            int(t.scheduled_time.split(":")[0]) * 60 + int(t.scheduled_time.split(":")[1])
            if t.scheduled_time
            else 9999
        ),
    )

# Tasks are sorted within each time-slot bucket by this category order.
# Lower number = scheduled earlier (meds before feeding, feeding before walk, etc.)
CATEGORY_ORDER = {"meds": 0, "feeding": 1, "walk": 2, "grooming": 3, "enrichment": 4}

# Back-to-back pairs that should raise a conflict warning
CONFLICTING_BACK_TO_BACK: set[tuple[str, str]] = {
    ("walk", "walk"),
    ("feeding", "feeding"),
    ("meds", "meds"),
}

# Ordering rules: key category must appear before value category
MUST_PRECEDE: dict[str, str] = {"meds": "feeding"}


def _hhmm_to_minutes(hhmm: str) -> int:
    """Converts "HH:MM" to total minutes since midnight.  "08:30" → 510."""
    h, m = hhmm.split(":")
    return int(h) * 60 + int(m)


def _minutes_to_hhmm(total: int) -> str:
    """Converts total minutes since midnight back to "HH:MM".  510 → "08:30"."""
    return f"{total // 60:02d}:{total % 60:02d}"


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str           # "low" | "medium" | "high"
    category: str           # "walk" | "feeding" | "meds" | "grooming" | "enrichment"
    frequency: str = "daily"          # "daily" | "weekly" | "as_needed"
    preferred_time: str = "any"       # "morning" | "afternoon" | "evening" | "any"
    scheduled_time: str | None = None # clock time "HH:MM", e.g. "08:30"
    completed: bool = False
    last_completed_date: str | None = None  # ISO date "YYYY-MM-DD" — when it was last done
    due_date: str | None = None             # ISO date "YYYY-MM-DD" — when next occurrence is due

    def is_feasible(self, available_minutes: int) -> bool:
        """Returns True if this task fits within the remaining time budget."""
        return self.duration_minutes <= available_minutes

    def mark_complete(self, on_date: str | None = None) -> None:
        """Marks this task as done and records the completion date."""
        self.completed = True
        self.last_completed_date = on_date or date.today().isoformat()

    def as_next_occurrence(self) -> Task:
        """
        Returns a fresh copy of this task with completion state cleared and
        due_date set to the next correct calendar date using timedelta.

        Calculation
        -----------
        completed_on  — taken from self.last_completed_date (set by mark_complete
                        just before this method is called in Pet.complete_task).
        interval      — timedelta(days=1)  for "daily"
                        timedelta(days=7)  for "weekly"
        due_date      — (completed_on + interval).isoformat()

        Example
        -------
        Task completed on 2026-03-30 (daily):
            completed_on + timedelta(days=1) → due_date = "2026-03-31"

        Task completed on 2026-03-30 (weekly):
            completed_on + timedelta(days=7) → due_date = "2026-04-06"
        """
        completed_on = date.fromisoformat(
            self.last_completed_date if self.last_completed_date else date.today().isoformat()
        )
        intervals = {"daily": timedelta(days=1), "weekly": timedelta(days=7)}
        interval = intervals.get(self.frequency)
        next_due = (completed_on + interval).isoformat() if interval else None

        return replace(self, completed=False, last_completed_date=None, due_date=next_due)

    def is_due_today(self, today: str | None = None) -> bool:
        """
        Returns True if this task should appear in today's schedule.

          - "as_needed" → due only if not yet completed (one-shot).
          - "daily" / "weekly" → compare due_date against today:
              · due_date is None  → never been completed, due immediately.
              · due_date <= today → the next occurrence has arrived.
              · due_date > today  → still in the future, skip for now.
        """
        if self.frequency == "as_needed":
            return not self.completed

        if self.due_date is None:
            return True  # brand-new task, not yet completed once

        today_date = date.fromisoformat(today or date.today().isoformat())
        return date.fromisoformat(self.due_date) <= today_date


@dataclass
class Pet:
    name: str
    species: str            # "dog" | "cat" | "other"
    owner: Owner = field(repr=False)
    _tasks: list[Task] = field(default_factory=list, init=False, repr=False)

    def get_tasks(self) -> list[Task]:
        """Returns all tasks associated with this pet."""
        return list(self._tasks)

    def get_tasks_by_status(self, completed: bool) -> list[Task]:
        """Returns tasks filtered by completion status."""
        return [t for t in self._tasks if t.completed == completed]

    def add_task(self, task: Task) -> None:
        """Adds a task to this pet's task list."""
        self._tasks.append(task)

    def complete_task(self, task: Task) -> Task | None:
        """
        Marks task complete and, for recurring frequencies, appends a
        fresh next occurrence to this pet's task list.

          "daily"     → next occurrence added immediately (due tomorrow).
          "weekly"    → next occurrence added immediately (due in 7 days).
          "as_needed" → no next occurrence; returns None.

        Returns the newly created Task, or None if the task is one-shot.
        """
        task.mark_complete()
        if task.frequency in ("daily", "weekly"):
            next_task = task.as_next_occurrence()
            self._tasks.append(next_task)
            return next_task
        return None


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

    def filter_tasks(
        self,
        completed: bool | None = None,
        pet_name: str | None = None,
    ) -> list[Task]:
        """
        Returns tasks that match ALL supplied filters (filters are AND-ed).

          completed  – True → only done tasks; False → only pending tasks;
                       None → ignore completion status.
          pet_name   – case-insensitive pet name to restrict results;
                       None → include tasks from every pet.

        Examples
        --------
        owner.filter_tasks(completed=False)              # all pending tasks
        owner.filter_tasks(pet_name="Buddy")             # all of Buddy's tasks
        owner.filter_tasks(completed=True, pet_name="Buddy")  # Buddy's done tasks
        """
        results: list[Task] = []
        for pet in self._pets:
            if pet_name and pet.name.lower() != pet_name.lower():
                continue
            for task in pet.get_tasks():
                if completed is not None and task.completed != completed:
                    continue
                results.append(task)
        return results


@dataclass
class DailyPlan:
    scheduled_tasks: list[Task] = field(default_factory=list)
    skipped_tasks: list[Task] = field(default_factory=list)
    conflicts: list[str] = field(default_factory=list)
    total_duration: int = 0
    explanations: list[str] = field(default_factory=list)

    def summary(self) -> str:
        """Formats the plan as a readable string for display in the UI."""
        lines = [f"=== Daily Plan | {self.total_duration} min scheduled ===", ""]

        lines.append("Scheduled:")
        for task in self.scheduled_tasks:
            slot = f" [{task.preferred_time}]" if task.preferred_time != "any" else ""
            lines.append(
                f"  [x] {task.title}{slot} — {task.duration_minutes} min ({task.priority})"
            )

        if self.skipped_tasks:
            lines.append("\nSkipped:")
            for task in self.skipped_tasks:
                lines.append(
                    f"  [ ] {task.title} — {task.duration_minutes} min ({task.priority})"
                )

        if self.conflicts:
            lines.append("\nConflicts:")
            for c in self.conflicts:
                lines.append(f"  ⚠ {c}")

        if self.explanations:
            lines.append("\nReasoning:")
            for note in self.explanations:
                lines.append(f"  - {note}")

        return "\n".join(lines)


class Scheduler:
    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get_candidates(
        self,
        pet_filter: str | None = None,
        today: str | None = None,
    ) -> list[tuple[Pet, Task]]:
        """
        Returns (pet, task) pairs that are incomplete and due today.
        Optionally restricted to a single pet by name.
        """
        pairs = []
        for pet in self.owner.get_pets():
            if pet_filter and pet.name.lower() != pet_filter.lower():
                continue
            for task in pet.get_tasks():
                if not task.completed and task.is_due_today(today):
                    pairs.append((pet, task))
        return pairs

    def _sort_candidates(
        self,
        candidates: list[tuple[Pet, Task]],
    ) -> list[tuple[Pet, Task]]:
        """
        Sorts tasks using three tiers:
          1. Time-slot alignment — tasks matching the owner's preferred
             time_of_day come first; "any" tasks float in the middle.
          2. Priority — high before medium before low.
          3. Category order — meds → feeding → walk → grooming → enrichment.
        """
        preferred_time = self.owner.preferences.get("time_of_day", "morning")

        def sort_key(pair: tuple[Pet, Task]) -> tuple[int, int, int]:
            _, task = pair
            if task.preferred_time == preferred_time:
                time_rank = 0
            elif task.preferred_time == "any":
                time_rank = 1
            else:
                time_rank = 2
            priority_rank = -PRIORITY_ORDER.get(task.priority, 0)  # negate → higher first
            category_rank = CATEGORY_ORDER.get(task.category, 99)
            return (time_rank, priority_rank, category_rank)

        return sorted(candidates, key=sort_key)

    def _detect_time_conflicts(
        self,
        scheduled_pairs: list[tuple[Pet, Task]],
    ) -> list[str]:
        """
        Lightweight time-overlap detection across all scheduled tasks.

        Overlap test:  start_A < end_B  AND  start_B < end_A

        Simplifications vs. the naive nested-index approach
        ----------------------------------------------------
        1. Pre-compute windows — each task's (start, end) is calculated
           once into a flat list before any comparisons, so _hhmm_to_minutes
           is never called more than once per task.

        2. itertools.combinations(windows, 2) — replaces the manual
           "for i in range / for j in range(i+1, len(...))" pattern.
           combinations produces every unique pair in one readable line,
           with clean tuple unpacking instead of index arithmetic.
        """
        warnings: list[str] = []

        # Build (pet, task, start, end) once per timed task
        windows = [
            (pet, task,
             _hhmm_to_minutes(task.scheduled_time),
             _hhmm_to_minutes(task.scheduled_time) + task.duration_minutes)
            for pet, task in scheduled_pairs
            if task.scheduled_time
        ]

        for (pet_a, task_a, start_a, end_a), (pet_b, task_b, start_b, end_b) in combinations(windows, 2):
            if start_a < end_b and start_b < end_a:
                overlap_minutes = min(end_a, end_b) - max(start_a, start_b)
                warnings.append(
                    f"Time conflict: [{pet_a.name}] '{task_a.title}' "
                    f"({task_a.scheduled_time}–{_minutes_to_hhmm(end_a)}) "
                    f"overlaps [{pet_b.name}] '{task_b.title}' "
                    f"({task_b.scheduled_time}–{_minutes_to_hhmm(end_b)}) "
                    f"— {overlap_minutes} min overlap."
                )

        return warnings

    def _detect_conflicts(self, scheduled: list[Task]) -> list[str]:
        """
        Inspects the ordered scheduled list for two types of conflict:

        1. Back-to-back — two consecutive tasks share a category that
           shouldn't repeat without a break (e.g. walk → walk).
        2. Ordering violation — a task that must precede another
           (e.g. meds before feeding) appears later in the plan.
        """
        conflicts: list[str] = []

        # Back-to-back check
        for i in range(len(scheduled) - 1):
            curr, nxt = scheduled[i], scheduled[i + 1]
            if (curr.category, nxt.category) in CONFLICTING_BACK_TO_BACK:
                conflicts.append(
                    f"'{curr.title}' followed immediately by '{nxt.title}' "
                    f"— two '{curr.category}' tasks back-to-back."
                )

        # Ordering-violation check
        cats = [t.category for t in scheduled]
        for before_cat, after_cat in MUST_PRECEDE.items():
            if before_cat in cats and after_cat in cats:
                if cats.index(before_cat) > cats.index(after_cat):
                    conflicts.append(
                        f"'{after_cat}' is scheduled before '{before_cat}' "
                        f"— {before_cat} should always precede {after_cat}."
                    )

        return conflicts

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build_plan(
        self,
        pet_filter: str | None = None,
        today: str | None = None,
    ) -> DailyPlan:
        """
        Builds a daily plan by:
          1. Collecting tasks that are incomplete and due today
             (optionally restricted to one pet via pet_filter).
          2. Sorting by time-slot preference, priority, then category order.
          3. Greedily fitting tasks into the owner's time budget.
          4. Running conflict detection on the final scheduled order.
        """
        plan = DailyPlan()
        remaining = self.owner.get_available_time()

        candidates = self._get_candidates(pet_filter=pet_filter, today=today)
        sorted_candidates = self._sort_candidates(candidates)

        # Track (pet, task) pairs for the scheduled tasks so time-conflict
        # detection can include the pet name in its warning messages.
        scheduled_pairs: list[tuple[Pet, Task]] = []

        for pet, task in sorted_candidates:
            if task.is_feasible(remaining):
                plan.scheduled_tasks.append(task)
                scheduled_pairs.append((pet, task))
                plan.total_duration += task.duration_minutes
                remaining -= task.duration_minutes
                plan.explanations.append(
                    f"[{pet.name}] '{task.title}' scheduled — "
                    f"{task.duration_minutes} min used, {remaining} min remaining."
                )
            else:
                plan.skipped_tasks.append(task)
                plan.explanations.append(
                    f"[{pet.name}] '{task.title}' skipped — "
                    f"needs {task.duration_minutes} min, only {remaining} min left."
                )

        plan.conflicts = (
            self._detect_conflicts(plan.scheduled_tasks)
            + self._detect_time_conflicts(scheduled_pairs)
        )

        return plan

    def complete_task(self, pet: Pet, task: Task) -> Task | None:
        """
        Marks a task complete via its owning pet and returns the next
        occurrence if one was auto-created, or None for as_needed tasks.

        Keeps scheduling logic centralised: callers only need the Scheduler.
        """
        return pet.complete_task(task)

    def explain_plan(self) -> list[str]:
        """Returns only the reasoning notes from the built plan."""
        return self.build_plan().explanations
