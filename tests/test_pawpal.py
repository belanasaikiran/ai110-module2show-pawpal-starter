from pawpal_system import Owner, Pet, Task


def test_mark_complete_changes_status():
    task = Task(title="Morning Walk", duration_minutes=30, priority="high", category="walk")
    assert task.completed is False
    task.mark_complete()
    assert task.completed is True


def test_add_task_increases_pet_task_count():
    owner = Owner(name="Alex", available_minutes=60, preferences={})
    pet = Pet(name="Buddy", species="dog", owner=owner)

    assert len(pet.get_tasks()) == 0
    pet.add_task(Task(title="Breakfast", duration_minutes=10, priority="high", category="feeding"))
    assert len(pet.get_tasks()) == 1
