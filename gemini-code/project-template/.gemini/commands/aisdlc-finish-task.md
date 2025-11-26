Complete the specified task and create a finished task document.

**Usage**: `finish-task {task_id}`

**Instructions**:

1. **Read** `.ai-workspace/tasks/active/ACTIVE_TASKS.md` to find the details of the specified task.
2. **Verify that the task is complete**:
   - All tests are passing.
   - All acceptance criteria have been met.
   - The code has been reviewed and refactored.
3. **Create a finished task document**:
   - Copy the template from `.ai-workspace/templates/FINISHED_TASK_TEMPLATE.md`.
   - Name the new file `.ai-workspace/tasks/finished/{YYYYMMDD_HHMM}_{task_slug}.md`.
   - Fill in all sections of the template with information from the completed task, including:
     - The problem that was solved.
     - The investigation that was performed.
     - The solution that was implemented.
     - The files that were modified.
     - The testing that was performed.
     - The final result.
4. **Remove the task** from `.ai-workspace/tasks/active/ACTIVE_TASKS.md`.
5. **Confirm** that the task has been finished and the document has been created: "✅ Task #{id} finished. Document created at: {path}"

**Important**: The finished task document is a valuable piece of documentation. Please fill it out thoroughly and accurately.
