from pawpal_system import Owner, Pet, Task, Scheduler

# --- Setup ---
owner = Owner(
    name="Alex",
    available_minutes=90,
    preferences={"time_of_day": "morning", "avoid": "late_feeding"},
)

buddy = Pet(name="Buddy", species="dog", owner=owner)
whiskers = Pet(name="Whiskers", species="cat", owner=owner)

owner.add_pet(buddy)
owner.add_pet(whiskers)

# --- Tasks for Buddy (dog) ---
buddy.add_task(Task("Morning Walk",     duration_minutes=30, priority="high",   category="walk"))
buddy.add_task(Task("Breakfast",        duration_minutes=10, priority="high",   category="feeding"))
buddy.add_task(Task("Grooming Session", duration_minutes=25, priority="medium", category="grooming"))

# --- Tasks for Whiskers (cat) ---
whiskers.add_task(Task("Wet Food Feeding", duration_minutes=10, priority="high",   category="feeding"))
whiskers.add_task(Task("Flea Treatment",   duration_minutes=15, priority="medium", category="meds",      frequency="weekly"))
whiskers.add_task(Task("Play / Enrichment",duration_minutes=20, priority="low",    category="enrichment"))

# --- Generate plan ---
scheduler = Scheduler(owner)
plan = scheduler.build_plan()

# --- Print ---
print("Today's Schedule")
print("=" * 40)
print(plan.summary())
