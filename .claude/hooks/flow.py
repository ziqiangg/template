"""Workflow state and guards for Claude Code hooks and pre-commit. Standard library only.

  state   print the current state and the instruction file to read; --fetch first looks at origin (SessionStart)
  guard   block edits to fixed files and commits from subagents (PreToolUse, exit 2)
  stop    block finishing while a hard rule is broken (Stop / SubagentStop, exit 2)
  verify  the same checks for pre-commit (exit 1)
  pushcheck  refuse a push with uncommitted changes or without origin's main branch merged (pre-push, exit 1)
  gate    run scripts/gate.ps1, skipped when these exact files already passed (pre-commit, pre-push)
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
GATE_PASSED = "gate-passed"  # inside .git: the fingerprint of the files the gate last passed on
CONSTITUTION = ".specify/memory/constitution.md"
FOUNDATION = "specs/000-foundation/"
FETCH_AT_START_S = 8  # below the SessionStart hook's timeout; a session must never wait on the network
FETCH_BEFORE_PUSH_S = 60
INSTALLED_HOOKS = ("pre-commit", "pre-push")
SPEC_KIT_FILES = {"spec.md", "plan.md", "tasks.md", "research.md", "data-model.md", "quickstart.md"}
SPEC_KIT_DIRS = {"contracts", "checklists"}
REFS_SKIP = (".claude/", ".specify/scripts/", ".specify/templates/", ".specify/integrations/",
             ".specify/workflows/", ".git/")
LOCAL_SETTINGS = ".claude/settings.local.json"
FIXED_MESSAGE = "{name} is a fixed workflow file. Propose the change; a person edits it and runs rehash."
PLACEHOLDER = re.compile(r"\[[A-Z][A-Z0-9]*_[A-Z0-9_]+\]")  # Spec Kit tokens always contain "_"
HARMLESS_REDIRECT = re.compile(r"\d?>&\d|\d?>\s*(/dev/null|\$null|NUL)\b", re.I)
WRITE_HINT = re.compile(r">|\b(sed\s+-i|tee|rm|mv|truncate|Set-Content|Add-Content|Out-File|"
                        r"Remove-Item|Move-Item|Copy-Item|git\s+(checkout|restore|rm|mv))\b")
GIT_COMMIT = re.compile(r"(^|[;&|(]|\n)\s*git(\s+-\S+(\s+[^-\s]\S*)?)*\s+(commit|push)\b")
INSTRUCTION = {"SETUP": "setup.md", "INTAKE": "intake.md", "CLARIFY": "clarify.md",
               "PLAN": "plan.md", "TASKS": "tasks.md", "IMPLEMENT": "implement.md", "FINISH": "finish.md"}


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


def tree_dirty(*paths):
    out = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", *paths],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    return bool(out.strip())


OPEN_ITEM = re.compile(r"^\s*- \[ \]", re.M)


def checklists_approved(feature):
    """A custom checklist (other than Spec Kit's built-in requirements.md) exists and is fully ticked."""
    custom = [p for p in (ROOT / feature / "checklists").glob("*.md") if p.name != "requirements.md"]
    return bool(custom) and not any(OPEN_ITEM.search(p.read_text(encoding="utf-8")) for p in custom)


def unfinished(active):
    """Other features with unticked tasks or uncommitted changes, so a feature switch never hides work."""
    found = []
    for path in sorted(p for p in (ROOT / "specs").glob("*") if p.is_dir()):
        folder = rel(path.relative_to(ROOT))
        if folder == active:
            continue
        count = len(OPEN_ITEM.findall(read(f"{folder}/tasks.md")))
        if count:
            found.append(f"{folder} ({count} open task{'s' if count > 1 else ''})")
        elif tree_dirty(folder):
            found.append(f"{folder} (uncommitted)")
    return found


def current_state():
    constitution = re.sub(r"<!--.*?-->", "", read(CONSTITUTION), flags=re.S)
    if PLACEHOLDER.search(constitution) or GATE_STUB in read(GATE) or not read(GATE):
        return "SETUP", None
    if tree_dirty(CONSTITUTION, GATE):  # the base is ratified only once committed
        return "SETUP", None
    feature = active_feature()
    if not feature:
        return "IDLE", None
    has = {name: (ROOT / feature / name).is_file() for name in ("spec.md", "plan.md", "tasks.md")}
    if not has["spec.md"]:
        return "INTAKE", feature
    if feature.endswith("-foundation"):  # shared product knowledge only: clarified, then committed
        return ("CLARIFY" if tree_dirty() else "IDLE"), feature
    if not has["plan.md"]:
        return "CLARIFY", feature
    if not has["tasks.md"]:
        return ("TASKS" if checklists_approved(feature) else "PLAN"), feature
    if OPEN_ITEM.search(read(f"{feature}/tasks.md")):
        return "IMPLEMENT", feature
    return ("FINISH" if tree_dirty() else "IDLE"), feature


def git(*args, timeout=None):
    env = {**os.environ, "GIT_TERMINAL_PROMPT": "0", "GCM_INTERACTIVE": "never"}  # never wait on a sign-in
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, encoding="utf-8",
                          errors="replace", timeout=timeout, env=env)


def has_origin():
    return git("remote", "get-url", "origin").returncode == 0


def fetched(timeout):
    try:
        return git("fetch", "--quiet", "--prune", "origin", timeout=timeout).returncode == 0
    except subprocess.TimeoutExpired:
        return False


def origin_main():
    """Origin's main branch as last fetched; None before anything has been pushed there."""
    ref = git("symbolic-ref", "--short", "refs/remotes/origin/HEAD").stdout.strip()
    if ref:
        return ref
    for name in ("origin/main", "origin/master"):
        if git("rev-parse", "--verify", "--quiet", name).returncode == 0:
            return name
    return None


def other_branches(base):
    own = "origin/" + git("branch", "--show-current").stdout.strip()
    names = git("for-each-ref", "refs/remotes/origin", "--no-merged", base,
                "--format=%(refname:short)").stdout.split()
    return [name for name in names if name not in (base, own)]


def sync_lines():
    """What other developers have pushed, from the last fetch."""
    base = origin_main()
    if not base:
        return []
    lines = []
    count = int(git("rev-list", "--count", f"HEAD..{base}").stdout.strip() or 0)
    if count:
        lines.append(f"{base} has {count} commit{'s' if count > 1 else ''} this checkout lacks: merge before pushing.")
        changed = git("diff", "--name-only", f"HEAD...{base}").stdout.splitlines()
        fixed = set(recorded())
        shared = sorted(n for n in changed if n in (CONSTITUTION, GATE) or n in fixed or n.startswith(FOUNDATION))
        if shared:
            lines.append(f"shared changed: {', '.join(shared)}. After merging, follow change.md step 5 for your feature.")
        features = sorted({"/".join(n.split("/")[:2]) for n in changed
                           if n.startswith("specs/") and not n.startswith(FOUNDATION)})
        if features:
            lines.append(f"features changed: {', '.join(features)}")
    others = other_branches(base)
    if others:
        lines.append(f"other branches: {', '.join(others)}")
    return lines


def missing_hooks():
    hooks = git("rev-parse", "--git-path", "hooks").stdout.strip()
    return [name for name in INSTALLED_HOOKS if not (ROOT / hooks / name).is_file()]


def pushcheck():
    if tree_dirty():
        return "uncommitted changes: the gate would test them, not what is being pushed. Commit or stash them first."
    if not has_origin():
        return None
    if not fetched(FETCH_BEFORE_PUSH_S):
        return "could not reach origin, so this push cannot be checked against what others have pushed."
    base = origin_main()
    if base and git("merge-base", "--is-ancestor", base, "HEAD").returncode != 0:
        return f"this branch lacks {base}: merge it, then push, so the gate tests both people's work together."
    return None


def fingerprint():
    """The files the gate checks, as they are on disk: tracked files and untracked ones not ignored, each as
    the blob git would store. Staged, unstaged or committed, the same files give the same value."""
    blobs = {}
    for entry in filter(None, git("ls-files", "-s", "-z").stdout.split("\0")):
        meta, path = entry.split("\t", 1)
        blobs[path] = meta.split()[1]
    changed = [p for p in git("diff", "--name-only", "-z").stdout.split("\0") if p]
    changed += [p for p in git("ls-files", "-o", "--exclude-standard", "-z").stdout.split("\0") if p]
    for path in changed:
        blobs.pop(path, None)
    present = [p for p in changed if (ROOT / p).is_file()]
    if present:
        out = subprocess.run(["git", "-C", str(ROOT), "hash-object", "--stdin-paths"], input="\n".join(present),
                             capture_output=True, text=True, encoding="utf-8", check=True).stdout.split()
        blobs.update(zip(present, out))
    listing = "".join(f"{path} {blob}\n" for path, blob in sorted(blobs.items()))
    return hashlib.sha256(listing.encode("utf-8")).hexdigest()


def gate():
    """Each hook runs the gate; a repeat on files that already passed is skipped. A failure is never kept."""
    record = ROOT / git("rev-parse", "--git-path", GATE_PASSED).stdout.strip()
    before = fingerprint()
    if record.is_file() and record.read_text(encoding="utf-8").strip() == before:
        print("gate: skipped, these exact files already passed")
        return 0
    record.unlink(missing_ok=True)
    code = subprocess.run(["pwsh", "-NoProfile", "-File", GATE], cwd=ROOT).returncode
    if code == 0 and fingerprint() == before:  # a gate that changed files proves nothing about them
        record.write_text(before + "\n", encoding="utf-8")
    return code


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
            block(FIXED_MESSAGE.format(name=name))
    elif tool in ("Bash", "PowerShell"):
        command = args.get("command", "")
        if re.search(r"flow\.py\s+rehash", command):
            block("rehash is run by a person only.")
        if event.get("agent_id") and GIT_COMMIT.search(command):
            block("Agents never commit or push. Report back; the main session commits after approval.")
        # a segment must both write and name a fixed file; `write x && read fixed` is fine
        for segment in re.split(r"&&|\|\|?|;|\n", command):
            if WRITE_HINT.search(HARMLESS_REDIRECT.sub("", segment)):
                for name in protected():
                    if name.lower() in segment.replace("\\", "/").lower():
                        block(FIXED_MESSAGE.format(name=name))


def refs(term):
    out = subprocess.run(["git", "-C", str(ROOT), "grep", "-n", "-i", "-F", "--untracked", "-e", term],
                         capture_output=True, text=True, encoding="utf-8", errors="replace").stdout
    hits = [ln for ln in out.splitlines() if not ln.startswith(REFS_SKIP)]
    print("\n".join(hits) if hits else f"no file names '{term}'")


def rehash():
    lines = [f"{sha(name)}  {name}" for name in fixed_files()]
    (ROOT / HASHES).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    print(f"recorded {len(lines)} fixed files in {HASHES}")


def main(argv):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    command = argv[1] if len(argv) > 1 else ""
    if command == "state":
        unreachable = "--fetch" in argv and has_origin() and not fetched(FETCH_AT_START_S)
        state, feature = current_state()
        where = f" feature={feature}" if feature else ""
        read_first = f".claude/instructions/{INSTRUCTION[state]}" if state in INSTRUCTION else "CLAUDE.md (IDLE row)"
        print(f"STATE={state}{where} -> read {read_first}")
        others = unfinished(feature)
        if others:
            print("unfinished: " + "; ".join(others))
        if unreachable:
            print("could not reach origin: other developers' pushes were not checked.")
        for line in sync_lines():
            print(line)
        if state != "SETUP" and missing_hooks():  # SETUP installs them; a new clone never passes through it
            print("the commit and push checks are not installed in this clone: run `pre-commit install`.")
    elif command == "pushcheck":
        reason = pushcheck()
        if reason:
            print(reason, file=sys.stderr)
            sys.exit(1)
    elif command == "gate":
        sys.exit(gate())
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
