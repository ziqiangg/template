"""Workflow state and guards for Claude Code hooks and pre-commit. Standard library only.

  state   print the current state and the instruction file to read (SessionStart)
  guard   block edits to fixed files and commits from subagents (PreToolUse, exit 2)
  stop    block finishing while a hard rule is broken (Stop / SubagentStop, exit 2)
  verify  the same checks for pre-commit (exit 1)
  refs    list every file that names a term (blast radius of a change)
  rehash  record the hashes of the fixed files (a person runs this, never Claude)
"""

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
HASHES = ".claude/immutable.sha256"
FIXED_GLOBS = ["CLAUDE.md", ".claude/settings.json", ".claude/hooks/flow.py",
               ".claude/hooks/tests/*.py", ".claude/instructions/*.md", ".claude/agents/*.md"]
GATE = "scripts/gate.ps1"
GATE_STUB = "GATE-NOT-CONFIGURED"
CONSTITUTION = ".specify/memory/constitution.md"
SPEC_KIT_FILES = {"spec.md", "plan.md", "tasks.md", "research.md", "data-model.md", "quickstart.md"}
SPEC_KIT_DIRS = {"contracts", "checklists"}
REFS_SKIP = (".claude/", ".specify/scripts/", ".specify/templates/", ".specify/integrations/",
             ".specify/workflows/", ".git/")
LOCAL_SETTINGS = ".claude/settings.local.json"
PLACEHOLDER = re.compile(r"\[[A-Z][A-Z0-9]*_[A-Z0-9_]+\]")  # Spec Kit tokens always contain "_"
HARMLESS_REDIRECT = re.compile(r"\d?>&\d|\d?>\s*(/dev/null|\$null|NUL)\b", re.I)
WRITE_HINT = re.compile(r">|\b(sed\s+-i|tee|rm|mv|truncate|Set-Content|Add-Content|Out-File|"
                        r"Remove-Item|Move-Item|Copy-Item|git\s+(checkout|restore|rm|mv))\b")
GIT_COMMIT = re.compile(r"(^|[;&|(]|\n)\s*git(\s+-\S+(\s+[^-\s]\S*)?)*\s+(commit|push)\b")
INSTRUCTION = {"SETUP": "setup.md", "INTAKE": "intake.md", "CLARIFY": "clarify.md",
               "TASKS": "tasks.md", "IMPLEMENT": "implement.md", "FINISH": "finish.md"}


def rel(path):
    return Path(path).as_posix()


def read(relpath):
    p = ROOT / relpath
    return p.read_text(encoding="utf-8", errors="replace") if p.is_file() else ""


def fixed_files():
    found = {rel(p.relative_to(ROOT)) for g in FIXED_GLOBS for p in ROOT.glob(g) if p.is_file()}
    return sorted(found)


def sha(relpath):
    # line endings normalised so a CRLF checkout does not look like an edit
    return hashlib.sha256((ROOT / relpath).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def recorded():
    lines = read(HASHES).splitlines()
    return {name: digest for digest, name in (ln.split("  ", 1) for ln in lines if "  " in ln)}


def active_feature():
    """The feature folder Spec Kit points at, as Spec Kit resolves it."""
    folder = os.environ.get("SPECIFY_FEATURE_DIRECTORY")
    if not folder:
        try:
            folder = json.loads(read(".specify/feature.json") or "{}").get("feature_directory")
        except json.JSONDecodeError:
            folder = None
    return rel(folder) if folder and (ROOT / folder).is_dir() else None


def tree_dirty():
    out = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain"],
                         capture_output=True, text=True).stdout
    return bool(out.strip())


def current_state():
    constitution = re.sub(r"<!--.*?-->", "", read(CONSTITUTION), flags=re.S)
    if PLACEHOLDER.search(constitution) or GATE_STUB in read(GATE) or not read(GATE):
        return "SETUP", None
    feature = active_feature()
    if not feature:
        return "IDLE", None
    has = {name: (ROOT / feature / name).is_file() for name in ("spec.md", "plan.md", "tasks.md")}
    if not has["spec.md"]:
        return "INTAKE", feature
    if feature.endswith("-foundation"):  # product knowledge only: no plan or tasks
        return ("FINISH" if tree_dirty() else "IDLE"), feature
    if not has["plan.md"]:
        return "CLARIFY", feature
    if not has["tasks.md"]:
        return "TASKS", feature
    if re.search(r"^\s*- \[ \]", read(f"{feature}/tasks.md"), re.M):
        return "IMPLEMENT", feature
    return ("FINISH" if tree_dirty() else "IDLE"), feature


def problems():
    found = []
    hashes = recorded()
    if not hashes:
        found.append(f"{HASHES} is missing: a person runs `python .claude/hooks/flow.py rehash`")
    for name in sorted(set(hashes) | set(fixed_files())):
        if name not in hashes:
            found.append(f"{name} is new and not in {HASHES}")
        elif not (ROOT / name).is_file() or sha(name) != hashes[name]:
            found.append(f"{name} is fixed but was changed: restore it with `git checkout -- {name}`")
    for folder in sorted(p for p in (ROOT / "specs").glob("*") if p.is_dir()):
        name = rel(folder.relative_to(ROOT))
        if (folder / "plan.md").is_file() and "[NEEDS CLARIFICATION" in read(f"{name}/spec.md"):
            found.append(f"{name}/spec.md still has NEEDS CLARIFICATION after planning: run /speckit-clarify")
        for item in sorted(folder.iterdir()):
            ok = item.name in SPEC_KIT_FILES if item.is_file() else item.name in SPEC_KIT_DIRS
            if not ok:
                found.append(f"{name}/{item.name} is not a Spec Kit file: move it out of specs/")
    return found


def protected():
    return set(recorded()) | set(fixed_files()) | {HASHES, LOCAL_SETTINGS}


def locked(path_text):
    try:
        target = rel(Path(path_text).resolve().relative_to(ROOT.resolve()))
    except ValueError:
        return None
    names = protected()
    return target if target.lower() in {n.lower() for n in names} else None


def block(reason):
    print(reason, file=sys.stderr)
    sys.exit(2)


def guard(event):
    tool, args = event.get("tool_name", ""), event.get("tool_input") or {}
    if tool in ("Write", "Edit", "NotebookEdit"):
        path = args.get("file_path") or args.get("notebook_path")
        if not path:
            block("guard: no file path in the tool call")
        name = locked(Path(path) if Path(path).is_absolute() else ROOT / path)
        if name:
            block(f"{name} is a fixed workflow file. Propose the change; a person edits it and runs rehash.")
    elif tool in ("Bash", "PowerShell"):
        command = args.get("command", "")
        if re.search(r"flow\.py\s+rehash", command):
            block("rehash is run by a person only.")
        if event.get("agent_id") and GIT_COMMIT.search(command):
            block("Agents never commit or push. Report back; the main session commits after approval.")
        if WRITE_HINT.search(HARMLESS_REDIRECT.sub("", command)):
            for name in protected():
                if name.lower() in command.replace("\\", "/").lower():
                    block(f"{name} is a fixed workflow file. Propose the change instead.")


def refs(term):
    out = subprocess.run(["git", "-C", str(ROOT), "grep", "-n", "-i", "-F", "--untracked", "-e", term],
                         capture_output=True, text=True).stdout
    hits = [ln for ln in out.splitlines() if not ln.startswith(REFS_SKIP)]
    print("\n".join(hits) if hits else f"no file names '{term}'")


def rehash():
    lines = [f"{sha(name)}  {name}" for name in fixed_files()]
    (ROOT / HASHES).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"recorded {len(lines)} fixed files in {HASHES}")


def main(argv):
    command = argv[1] if len(argv) > 1 else ""
    if command == "state":
        state, feature = current_state()
        where = f" feature={feature}" if feature else ""
        read_first = f".claude/instructions/{INSTRUCTION[state]}" if state in INSTRUCTION else "CLAUDE.md (IDLE row)"
        print(f"STATE={state}{where} -> read {read_first}")
    elif command == "guard":
        guard(json.loads(sys.stdin.read()))
    elif command == "stop":
        event = json.loads(sys.stdin.read() or "{}")
        found = [] if event.get("stop_hook_active") else problems()
        if found:
            block("Fix before finishing:\n- " + "\n- ".join(found))
    elif command == "verify":
        found = problems()
        if found:
            print("\n".join(found), file=sys.stderr)
            sys.exit(1)
    elif command == "refs" and len(argv) > 2:
        refs(" ".join(argv[2:]))
    elif command == "rehash":
        rehash()
    else:
        print(__doc__, file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    try:
        main(sys.argv)
    except SystemExit:
        raise
    except Exception as exc:  # fail closed: any crash blocks the action
        block(f"flow.py failed: {exc}")
