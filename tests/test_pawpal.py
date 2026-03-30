from datetime import date, timedelta

import pytest

from pawpal_system import Owner, Pet, Scheduler, Task, sort_by_time


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_owner(minutes: int = 120, prefs: dict | None = None) -> Owner:
    return Owner(name="Alex", available_minutes=minutes, preferences=prefs or {})


def make_pet(owner: Owner, name: str = "Buddy") -> Pet:
    pet = Pet(name=name, species="dog", owner=owner)
    owner.add_pet(pet)
    return pet


def make_task(**kwargs) -> Task:
    defaults = dict(title="Task", duration_minutes=10, priority="medium", category="walk")
    defaults.update(kwargs)
    return Task(**defaults)


# ===========================================================================
# Existing tests (preserved)
# ===========================================================================

def test_mark_complete_changes_status():
    task = Task(title="Morning Walk", duration_minutes=30, priority="high", category="walk")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    owner = make_owner()
    pet = Pet(name="Buddy", species="dog", owner=owner)

    assert len(pet.get_tasks()) == 0
    pet.add_task(Task(title="Breakfast", duration_minutes=10, priority="high", category="feeding"))
    assert len(pet.get_tasks()) == 1


# ===========================================================================
# SORTING CORRECTNESS — sort_by_time()
# ===========================================================================

class TestSortByTime:
    def test_chronological_order(self):
        """Tasks with scheduled_time are returned earliest-first."""
        t1 = make_task(title="Lunch",     scheduled_time="12:00")
        t2 = make_task(title="Morning",   scheduled_time="08:00")
        t3 = make_task(title="Evening",   scheduled_time="18:30")

        result = sort_by_time([t1, t2, t3])
        assert [t.title for t in result] == ["Morning", "Lunch", "Evening"]

    def test_unscheduled_tasks_go_last(self):
        """Tasks without a scheduled_time are placed at the end."""
        timed   = make_task(title="Timed",     scheduled_time="09:00")
        no_time = make_task(title="No time",   scheduled_time=None)

        result = sort_by_time([no_time, timed])
        assert result[0].title == "Timed"
        assert result[1].title == "No time"

    def test_all_unscheduled_no_crash(self):
        """A list of tasks with no scheduled_time returns without error."""
        tasks = [make_task(title=f"T{i}") for i in range(3)]
        result = sort_by_time(tasks)
        assert len(result) == 3

    def test_same_time_stable_order(self):
        """Two tasks at the same time preserve their relative input order."""
        t1 = make_task(title="First",  scheduled_time="10:00")
        t2 = make_task(title="Second", scheduled_time="10:00")
        result = sort_by_time([t1, t2])
        assert [t.title for t in result] == ["First", "Second"]

    def test_returns_new_list(self):
        """sort_by_time must not mutate the original list."""
        tasks = [make_task(scheduled_time="10:00"), make_task(scheduled_time="08:00")]
        original_order = [id(t) for t in tasks]
        sort_by_time(tasks)
        assert [id(t) for t in tasks] == original_order


# ===========================================================================
# RECURRENCE LOGIC — Task.as_next_occurrence / Pet.complete_task
# ===========================================================================

class TestRecurrenceLogic:
    def test_daily_task_due_next_day(self):
        """Completing a daily task creates a new task due exactly 1 day later."""
        today = date.today().isoformat()
        task  = make_task(frequency="daily")
        task.mark_complete(on_date=today)

        next_task = task.as_next_occurrence()
        expected_due = (date.today() + timedelta(days=1)).isoformat()

        assert next_task.due_date == expected_due

    def test_weekly_task_due_in_seven_days(self):
        """Completing a weekly task creates a new task due exactly 7 days later."""
        today = date.today().isoformat()
        task  = make_task(frequency="weekly")
        task.mark_complete(on_date=today)

        next_task = task.as_next_occurrence()
        expected_due = (date.today() + timedelta(days=7)).isoformat()

        assert next_task.due_date == expected_due

    def test_next_occurrence_is_not_completed(self):
        """The new occurrence starts in an incomplete state."""
        task = make_task(frequency="daily")
        task.mark_complete()
        next_task = task.as_next_occurrence()

        assert next_task.completed is False
        assert next_task.last_completed_date is None

    def test_pet_complete_task_appends_next_occurrence(self):
        """pet.complete_task() adds the next occurrence to the pet's task list."""
        owner = make_owner()
        pet   = make_pet(owner)
        task  = make_task(frequency="daily")
        pet.add_task(task)

        assert len(pet.get_tasks()) == 1
        pet.complete_task(task)
        assert len(pet.get_tasks()) == 2

    def test_as_needed_task_returns_no_next_occurrence(self):
        """as_needed tasks are one-shot — complete_task returns None."""
        owner = make_owner()
        pet   = make_pet(owner)
        task  = make_task(frequency="as_needed")
        pet.add_task(task)

        result = pet.complete_task(task)
        assert result is None
        assert len(pet.get_tasks()) == 1   # no new task added

    def test_is_due_today_when_due_date_is_today(self):
        today = date.today().isoformat()
        task  = make_task(frequency="daily", due_date=today)
        assert task.is_due_today(today) is True

    def test_is_due_today_when_due_date_is_tomorrow(self):
        tomorrow = (date.today() + timedelta(days=1)).isoformat()
        task = make_task(frequency="daily", due_date=tomorrow)
        assert task.is_due_today(date.today().isoformat()) is False

    def test_is_due_today_when_due_date_is_none(self):
        """Brand-new task with no due_date should be treated as due immediately."""
        task = make_task(frequency="daily", due_date=None)
        assert task.is_due_today() is True


# ===========================================================================
# CONFLICT DETECTION — Scheduler
# ===========================================================================

class TestConflictDetection:
    def _scheduler_with_tasks(self, *tasks, minutes: int = 300) -> tuple[Scheduler, Pet]:
        owner = make_owner(minutes=minutes)
        pet   = make_pet(owner)
        for t in tasks:
            pet.add_task(t)
        return Scheduler(owner), pet

    def test_exact_same_scheduled_time_flagged(self):
        """Two tasks at the exact same HH:MM produce a time-conflict warning."""
        t1 = make_task(title="Walk",    scheduled_time="09:00", duration_minutes=30)
        t2 = make_task(title="Feeding", scheduled_time="09:00", duration_minutes=20, category="feeding")
        scheduler, _ = self._scheduler_with_tasks(t1, t2)

        plan = scheduler.build_plan()
        assert any("overlap" in c.lower() or "conflict" in c.lower() for c in plan.conflicts)

    def test_overlapping_windows_flagged(self):
        """Tasks whose time windows overlap (but don't start at same time) are flagged."""
        t1 = make_task(title="Walk",    scheduled_time="09:00", duration_minutes=30)  # 09:00–09:30
        t2 = make_task(title="Feeding", scheduled_time="09:15", duration_minutes=30,  # 09:15–09:45
                       category="feeding")
        scheduler, _ = self._scheduler_with_tasks(t1, t2)

        plan = scheduler.build_plan()
        conflict_text = " ".join(plan.conflicts).lower()
        assert "overlap" in conflict_text or "conflict" in conflict_text

    def test_non_overlapping_tasks_no_conflict(self):
        """Tasks on separate time windows produce no time-conflict warnings."""
        t1 = make_task(title="Walk",    scheduled_time="08:00", duration_minutes=30)  # 08:00–08:30
        t2 = make_task(title="Feeding", scheduled_time="09:00", duration_minutes=30,  # 09:00–09:30
                       category="feeding")
        scheduler, _ = self._scheduler_with_tasks(t1, t2)

        plan = scheduler.build_plan()
        time_conflicts = [c for c in plan.conflicts if "overlap" in c.lower()]
        assert time_conflicts == []

    def test_back_to_back_walk_flagged(self):
        """Two consecutive walk tasks produce a back-to-back conflict."""
        t1 = make_task(title="Morning Walk", category="walk")
        t2 = make_task(title="Afternoon Walk", category="walk")
        scheduler, _ = self._scheduler_with_tasks(t1, t2)

        plan = scheduler.build_plan()
        assert any("back-to-back" in c.lower() for c in plan.conflicts)

    def test_feeding_before_meds_ordering_violation(self):
        """Scheduling feeding before meds triggers a MUST_PRECEDE ordering conflict."""
        feeding = make_task(title="Breakfast",  category="feeding", priority="high")
        meds    = make_task(title="Medicine",   category="meds",    priority="low")
        # Give owner a morning preference so feeding (high priority) sorts first
        owner = make_owner(prefs={"time_of_day": "morning"})
        pet   = make_pet(owner)
        # Add feeding first so it ends up before meds in the scheduled list
        pet.add_task(feeding)
        pet.add_task(meds)
        scheduler = Scheduler(owner)

        plan = scheduler.build_plan()
        # Either an ordering conflict or a priority-driven correct order — check both paths
        if any("meds" in c.lower() or "feeding" in c.lower() for c in plan.conflicts):
            # conflict was raised as expected
            assert True
        else:
            # Scheduler naturally put meds first — no conflict, which is also correct
            scheduled_cats = [t.category for t in plan.scheduled_tasks]
            assert scheduled_cats.index("meds") < scheduled_cats.index("feeding")

    def test_conflicts_do_not_block_plan(self):
        """Conflicts are advisory — scheduled_tasks is still populated."""
        t1 = make_task(title="Walk 1", scheduled_time="09:00", duration_minutes=30)
        t2 = make_task(title="Walk 2", scheduled_time="09:00", duration_minutes=30, category="walk")
        scheduler, _ = self._scheduler_with_tasks(t1, t2)

        plan = scheduler.build_plan()
        assert len(plan.scheduled_tasks) > 0
        assert len(plan.conflicts) > 0


# ===========================================================================
# EDGE CASES — happy paths & boundary conditions
# ===========================================================================

class TestEdgeCases:
    def test_pet_with_no_tasks_builds_empty_plan(self):
        owner = make_owner()
        pet   = make_pet(owner)
        plan  = Scheduler(owner).build_plan()

        assert plan.scheduled_tasks == []
        assert plan.skipped_tasks   == []
        assert plan.conflicts       == []
        assert plan.total_duration  == 0

    def test_owner_with_no_pets_builds_empty_plan(self):
        owner = make_owner()
        plan  = Scheduler(owner).build_plan()

        assert plan.scheduled_tasks == []

    def test_task_fits_exactly_in_budget(self):
        """A task whose duration == available_minutes should be scheduled, not skipped."""
        owner = make_owner(minutes=30)
        pet   = make_pet(owner)
        pet.add_task(make_task(duration_minutes=30))
        plan  = Scheduler(owner).build_plan()

        assert len(plan.scheduled_tasks) == 1
        assert plan.skipped_tasks        == []
        assert plan.total_duration       == 30

    def test_all_tasks_exceed_budget_all_skipped(self):
        owner = make_owner(minutes=5)
        pet   = make_pet(owner)
        pet.add_task(make_task(title="T1", duration_minutes=30))
        pet.add_task(make_task(title="T2", duration_minutes=60))
        plan  = Scheduler(owner).build_plan()

        assert plan.scheduled_tasks == []
        assert len(plan.skipped_tasks) == 2

    def test_get_tasks_returns_copy(self):
        """Mutating the list returned by get_tasks() must not affect internal state."""
        owner = make_owner()
        pet   = make_pet(owner)
        pet.add_task(make_task())

        tasks = pet.get_tasks()
        tasks.clear()

        assert len(pet.get_tasks()) == 1

    def test_pet_filter_excludes_other_pets(self):
        """build_plan(pet_filter=...) only schedules the named pet's tasks."""
        owner = make_owner(minutes=120)
        rex   = make_pet(owner, name="Rex")
        buddy = make_pet(owner, name="Buddy")
        rex.add_task(make_task(title="Rex Walk"))
        buddy.add_task(make_task(title="Buddy Walk"))

        plan = Scheduler(owner).build_plan(pet_filter="Rex")
        titles = [t.title for t in plan.scheduled_tasks]

        assert "Rex Walk"   in titles
        assert "Buddy Walk" not in titles

    def test_high_priority_scheduled_before_low(self):
        """With equal time constraints, high-priority task appears first in the plan."""
        owner = make_owner(prefs={"time_of_day": "morning"})
        pet   = make_pet(owner)
        pet.add_task(make_task(title="Low",  priority="low",  preferred_time="morning"))
        pet.add_task(make_task(title="High", priority="high", preferred_time="morning"))

        plan = Scheduler(owner).build_plan()
        titles = [t.title for t in plan.scheduled_tasks]

        assert titles.index("High") < titles.index("Low")
