# Git Workflow: nbs_screening_tool

Quick reference for pushing and pulling this repo to GitHub.
Remote: https://github.com/g-adzan/nbstool_v3

Run all commands in **Git Bash**, inside the repo folder:

```bash
cd "/c/Users/carbo/Documents/Claude/Projects/NBS Tool/nbs_screening_tool"
```

Tip: save and close notebooks in Jupyter or VS Code before running git.
Open notebooks auto save and make files look "modified" in the middle of a git step.

---

## Before you start working

Pull the latest version from GitHub first:

```bash
git pull
```

## After you finish working

Send your changes to GitHub:

```bash
git status                                 # see which files changed
git add -A                                  # stage all changes
git commit -m "short note about the change"
git push                                     # upload to GitHub
```

Order matters: `add` then `commit`, then `push`. Push only sends what you
have committed. If you forget to commit, push sends nothing.

---

## Common situations

### Push is rejected: "fetch first" or "non-fast-forward"

GitHub moved ahead of your local copy (someone pushed, or you uploaded
something on the web). Pull first, then push again:

```bash
git pull
git push
```

### `git status` shows a notebook as modified but you did not touch it

That is usually a notebook re save (outputs or metadata changed). It is
safe to commit:

```bash
git add -A
git commit -m "notebook re-save"
```

### You want to undo local changes to one file (not yet committed)

```bash
git restore "path/to/file"
```

### Check what is going on

```bash
git status                 # working tree state
git log --oneline -5       # recent commits
git remote -v              # confirm the GitHub link
```

---

## Notes

- Authentication: HTTPS with Git Credential Manager. The browser login
  popup only appears the first time. After that it is automatic.
- `.gitignore` already excludes large geospatial data (`.tif`, `.shp`,
  etc.) and the `outputs/` folder, so those never get pushed.
- The one time history merge with GitHub is already done. You do not need
  `--allow-unrelated-histories` again.
