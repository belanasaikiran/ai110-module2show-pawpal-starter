from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------
owner = Owner(
    name="Alex",
    available_minutes=180,
    preferences={"time_of_day": "morning"},
)

buddy    = Pet(name="Buddy",    species="dog", owner=owner)
whiskers = Pet(name="Whiskers", species="cat", owner=owner)
owner.add_pet(buddy)
owner.add_pet(whiskers)

# ---------------------------------------------------------------------------
# Tasks — some intentionally overlap to trigger time-conflict warnings
#
#  08:00 ──┬── Breakfast (10 min) ──┤ 08:10         [Buddy]
#  08:00 ──┼── Morning Meds (5 min) ┤ 08:05         [Whiskers] EXACT same start
#  08:05 ──┼── Wet Food (10 min) ───┤ 08:15         [Whiskers] overlaps Breakfast
#  09:00 ──┴── Morning Walk (30 min)┤ 09:30         [Buddy]    no conflict
#  11:00 ─── Grooming (25 min) ─────┤ 11:25         [Buddy]    no conflict
# ---------------------------------------------------------------------------

buddy.add_task(Task(
    "Breakfast",
    duration_minutes=10, priority="high", category="feeding",
    scheduled_time="08:00",           # 08:00 – 08:10
))
buddy.add_task(Task(
    "Morning Walk",
    duration_minutes=30, priority="high", category="walk",
    scheduled_time="09:00",           # 09:00 – 09:30  (no conflict)
))
buddy.add_task(Task(
    "Grooming Session",
    duration_minutes=25, priority="medium", category="grooming",
    scheduled_time="11:00",           # 11:00 – 11:25  (no conflict)
))

whiskers.add_task(Task(
    "Morning Meds",
    duration_minutes=5, priority="high", category="meds",
    scheduled_time="08:00",           # 08:00 – 08:05  ← exact same start as Breakfast
))
whiskers.add_task(Task(
    "Wet Food Feeding",
    duration_minutes=10, priority="high", category="feeding",
    scheduled_time="08:05",           # 08:05 – 08:15  ← overlaps Breakfast (08:00–08:10)
))

# ---------------------------------------------------------------------------
# DEMO 1 — Full schedule, expecting two time-conflict warnings
# ---------------------------------------------------------------------------
print("=" * 60)
print("DEMO 1 — Two deliberate time conflicts")
print("=" * 60)
scheduler = Scheduler(owner)
plan = scheduler.build_plan()
print(plan.summary())

# Verify programmatically
time_conflicts = [c for c in plan.conflicts if "Time conflict" in c]
print(f"\nTime-conflict warnings found: {len(time_conflicts)}")
for w in time_conflicts:
    print(f"  {w}")

assert len(time_conflicts) == 2, (
    f"Expected 2 time-conflict warnings, got {len(time_conflicts)}"
)
print("\nPASS — Scheduler caught both overlaps without crashing.")

# ---------------------------------------------------------------------------
# DEMO 2 — Tasks with NO scheduled_time are ignored by time-conflict check
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("DEMO 2 — Tasks without scheduled_time are safely skipped")
print("=" * 60)

owner2 = Owner(name="Sam", available_minutes=60, preferences={})
rex = Pet(name="Rex", species="dog", owner=owner2)
owner2.add_pet(rex)

rex.add_task(Task("Walk",    duration_minutes=20, priority="high",   category="walk"))
rex.add_task(Task("Feeding", duration_minutes=10, priority="medium", category="feeding"))

plan2 = Scheduler(owner2).build_plan()
time_conflicts2 = [c for c in plan2.conflicts if "Time conflict" in c]
print(f"  Time-conflict warnings: {len(time_conflicts2)}  (expected: 0)")
assert len(time_conflicts2) == 0
print("  PASS — no false positives for un-timed tasks.")

# ---------------------------------------------------------------------------
# DEMO 3 — Same-pet overlap (both tasks belong to Buddy)
# ---------------------------------------------------------------------------
print("\n" + "=" * 60)
print("DEMO 3 — Same-pet overlap (both tasks on Buddy)")
print("=" * 60)

owner3 = Owner(name="Jo", available_minutes=120, preferences={})
max_pet = Pet(name="Max", species="dog", owner=owner3)
owner3.add_pet(max_pet)

max_pet.add_task(Task(
    "Morning Walk",
    duration_minutes=30, priority="high", category="walk",
    scheduled_time="07:00",          # 07:00 – 07:30
))
max_pet.add_task(Task(
    "Breakfast",
    duration_minutes=15, priority="high", category="feeding",
    scheduled_time="07:20",          # 07:20 – 07:35  ← overlaps walk by 10 min
))

plan3 = Scheduler(owner3).build_plan()
same_pet_conflicts = [c for c in plan3.conflicts if "Time conflict" in c]
print(f"  Same-pet time-conflict warnings: {len(same_pet_conflicts)}  (expected: 1)")
for w in same_pet_conflicts:
    print(f"  {w}")
assert len(same_pet_conflicts) == 1
print("  PASS")
