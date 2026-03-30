# PawPal+ Project Reflection

## 1. System Design

3 core actions a user should be able to perform in the app are:
- add/manage pet and owner information
- add/edit pet care tasks (including duration and priority)
- generate and view a daily schedule/plan based on the entered information and constraints


**a. Initial design**

- Briefly describe your initial UML design.

Refer the file `uml.mermaid` for the mermaid diagram.

`Owner` class represents the pet owner, with attributes for their name, available time, and preferences. It has a method to calculate available time for tasks.

`Pet` is a data class for the pet being cared for. It has attibutes name, species, and a back reference to its owner. It has a method to get the list of tasks associated with the pet.

`Task` is a single care activity with title, duration, priority, category, and completion status. It has a method (`is_feasible()`) to check if it can fit within the remaining time. 

`Scheduler` is responsible for taking the owner, pet, and list of tasks and building a daily plan. It has methods to build the plan and explain the reasoning behind it.
- `buiild_plan()` is the core scheduling logic that selects and orders tasks based on constraints and priorities. 
- `explain_plan()` provides reasoning for why certain tasks were included or skipped.

`DailyPlan` is a data class that holds the scheduled tasks, skipped tasks, total duration, and explanations. It has a method to format the plan for display in the UI.



- What classes did you include, and what responsibilities did you assign to each?

- `Owner` 
    - **Responsibilities**:
        - Store owner information (name, available time, preferences)
        - Calculate available time for tasks
- `Pet`
    - **Responsibilities**:
        - Store pet information (name, species, owner)
        - Provide access to assigned tasks
- `Task`
    - **Responsibilities**:
        - Store task details (title, duration, priority, category, completion status)
        - Determine if the task is feasible in given available time
- `Scheduler`
    - **Responsibilities**:
        - Build a daily plan based on the owner, pet, and tasks
        - Give reasoning behind the generated plan
- `DailyPlan`
    - **Responsibilities**:
        - Store the results of the scheduling (scheduled tasks, skipped tasks, total duration, explanations)
        - Format the plan for display in the UI


**b. Design changes**

- Did your design change during implementation?
    Yes
- If yes, describe at least one change and why you made it.
    backward looking -> forward looking recurrence

    - In Original design, the Scheduler would work on one pet's task list, passed in manually from outside. That made the caller responsible for gathering and passing the right tasks every time.
    

    When implementing `build_plan()`, it became clear the Scheduler should be responsible for collecting tasks itself across all pets by walking owner -> get_pets() -> get_tasks(). Passing pet and tasks in as constructor arguments.


---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?

    - Time budget - Hard Constraint
    - Priority + Category - Orddering constraint
    - conflcts and detection of it - Soft constraint (explanation, not strictly enforced)

- How did you decide which constraints mattered most?

    - Time Budget - Without it the plan is meaningless . you can't schedule 4 hours of tasks into a 90-minute morning. It had to be a hard block.

    - Priority + Category - TThese made the greedy algorithm produce reasonable results without extra complexity. Meds before feeding is a real pet-health concern, not just a preference.

    - Conflict detection - Intentionally kept as warnings, not blockers. Crashing or refusing to build a plan because two tasks overlap is worse for a user than just being told about it.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.

    **Greedy first-fit schedyuling**: build_plan() sorts tasks once by priority/time and then walks down the list. the first task that fits the remaining budget is locked in immediately. No task is ever reconsidered.


- Why is that tradeoff reasonable for this scenario?

    Greedy gives you A + C (one high, one medium).

    ```
    budget = 60 min

    Task A  — 40 min, high priority    ← greedy picks this
    Task B  — 35 min, high priority    ← needs 35, only 20 left → skipped
    Task C  — 20 min, medium priority  ← fits the gap → scheduled
    ```
    
    A smarter approach would notice that skipping A lets you fit B + C (two tasks in nearly the same time), or that neither combination is clearly better and the owner should be asked.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?

- I used AI to designing and brainstorming when I was trying to figure out how to structure the Scheduler and DailyPlan classes. I asked suggestions on how to organize the scheduling logic and what attributes the DailyPlan should have.


- What kinds of prompts or questions were most helpful?

- "How should I structure the Scheduler class to build a daily plan based on owner, pet, and tasks?"
- "Generating a UML diagram for the app that includes Owner, Pet, Task, Scheduler, and DailyPlan classes with their attributes and methods." and "Explain the links"
- "Why a specific algorithm optmization would be better than a greedy approach for the scheduling problem?"

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.

  - It assumed something else and re-wrote the entire README. I had to stop it and had to take over in correcting the README.

- How did you evaluate or verify what the AI suggested?

  I read the README file and check what the AI has written for professional grade. It removed most the things that was suggested to be included in earlier phases.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?

 - Sorting correctness
 - Recurrence Logic
 - Edge cases such as pet with no taskks, owner with no pets, tasks that exceed the time budget, etc.

- Why were these tests important?

    - Sorting correctness ensures that the tasks are ordered properly by priority and time, which is fundamental to the scheduling logic.
    - Recurrence logic tests verify that daily and weekly tasks are rescheduled correctly after completion, which is key for ongoing pet care.
    - Edge cases test the robustness of the system and ensure it can handle real-world scenarios without crashing or producing nonsensical plans.

**b. Confidence**

- How confident are you that your scheduler works correctly?
 99%

- What edge cases would you test next if you had more time?

Add more people and add specific times

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
  - I'm most satisfied with the overall scheduling logic and how well it takes into account various constraints and priorities. 

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

    - I would implement a more better scheduling algorithm that considers more combinations of tasks rather than just a greedy first-fit approach. This would allow for better optimization of the owner's time and potentially include more high-priority tasks in the plan.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?

    - I learned while AI can be a powerful tool for brainstorming and generating ideas, it's crucial to maintain my judgment and sight of the project. Not all AI suggestions will be accurate, and it's important to evaluate them and make  decisions about what to accept or reject.