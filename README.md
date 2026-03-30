# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## Smarter Scheduling

The scheduler goes beyond a simple priority sort. Here is what was added and why.

### Multi-tier task sorting
Tasks are sorted across three tiers before any are placed into the plan:
1. **Time-slot alignment** — tasks whose `preferred_time` matches the owner's `time_of_day` preference go first.
2. **Priority** — `high` before `medium` before `low`.
3. **Category order** — `meds → feeding → walk → grooming → enrichment`, so medically important tasks always precede meals and exercise.

### Clock-time sorting
Every task can carry an optional `scheduled_time` in `"HH:MM"` format. `sort_by_time()` converts each string to total minutes since midnight with a lambda key and returns a new list ordered by actual clock time, with un-timed tasks placed at the end.

### Filtering by pet or status
`Owner.filter_tasks(completed, pet_name)` returns only the tasks that match every supplied filter (filters are AND-ed). Useful for showing a single pet's pending tasks or checking what has already been completed.

### Recurring task logic with `timedelta`
When a recurring task is marked complete, `Pet.complete_task()` automatically appends a fresh next occurrence with a computed `due_date`:
- `"daily"` tasks: `due_date = completed_on + timedelta(days=1)`
- `"weekly"` tasks: `due_date = completed_on + timedelta(days=7)`
- `"as_needed"` tasks: no next occurrence is created.

`Task.is_due_today()` then compares `due_date` against today — a single date comparison instead of counting elapsed days.

### Conflict detection
After the greedy pass, two checks run on the final scheduled list:

| Check | What it catches |
|---|---|
| Back-to-back | Two consecutive tasks share a category that should not repeat without a break (e.g. `walk → walk`). |
| Ordering violation | A category that must precede another appears later (e.g. `feeding` before `meds`). |
| Time-window overlap | Two tasks with `scheduled_time` set have overlapping intervals, detected with the standard `start_A < end_B AND start_B < end_A` test. |

All conflicts are returned as warning strings — the plan is never blocked or discarded.


## Testing PawPal+

Run the tests with:

```bash
python -m pytest
```

Confidence Level: 5

### Test classes

| Class	| Tests	| Covers
| --- | --- | ---
| TestSortByTime	| 5	| Chronological order, unscheduled tasks last, no-crash with all-None times, stable sort at equal times, immutability
| TestRecurrenceLogic	| 8	| Daily → +1 day, weekly → +7 days, next occurrence starts incomplete, complete_task appends to pet, as_needed returns None, is_due_today for today/tomorrow/None
| TestConflictDetection	| 6	| Exact same time flagged, overlapping windows flagged, non-overlapping clean, back-to-back walk, feeding-before-meds ordering, conflicts don't block the plan
| TestEdgeCases	| 7	| Pet with no tasks, owner with no pets, task fits exactly in budget, all tasks skipped, get_tasks returns a copy, pet_filter isolates one pet, high priority sorts before low
| Add/Mark Complete test cases | 2 | Adding a task to a pet, marking a task complete and checking next occurrence
