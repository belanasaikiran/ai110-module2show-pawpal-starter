import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, sort_by_time

# --- Session state guards ---
if "owner" not in st.session_state:
    st.session_state.owner = None

if "pet" not in st.session_state:
    st.session_state.pet = None

if "plan" not in st.session_state:
    st.session_state.plan = None

# ---------------------------------------------------------------------------

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# --- Section 1: Owner + Pet setup ---
st.subheader("1. Owner & Pet")

col1, col2 = st.columns(2)
with col1:
    owner_name = st.text_input("Owner name", value="Jordan")
    available_minutes = st.number_input(
        "Available minutes today", min_value=10, max_value=480, value=90
    )
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])

time_of_day = st.selectbox(
    "Preferred time of day",
    ["morning", "afternoon", "evening"],
    help="Tasks that match this preference are scheduled first.",
)

if st.button("Set up Owner & Pet"):
    owner = Owner(
        name=owner_name,
        available_minutes=int(available_minutes),
        preferences={"time_of_day": time_of_day},
    )
    pet = Pet(name=pet_name, species=species, owner=owner)
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pet = pet
    st.session_state.plan = None
    st.success(
        f"Ready! {owner_name} owns {pet_name} the {species} "
        f"with {available_minutes} min today ({time_of_day} preference)."
    )

st.divider()

# --- Section 2: Add tasks ---
st.subheader("2. Tasks")

if st.session_state.pet is None:
    st.info("Set up an owner and pet above before adding tasks.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
        category = st.selectbox(
            "Category", ["walk", "feeding", "meds", "grooming", "enrichment"]
        )
    with col2:
        duration = st.number_input(
            "Duration (minutes)", min_value=1, max_value=240, value=20
        )
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
    with col3:
        preferred_time = st.selectbox(
            "Preferred time", ["any", "morning", "afternoon", "evening"]
        )
        scheduled_time_input = st.text_input(
            "Scheduled time (HH:MM, optional)", value="",
            help="Pin this task to a clock time for overlap detection (e.g. 09:00)."
        )

    scheduled_time = scheduled_time_input.strip() or None

    if st.button("Add task"):
        task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            category=category,
            preferred_time=preferred_time,
            scheduled_time=scheduled_time,
        )
        st.session_state.pet.add_task(task)
        st.session_state.plan = None
        st.success(f"Added '{task_title}' ({duration} min, {priority} priority).")

    # Display current tasks sorted chronologically via sort_by_time()
    current_tasks = st.session_state.pet.get_tasks()
    if current_tasks:
        sorted_tasks = sort_by_time(current_tasks)
        st.write(f"Tasks for **{st.session_state.pet.name}** (sorted by scheduled time):")
        st.table([
            {
                "Title": t.title,
                "Category": t.category,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Preferred time": t.preferred_time,
                "Scheduled at": t.scheduled_time or "—",
                "Done": "Yes" if t.completed else "No",
            }
            for t in sorted_tasks
        ])
    else:
        st.info("No tasks yet. Add one above.")

st.divider()

# --- Section 3: Generate schedule ---
st.subheader("3. Build Schedule")

if st.session_state.owner is None:
    st.info("Set up an owner and pet first.")
elif not st.session_state.owner.get_all_tasks():
    st.info("Add at least one task before generating a schedule.")
else:
    if st.button("Generate schedule"):
        scheduler = Scheduler(st.session_state.owner)
        st.session_state.plan = scheduler.build_plan()

    if st.session_state.plan is not None:
        plan = st.session_state.plan

        # --- Summary banner ---
        skipped_count = len(plan.skipped_tasks)
        conflict_count = len(plan.conflicts)
        if conflict_count > 0:
            st.warning(
                f"Plan built with {conflict_count} conflict(s) — "
                f"{plan.total_duration} min scheduled, {skipped_count} task(s) skipped. "
                "Review the warnings below."
            )
        else:
            st.success(
                f"Plan looks good — {plan.total_duration} min scheduled, "
                f"{skipped_count} task(s) skipped, no conflicts."
            )

        # --- Conflict warnings ---
        if plan.conflicts:
            st.markdown("#### Scheduling Conflicts")
            for conflict in plan.conflicts:
                # Provide a plain-English action hint alongside the technical message
                if "overlap" in conflict.lower():
                    tip = "Try giving these tasks non-overlapping start times."
                elif "back-to-back" in conflict.lower():
                    tip = "Consider adding a break or a different task in between."
                elif "precede" in conflict.lower() or "before" in conflict.lower():
                    tip = "Reorder tasks so medications come before feeding."
                else:
                    tip = "Review your task order or timing."
                st.warning(f"**{conflict}**\n\n*Suggestion: {tip}*")

        # --- Scheduled tasks table ---
        if plan.scheduled_tasks:
            st.markdown("#### Scheduled Tasks")
            # sort_by_time from Scheduler keeps timed tasks in clock order for display
            display_tasks = sort_by_time(plan.scheduled_tasks)
            st.table([
                {
                    "Title": t.title,
                    "Category": t.category,
                    "Duration (min)": t.duration_minutes,
                    "Priority": t.priority,
                    "Scheduled at": t.scheduled_time or "—",
                }
                for t in display_tasks
            ])

        # --- Skipped tasks table ---
        if plan.skipped_tasks:
            st.markdown("#### Skipped Tasks (not enough time)")
            st.table([
                {
                    "Title": t.title,
                    "Category": t.category,
                    "Duration (min)": t.duration_minutes,
                    "Priority": t.priority,
                }
                for t in plan.skipped_tasks
            ])

        # --- Scheduler reasoning (collapsed by default) ---
        if plan.explanations:
            with st.expander("Why did the scheduler make these choices?"):
                for note in plan.explanations:
                    st.write(f"- {note}")
