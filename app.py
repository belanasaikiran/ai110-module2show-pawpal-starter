import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

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
    available_minutes = st.number_input("Available minutes today", min_value=10, max_value=480, value=90)
with col2:
    pet_name = st.text_input("Pet name", value="Mochi")
    species = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Set up Owner & Pet"):
    owner = Owner(name=owner_name, available_minutes=int(available_minutes), preferences={})
    pet = Pet(name=pet_name, species=species, owner=owner)
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pet = pet
    st.session_state.plan = None   # reset any previous plan
    st.success(f"Ready! {owner_name} owns {pet_name} the {species} with {available_minutes} min today.")

st.divider()

# --- Section 2: Add tasks ---
st.subheader("2. Tasks")

if st.session_state.pet is None:
    st.info("Set up an owner and pet above before adding tasks.")
else:
    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

    if st.button("Add task"):
        task = Task(title=task_title, duration_minutes=int(duration), priority=priority, category="general")
        st.session_state.pet.add_task(task)   # Pet owns the task list
        st.session_state.plan = None           # reset plan so it can be regenerated
        st.success(f"Added '{task_title}' ({duration} min, {priority} priority).")

    current_tasks = st.session_state.pet.get_tasks()
    if current_tasks:
        st.write(f"Tasks for **{st.session_state.pet.name}**:")
        st.table([
            {"title": t.title, "duration_minutes": t.duration_minutes, "priority": t.priority, "completed": t.completed}
            for t in current_tasks
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
        st.success(f"Plan built — {plan.total_duration} min scheduled, {len(plan.skipped_tasks)} task(s) skipped.")
        st.text(plan.summary())
