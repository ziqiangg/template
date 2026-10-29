"""Tests for flow.py. Run from the repo root: python -m unittest discover -s .claude/hooks/tests"""

import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

FLOW = Path(__file__).resolve().parents[1] / "flow.py"
RATIFIED = "# Demo Constitution\n\n**Version**: 1.0.0 | **Ratified**: 2026-01-01\n"
GATE_DONE = "uv run pytest -q\n"


def run(root, *args, stdin=""):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(root)}
    env.pop("SPECIFY_FEATURE_DIRECTORY", None)
    return subprocess.run(
        [sys.executable, "-I", str(root / ".claude/hooks/flow.py"), *args],
        input=stdin, capture_output=True, text=True, cwd=root, env=env,
    )


class Repo:
    """A throwaway project laid out like the template."""

    def __init__(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        subprocess.run(["git", "init", "-q", str(self.root)], check=True)
        self.write(".specify/memory/constitution.md", RATIFIED)
        self.write("scripts/gate.ps1", GATE_DONE)
        self.write("CLAUDE.md", "router\n")
        self.write(".claude/instructions/plan.md", "fixed\n")
        self.write(".claude/agents/reviewer.md", "fixed\n")
        self.write(".claude/settings.json", "{}\n")
        self.write(".claude/hooks/flow.py", FLOW.read_text(encoding="utf-8"))
        rehash = run(self.root, "rehash")
        assert rehash.returncode == 0, rehash.stderr
        self.commit()

    def write(self, rel, text):
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")

    def commit(self):
        g = ["git", "-C", str(self.root), "-c", "user.name=t", "-c", "user.email=t@t"]
        subprocess.run([*g, "add", "-A"], check=True)
        subprocess.run([*g, "commit", "-q", "-m", "x", "--no-verify"], check=True)

    def feature(self, name="001-demo", **files):
        self.write(".specify/feature.json", json.dumps({"feature_directory": f"specs/{name}"}))
        (self.root / "specs" / name).mkdir(parents=True, exist_ok=True)
        for rel, text in files.items():
            self.write(f"specs/{name}/{rel.replace('__', '/')}", text)

    def state(self):
        return run(self.root, "state").stdout

    def close(self):
        self.tmp.cleanup()


class StateTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()

    def tearDown(self):
        self.repo.close()

    def test_setup_when_constitution_has_placeholders(self):
        self.repo.write(".specify/memory/constitution.md", "# [PROJECT_NAME] Constitution\n")
        self.assertIn("STATE=SETUP", self.repo.state())

    def test_setup_when_gate_is_the_stub(self):
        self.repo.write("scripts/gate.ps1", "# GATE-NOT-CONFIGURED\nexit 1\n")
        self.assertIn("STATE=SETUP", self.repo.state())

    def test_ratified_constitution_with_bracketed_words_is_not_setup(self):
        self.repo.write(".specify/memory/constitution.md",
                        "<!-- Sync report: [PROJECT_NAME] replaced -->\n" + RATIFIED + "Each [US1] story [MUST] pass.\n")
        self.assertNotIn("STATE=SETUP", self.repo.state())

    def test_foundation_spec_does_not_wait_for_a_plan(self):
        self.repo.feature("000-foundation", **{"spec.md": "glossary\n"})
        self.assertIn("STATE=FINISH", self.repo.state())
        self.repo.commit()
        self.assertIn("STATE=IDLE", self.repo.state())

    def test_idle_without_active_feature(self):
        self.assertIn("STATE=IDLE", self.repo.state())

    def test_intake_when_feature_has_no_spec(self):
        self.repo.feature()
        out = self.repo.state()
        self.assertIn("STATE=INTAKE", out)
        self.assertIn("specs/001-demo", out)

    def test_clarify_when_spec_but_no_plan(self):
        self.repo.feature(**{"spec.md": "# Spec\n"})
        self.assertIn("STATE=CLARIFY", self.repo.state())

    def test_tasks_when_plan_but_no_tasks(self):
        self.repo.feature(**{"spec.md": "s\n", "plan.md": "p\n"})
        self.assertIn("STATE=TASKS", self.repo.state())

    def test_implement_when_unchecked_tasks(self):
        self.repo.feature(**{"spec.md": "s\n", "plan.md": "p\n", "tasks.md": "- [x] T001 a\n- [ ] T002 b\n"})
        self.assertIn("STATE=IMPLEMENT", self.repo.state())

    def test_finish_when_all_checked_and_tree_dirty(self):
        self.repo.feature(**{"spec.md": "s\n", "plan.md": "p\n", "tasks.md": "- [x] T001 a\n- [X] T002 b\n"})
        self.assertIn("STATE=FINISH", self.repo.state())

    def test_idle_when_all_checked_and_tree_clean(self):
        self.repo.feature(**{"spec.md": "s\n", "plan.md": "p\n", "tasks.md": "- [x] T001 a\n"})
        self.repo.commit()
        self.assertIn("STATE=IDLE", self.repo.state())

    def test_state_names_instruction_file(self):
        self.repo.feature(**{"spec.md": "s\n", "plan.md": "p\n"})
        self.assertIn(".claude/instructions/tasks.md", self.repo.state())


class GuardTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()

    def tearDown(self):
        self.repo.close()

    def guard(self, payload):
        return run(self.repo.root, "guard", stdin=json.dumps(payload))

    def edit(self, rel, **extra):
        path = str(self.repo.root / rel)
        return self.guard({"tool_name": "Edit", "tool_input": {"file_path": path}, **extra})

    def bash(self, command, **extra):
        return self.guard({"tool_name": "Bash", "tool_input": {"command": command}, **extra})

    def test_blocks_edit_to_locked_file(self):
        r = self.edit(".claude/instructions/plan.md")
        self.assertEqual(r.returncode, 2)
        self.assertIn("fixed", r.stderr)

    def test_blocks_edit_to_hash_list(self):
        self.assertEqual(self.edit(".claude/immutable.sha256").returncode, 2)

    def test_allows_edit_to_product_file(self):
        self.assertEqual(self.edit("src/app.py").returncode, 0)

    def test_allows_edit_to_project_gate(self):
        self.assertEqual(self.edit("scripts/gate.ps1").returncode, 0)

    def test_blocks_bash_write_to_locked_file(self):
        self.assertEqual(self.bash("echo x > CLAUDE.md").returncode, 2)
        self.assertEqual(self.bash("sed -i s/a/b/ .claude/agents/reviewer.md").returncode, 2)

    def test_edit_and_shell_blocks_give_the_same_message(self):
        via_edit = self.edit("CLAUDE.md").stderr
        via_shell = self.bash("echo x > CLAUDE.md").stderr
        self.assertEqual(via_edit, via_shell)
        self.assertIn("a person edits it and runs rehash", via_edit)

    def test_allows_bash_read_of_locked_file(self):
        self.assertEqual(self.bash("cat CLAUDE.md | head -5").returncode, 0)
        self.assertEqual(self.bash("cat .claude/instructions/plan.md 2>&1 | head").returncode, 0)
        self.assertEqual(self.bash("grep x CLAUDE.md 2>/dev/null").returncode, 0)
        self.assertEqual(self.bash("cp CLAUDE.md /tmp/x").returncode, 0)

    def test_blocks_powershell_write_to_locked_file(self):
        r = self.guard({"tool_name": "PowerShell", "tool_input": {"command": "Set-Content CLAUDE.md x"}})
        self.assertEqual(r.returncode, 2)

    def test_blocks_edit_to_local_settings(self):
        self.assertEqual(self.edit(".claude/settings.local.json").returncode, 2)

    def test_allows_agent_reads_that_mention_commit_or_push(self):
        self.assertEqual(self.bash("git diff src/commit.py", agent_id="a1").returncode, 0)
        self.assertEqual(self.bash("git log | grep push", agent_id="a1").returncode, 0)

    def test_blocks_agent_commit_with_git_options(self):
        self.assertEqual(self.bash("git -C sub commit -m x", agent_id="a1").returncode, 2)
        self.assertEqual(self.bash("cd x && git push origin main", agent_id="a1").returncode, 2)

    def test_blocks_rehash_from_claude(self):
        self.assertEqual(self.bash("python .claude/hooks/flow.py rehash").returncode, 2)

    def test_blocks_commit_from_subagent(self):
        r = self.bash('git commit -m "x"', agent_id="a1", agent_type="implementer")
        self.assertEqual(r.returncode, 2)
        self.assertEqual(self.bash("git push", agent_id="a1").returncode, 2)

    def test_allows_commit_from_main_session(self):
        self.assertEqual(self.bash('git commit -m "x"').returncode, 0)

    def test_fails_closed_on_bad_input(self):
        self.assertEqual(run(self.repo.root, "guard", stdin="not json").returncode, 2)


class StopAndVerifyTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()

    def tearDown(self):
        self.repo.close()

    def stop(self, active=False):
        return run(self.repo.root, "stop", stdin=json.dumps({"stop_hook_active": active}))

    def test_clean_repo_passes(self):
        self.assertEqual(self.stop().returncode, 0)
        self.assertEqual(run(self.repo.root, "verify").returncode, 0)

    def test_changed_locked_file_blocks(self):
        self.repo.write(".claude/instructions/plan.md", "edited\n")
        r = self.stop()
        self.assertEqual(r.returncode, 2)
        self.assertIn(".claude/instructions/plan.md", r.stderr)
        self.assertEqual(run(self.repo.root, "verify").returncode, 1)

    def test_open_clarification_after_plan_blocks(self):
        self.repo.feature(**{"spec.md": "x [NEEDS CLARIFICATION: who?]\n", "plan.md": "p\n"})
        self.assertEqual(self.stop().returncode, 2)

    def test_open_clarification_before_plan_is_fine(self):
        self.repo.feature(**{"spec.md": "x [NEEDS CLARIFICATION: who?]\n"})
        self.assertEqual(self.stop().returncode, 0)

    def test_extra_file_in_feature_folder_blocks(self):
        self.repo.feature(**{"spec.md": "s\n", "analyze-report.md": "r\n"})
        r = self.stop()
        self.assertEqual(r.returncode, 2)
        self.assertIn("analyze-report.md", r.stderr)

    def test_spec_kit_outputs_are_allowed(self):
        self.repo.feature(**{
            "spec.md": "s\n", "plan.md": "p\n", "tasks.md": "t\n", "research.md": "r\n",
            "data-model.md": "d\n", "quickstart.md": "q\n", "contracts__api.md": "c\n",
            "checklists__ux.md": "c\n",
        })
        self.assertEqual(self.stop().returncode, 0)

    def test_stop_hook_active_never_blocks(self):
        self.repo.write(".claude/instructions/plan.md", "edited\n")
        self.assertEqual(self.stop(active=True).returncode, 0)


class RefsTest(unittest.TestCase):
    def test_lists_every_file_naming_the_term(self):
        repo = Repo()
        try:
            repo.write("specs/001-demo/spec.md", "The Upload Limit is 5 MB.\n")
            repo.write("src/upload.py", "UPLOAD_LIMIT = 5  # upload limit\n")
            repo.write(".specify/memory/constitution.md", RATIFIED + "No upload limit above 10 MB.\n")
            repo.write(".specify/templates/spec-template.md", "upload limit\n")
            repo.write(".claude/instructions/x.md", "upload limit\n")
            out = run(repo.root, "refs", "upload limit").stdout
            self.assertIn("specs/001-demo/spec.md:1", out)
            self.assertIn("src/upload.py:1", out)
            self.assertIn(".specify/memory/constitution.md:4", out)
            self.assertNotIn(".specify/templates", out)
            self.assertNotIn(".claude/", out)
        finally:
            repo.close()


if __name__ == "__main__":
    unittest.main()
