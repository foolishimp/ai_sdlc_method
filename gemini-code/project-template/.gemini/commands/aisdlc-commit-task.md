Commit a completed task using information from the finished task document.

**Usage**: `commit-task {task_id}`

**Instructions**:

1. **Find the finished task document** in `.ai-workspace/tasks/finished/`
   - Look for the most recent file matching the task ID.
2. **Read the finished task document** to gather the necessary information for the commit.
3. **Generate a commit message** using this format:
   ```
   Task #{id}: {title}

   {A brief summary of the problem addressed by the task.}

   {A brief summary of the solution implemented.}

   Tests: {A summary of the testing performed.}
   TDD: RED → GREEN → REFACTOR

   Implements: {Any requirement keys (REQ-*) implemented by this task.}

   🤖 Generated with Gemini
   Co-Authored-By: Gemini <noreply@google.com>
   ```
4. **Show the generated commit message** to the user and ask for their approval.
5. **If approved**, run the following commands:
   ```bash
   git add -A
   git commit -m "$(cat <<'EOF'
   {The full commit message you generated}
   EOF
   )"
   ```
6. **Update the session file** if there is an active session.
7. **Confirm the commit** by showing the user the commit hash: "✅ Committed: {commit_hash}"

**Important**:
- Always show the full commit message to the user before committing.
- Include any relevant requirement keys in the commit message.
- Keep the commit message concise but informative.
