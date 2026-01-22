# Parallelize Tasks

You are helping the user parallelize their work across multiple Claude Code terminals using git worktrees.

## Modes

This skill has two modes based on context:
- **Setup mode**: When there's no active parallel work, analyze tasks and create worktrees
- **Merge mode**: When worktrees exist, help merge completed work back

Check which mode by running `git worktree list` - if there's more than one worktree, you're likely in merge mode.

---

# SETUP MODE: Analyze and Create Parallel Work

## Step 1: Analyze Tasks

Examine the current context:
- Check for any existing todo list or plan file
- Look at uncommitted changes and recent work
- Understand what work needs to be done

Group tasks into **parallelizable units** based on:
- **File boundaries**: Tasks touching different files can run in parallel
- **Directory boundaries**: backend/ vs frontend/ vs tests/
- **Feature boundaries**: Independent features that don't share code

## Step 2: Present Parallelization Options

Show a clear breakdown:

```
## Parallelization Analysis

I found [N] tasks that could be parallelized into [M] independent work streams:

### Stream 1: [Name] (this terminal)
Files: backend/app.py, backend/database.py
Tasks:
- [ ] Task A
- [ ] Task B

### Stream 2: [Name] (new terminal)
Files: frontend/index.html, frontend/app.js
Tasks:
- [ ] Task C
- [ ] Task D

### Cannot Parallelize (sequential)
- [ ] Task E (depends on Task A)
```

Ask: "Would you like me to set up worktrees for parallel execution?"

## Step 3: Create Worktrees

For each parallel stream (except current terminal):

```bash
git worktree add <path> -b <branch-name>
```

Naming conventions:
- Path: `../<project-name>-<stream-name>` (e.g., `../FeedMovie-frontend`)
- Branch: `feature/<stream-name>` (e.g., `feature/frontend-auth`)

## Step 4: Generate Handoff Instructions

For each new worktree, output clear instructions the user can paste into the other terminal:

```markdown
## Handoff: [Stream Name]

**Directory**: cd /path/to/worktree
**Branch**: feature/branch-name

### Context
[Brief project description and what's been done so far]

### Your Tasks
1. [ ] First task with specifics
2. [ ] Second task with specifics

### Files You Own (safe to modify)
- path/to/file1.ext
- path/to/file2.ext

### Files to NOT Modify (being edited elsewhere)
- path/to/shared/file.ext

### Interfaces/Contracts
[Any APIs or interfaces between streams that must match]

### When Done
1. Commit all changes
2. Run: git push -u origin feature/branch-name
3. Let the main terminal know you're done
```

## Step 5: Save State

Create `.claude/parallel-work.json`:

```json
{
  "created_at": "ISO timestamp",
  "main_branch": "main",
  "worktrees": [
    {
      "name": "frontend",
      "path": "../Project-frontend",
      "branch": "feature/frontend-auth",
      "tasks": ["Add auth UI", "Add onboarding"],
      "files": ["frontend/*"],
      "status": "in_progress"
    }
  ]
}
```

---

# MERGE MODE: Complete Parallel Work

## Step 1: Check Status

```bash
git worktree list
git fetch origin
cat .claude/parallel-work.json 2>/dev/null
```

Show status table:
```
| Worktree | Branch | Remote | Status |
|----------|--------|--------|--------|
| ../Project-frontend | feature/frontend-auth | pushed | Ready to merge |
```

## Step 2: Pre-Merge Checks

```bash
# What will be merged
git log main..origin/<branch> --oneline

# Check for conflicts
git diff main...origin/<branch> --stat
```

Warn if same files modified in both branches.

## Step 3: Merge

```bash
git checkout main
git merge origin/<branch> --no-ff -m "Merge <branch>: <description>"
```

### If Conflicts Occur

1. Show conflicted files: `git diff --name-only --diff-filter=U`
2. For each conflict, explain what each side changed
3. Help resolve using the Edit tool
4. Complete: `git add <files> && git commit`

## Step 4: Clean Up

```bash
# Remove worktree
git worktree remove <path>

# Delete local branch
git branch -d <branch>

# Optional: delete remote branch
git push origin --delete <branch>
```

Update or remove `.claude/parallel-work.json`.

---

# Important Rules

1. **Never parallelize tasks touching the same file** - causes merge conflicts
2. **Identify dependencies first** - dependent tasks can't parallelize
3. **2-3 streams max** - more adds overhead without benefit
4. **Keep interfaces stable** - define shared APIs upfront
5. **Commit frequently** - smaller commits = easier merges

---

# Quick Reference

| Command | What it does |
|---------|--------------|
| `git worktree add ../path -b branch` | Create new worktree |
| `git worktree list` | Show all worktrees |
| `git worktree remove ../path` | Remove worktree |
| `git merge origin/branch --no-ff` | Merge preserving history |
| `git branch -d branch` | Delete local branch |
