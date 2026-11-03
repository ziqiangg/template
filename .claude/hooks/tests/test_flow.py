"""Tests for flow.py. Run from the repo root: python -m unittest discover -s .claude/hooks/tests"""

import json
import os
import shutil
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
        self.repo.commit()
        self.assertNotIn("STATE=SETUP", self.repo.state())

    def test_foundation_spec_does_not_wait_for_a_plan(self):
        self.repo.feature("000-foundation", **{"spec.md": "glossary\n"})
        self.assertIn("STATE=CLARIFY", self.repo.state())
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

    def test_setup_while_constitution_or_gate_uncommitted(self):
        self.repo.write(".specify/memory/constitution.md", RATIFIED + "More.\n")
        self.assertIn("STATE=SETUP", self.repo.state())
        self.repo.commit()
        self.repo.write("scripts/gate.ps1", GATE_DONE + "node --test\n")
        self.assertIn("STATE=SETUP", self.repo.state())

    def test_plan_until_a_custom_checklist_is_fully_ticked(self):
        self.repo.feature(**{"spec.md": "s\n", "plan.md": "p\n", "checklists__requirements.md": "- [x] a\n"})
        self.assertIn("STATE=PLAN", self.repo.state())
        self.repo.feature(**{"checklists__ux.md": "- [x] CHK001 a\n- [ ] CHK002 b\n"})
        self.assertIn("STATE=PLAN", self.repo.state())
        self.repo.feature(**{"checklists__ux.md": "- [x] CHK001 a\n- [X] CHK002 b\n"})
        self.assertIn("STATE=TASKS", self.repo.state())

    def test_state_lists_other_unfinished_features(self):
        self.repo.feature("001-demo", **{"spec.md": "s\n", "plan.md": "p\n", "tasks.md": "- [x] a\n- [ ] b\n- [ ] c\n"})
        self.repo.feature("002-next", **{"spec.md": "s\n"})
        out = self.repo.state()
        self.assertIn("STATE=CLARIFY feature=specs/002-next", out)
        self.assertIn("unfinished: specs/001-demo (2 open tasks)", out)

    def test_state_lists_other_uncommitted_features(self):
        self.repo.feature("001-demo", **{"spec.md": "s\n", "plan.md": "p\n", "tasks.md": "- [x] a\n"})
        self.repo.commit()
        self.repo.write("specs/001-demo/spec.md", "s changed\n")
        self.repo.feature("002-next", **{"spec.md": "s\n"})
        self.assertIn("unfinished: specs/001-demo (uncommitted)", self.repo.state())

    def test_tasks_when_plan_and_checklist_approved(self):
        self.repo.feature(**{"spec.md": "s\n", "plan.md": "p\n", "checklists__ux.md": "- [x] CHK001 a\n"})
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
        self.assertIn(".claude/instructions/plan.md", self.repo.state())


class TwoClones:
    """The Repo above pushed to a bare origin, plus a second developer's clone of it."""

    def __init__(self):
        self.repo = Repo()
        self.tmp = tempfile.TemporaryDirectory()
        base = Path(self.tmp.name)
        self.origin = base / "origin.git"
        self.other = base / "other"
        subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(self.origin)], check=True)
        self.git(self.repo.root, "branch", "-M", "main")
        self.git(self.repo.root, "remote", "add", "origin", str(self.origin))
        self.git(self.repo.root, "push", "-q", "-u", "origin", "main")
        subprocess.run(["git", "clone", "-q", str(self.origin), str(self.other)], check=True)

    @staticmethod
    def git(root, *args):
        return subprocess.run(["git", "-C", str(root), "-c", "user.name=t", "-c", "user.email=t@t", *args],
                              check=True, capture_output=True, text=True)

    def other_pushes(self, rel, ref="main"):
        path = self.other / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("changed\n", encoding="utf-8", newline="\n")
        self.git(self.other, "add", "-A")
        self.git(self.other, "commit", "-q", "-m", "other", "--no-verify")
        self.git(self.other, "push", "-q", "origin", f"HEAD:{ref}")

    def state(self, *args):
        return run(self.repo.root, "state", *args)

    def close(self):
        self.repo.close()
        self.tmp.cleanup()


class SyncStateTest(unittest.TestCase):
    def setUp(self):
        self.clones = TwoClones()
        self.addCleanup(self.clones.close)

    def test_nothing_is_said_when_up_to_date(self):
        self.assertNotIn("origin/", self.clones.state("--fetch").stdout)

    def test_fetch_reports_commits_this_checkout_lacks(self):
        self.clones.other_pushes("src/a.py")
        out = self.clones.state("--fetch")
        self.assertEqual(out.returncode, 0)
        self.assertIn("origin/main has 1 commit this checkout lacks", out.stdout)

    def test_plain_state_does_not_fetch(self):
        self.clones.other_pushes("src/a.py")
        self.assertNotIn("origin/main has", self.clones.state().stdout)
        self.clones.state("--fetch")
        self.assertIn("origin/main has 1 commit", self.clones.state().stdout)

    def test_names_shared_files_and_features_that_changed(self):
        self.clones.other_pushes("specs/000-foundation/spec.md")
        self.clones.other_pushes(".specify/memory/constitution.md")
        self.clones.other_pushes("scripts/gate.ps1")
        self.clones.other_pushes("specs/003-other/spec.md")
        out = self.clones.state("--fetch").stdout
        self.assertIn("origin/main has 4 commits", out)
        self.assertIn("shared changed: .specify/memory/constitution.md, scripts/gate.ps1, specs/000-foundation/spec.md", out)
        self.assertIn("change.md", out)
        self.assertIn("features changed: specs/003-other", out)

    def test_a_feature_only_change_names_no_shared_files(self):
        self.clones.other_pushes("specs/003-other/spec.md")
        self.assertNotIn("shared changed", self.clones.state("--fetch").stdout)

    def test_lists_other_branches_still_in_progress(self):
        self.clones.other_pushes("specs/003-other/spec.md", ref="refs/heads/003-other")
        self.assertIn("other branches: origin/003-other", self.clones.state("--fetch").stdout)

    def test_an_unreachable_origin_never_stops_the_state(self):
        TwoClones.git(self.clones.repo.root, "remote", "set-url", "origin", str(self.clones.origin) + "-gone")
        out = self.clones.state("--fetch")
        self.assertEqual(out.returncode, 0)
        self.assertIn("STATE=", out.stdout)
        self.assertIn("could not reach origin", out.stdout)

    def test_no_remote_says_nothing(self):
        repo = Repo()
        self.addCleanup(repo.close)
        out = run(repo.root, "state", "--fetch")
        self.assertEqual(out.returncode, 0)
        self.assertNotIn("origin", out.stdout)


class HooksInstalledTest(unittest.TestCase):
    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.close)

    def hook(self, name):
        (self.repo.root / ".git/hooks" / name).write_text("#!/bin/sh\n", encoding="utf-8")

    def test_warns_when_a_clone_has_no_hooks(self):
        self.assertIn("run `pre-commit install`", self.repo.state())

    def test_warns_when_the_push_hook_is_missing(self):
        self.hook("pre-commit")
        self.assertIn("run `pre-commit install`", self.repo.state())

    def test_silent_when_both_are_installed(self):
        self.hook("pre-commit")
        self.hook("pre-push")
        self.assertNotIn("pre-commit install", self.repo.state())

    def test_silent_during_setup_which_installs_them(self):
        self.repo.write("scripts/gate.ps1", "# GATE-NOT-CONFIGURED\nexit 1\n")
        self.assertNotIn("pre-commit install", self.repo.state())


class PushCheckTest(unittest.TestCase):
    def setUp(self):
        self.clones = TwoClones()
        self.addCleanup(self.clones.close)

    def check(self):
        return run(self.clones.repo.root, "pushcheck")

    def test_passes_when_clean_and_up_to_date(self):
        self.assertEqual(self.check().returncode, 0)

    def test_refuses_a_branch_that_lacks_origin_main(self):
        self.clones.other_pushes("src/a.py")
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("origin/main", r.stderr)
        self.assertIn("merge", r.stderr)

    def test_passes_once_merged(self):
        self.clones.other_pushes("src/a.py")
        self.check()
        TwoClones.git(self.clones.repo.root, "merge", "-q", "--no-edit", "origin/main")
        self.assertEqual(self.check().returncode, 0)

    def test_refuses_uncommitted_changes_because_the_gate_would_test_them(self):
        self.clones.repo.write("src/new.py", "x\n")
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("uncommitted", r.stderr)

    def test_refuses_when_origin_cannot_be_reached(self):
        TwoClones.git(self.clones.repo.root, "remote", "set-url", "origin", str(self.clones.origin) + "-gone")
        r = self.check()
        self.assertEqual(r.returncode, 1)
        self.assertIn("could not reach origin", r.stderr)

    def test_first_push_to_an_empty_origin_passes(self):
        repo = Repo()
        self.addCleanup(repo.close)
        bare = Path(self.clones.tmp.name) / "empty.git"
        subprocess.run(["git", "init", "-q", "--bare", str(bare)], check=True)
        TwoClones.git(repo.root, "remote", "add", "origin", str(bare))
        self.assertEqual(run(repo.root, "pushcheck").returncode, 0)


COUNTING_GATE = "Add-Content -Path $env:GATE_LOG -Value 'ran'\nexit [int]$env:GATE_EXIT\n"


@unittest.skipUnless(shutil.which("pwsh"), "the gate runs with pwsh")
class GateTest(unittest.TestCase):
    """`flow.py gate` runs scripts/gate.ps1 once per set of files: a repeat on the same files is skipped."""

    def setUp(self):
        self.repo = Repo()
        self.addCleanup(self.repo.close)
        self.log = Path(self.repo.tmp.name + "-gate.log")
        self.addCleanup(lambda: self.log.unlink(missing_ok=True))
        self.repo.write("scripts/gate.ps1", COUNTING_GATE)
        self.repo.write(".gitignore", "ignored/\n")
        self.repo.commit()

    def gate(self, exit_code=0):
        env = {**os.environ, "CLAUDE_PROJECT_DIR": str(self.repo.root), "GATE_LOG": str(self.log),
               "GATE_EXIT": str(exit_code)}
        return subprocess.run([sys.executable, "-I", str(self.repo.root / ".claude/hooks/flow.py"), "gate"],
                              capture_output=True, text=True, cwd=self.repo.root, env=env)

    def runs(self):
        return len(self.log.read_text(encoding="utf-8").splitlines()) if self.log.exists() else 0

    def test_a_repeat_on_the_same_files_is_skipped(self):
        self.assertEqual(self.gate().returncode, 0)
        second = self.gate()
        self.assertEqual(second.returncode, 0)
        self.assertEqual(self.runs(), 1)
        self.assertIn("skipped", second.stdout)

    def test_a_changed_file_runs_it_again(self):
        self.gate()
        self.repo.write("CLAUDE.md", "router, changed\n")
        self.gate()
        self.assertEqual(self.runs(), 2)

    def test_a_new_untracked_file_runs_it_again_but_an_ignored_one_does_not(self):
        self.gate()
        self.repo.write("ignored/cache.txt", "x\n")
        self.gate()
        self.assertEqual(self.runs(), 1)
        self.repo.write("src/new.py", "x\n")
        self.gate()
        self.assertEqual(self.runs(), 2)

    def test_staging_and_committing_the_same_files_does_not_run_it_again(self):
        self.repo.write("src/a.py", "x\n")
        self.gate()  # before the commit, unstaged (finish.md step 2)
        subprocess.run(["git", "-C", str(self.repo.root), "add", "-A"], check=True)
        self.gate()  # the commit hook, staged
        self.repo.commit()
        self.gate()  # the push hook, committed
        self.assertEqual(self.runs(), 1)

    def test_a_failure_is_reported_and_never_remembered(self):
        self.assertEqual(self.gate(exit_code=1).returncode, 1)
        self.assertEqual(self.gate().returncode, 0)
        self.assertEqual(self.runs(), 2)

    def test_the_record_is_kept_out_of_the_working_tree(self):
        self.gate()
        status = subprocess.run(["git", "-C", str(self.repo.root), "status", "--porcelain"],
                                capture_output=True, text=True).stdout
        self.assertEqual(status, "")


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

    def test_write_and_fixed_read_in_separate_segments_are_allowed(self):
        state = "python -I .claude/hooks/flow.py state"
        self.assertEqual(self.bash(f'git commit -m "a -> b" && {state}').returncode, 0)
        self.assertEqual(self.bash(f"printf 'x' >> specs/001-demo/tasks.md && {state}").returncode, 0)
        self.assertEqual(self.bash("sed -i s/a/b/ specs/x.md; cat .claude/agents/reviewer.md").returncode, 0)

    def test_write_to_fixed_file_in_a_later_segment_is_blocked(self):
        self.assertEqual(self.bash("cat src/a.js && echo y > CLAUDE.md").returncode, 2)

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
