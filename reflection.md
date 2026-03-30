# PawPal+ Project Reflection

## 1. System Design

3 cpre actions a user should be able to perform in the app are:
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
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
