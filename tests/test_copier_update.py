import subprocess
from contextlib import contextmanager

from click.testing import CliRunner

from tools import copier_update


def _git(*args, cwd):
    return subprocess.check_output(["git", *args], cwd=cwd, text=True)


def _make_copier_conflict(repo):
    """Leave the repo like copier update does when a file has a conflict."""
    path = repo / ".pre-commit-config.yaml"
    path.write_text(
        "<<<<<<< before updating\nold\n=======\nnew\n>>>>>>> after updating\n"
    )
    sha = _git("hash-object", "-w", str(path), cwd=repo).strip()
    subprocess.run(
        ["git", "update-index", "--index-info"],
        input=(
            f"0 {'0' * 40}\t.pre-commit-config.yaml\n"
            f"100644 {sha} 2\t.pre-commit-config.yaml\n"
            f"100644 {sha} 3\t.pre-commit-config.yaml\n"
        ),
        text=True,
        cwd=repo,
        check=True,
    )


def test_copier_update_conflict_not_pushed(tmp_path, monkeypatch):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git("init", "-b", "16.0", cwd=repo)
    (repo / ".copier-answers.yml").write_text("_commit: v1\n")
    (repo / ".pre-commit-config.yaml").write_text("old\n")
    _git("add", ".", cwd=repo)
    _git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-m", "init", cwd=repo)
    monkeypatch.chdir(repo)

    @contextmanager
    def fake_clone(**kwargs):
        yield

    calls = []
    real_call = subprocess.call
    real_check_call = subprocess.check_call

    def fake_call(cmd, *args, **kwargs):
        if cmd[0] == "copier":
            _make_copier_conflict(repo)
            return 0
        if cmd[0] == "pre-commit":
            return 0
        return real_call(cmd, *args, **kwargs)

    def fake_check_call(cmd, *args, **kwargs):
        if cmd[:2] in (["git", "push"], ["gh", "pr"]):
            calls.append(cmd)
            return 0
        return real_check_call(cmd, *args, **kwargs)

    monkeypatch.setattr(copier_update, "temporary_clone", fake_clone)
    monkeypatch.setattr(copier_update.subprocess, "call", fake_call)
    monkeypatch.setattr(copier_update.subprocess, "check_call", fake_check_call)
    monkeypatch.setattr(
        copier_update, "_get_update_dotfiles_open_pr", lambda *a, **kw: None
    )
    result = CliRunner().invoke(
        copier_update.main, ["--repos", "repo", "--branches", "16.0"]
    )
    assert result.exit_code == 0, result.output
    assert ["git", "push"] not in calls
    assert ["git", "push", "-f", "origin", "16.0-ocabot-update-dotfiles"] in calls
    assert any(cmd[:3] == ["gh", "pr", "create"] for cmd in calls)
