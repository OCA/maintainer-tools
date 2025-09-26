import ast
import re
import subprocess
from pathlib import Path

import click


def _mark_modules_uninstallable(addons_dir: Path) -> None:
    for manifest_path in addons_dir.glob("*/__manifest__.py"):
        manifest_text = manifest_path.read_text(encoding="utf-8")
        manifest = ast.literal_eval(manifest_text)
        if "installable" not in manifest:
            src = r",?\s*}"
            dest = ",\n    'installable': False,\n}"
        else:
            src = "[\"']installable[\"']: *True"
            dest = '"installable": False'
        manifest_path.write_text(re.sub(src, dest, manifest_text, re.DOTALL))


@click.command()
@click.option("--odoo-version", required=True)
@click.option("--new-branch-name")
@click.option(
    "--addons-dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    default=".",
)
@click.option(
    "--data",
    multiple=True,
    help="Additional copier data, as key=value",
)
def main(
    odoo_version: str,
    new_branch_name: str | None,
    addons_dir: Path,
    data: list[str],
) -> None:
    """Create a new branch off an existing branch and set all addons installable=False.

    To use it, go to a git clone of a repo and checkout the branch you want to start from.
    """
    if not new_branch_name:
        new_branch_name = odoo_version
    result = subprocess.run(
        ["git", "rev-parse", "--abbrev-ref", "HEAD"],
        check=True,
        text=True,
        capture_output=True,
    )
    previous_branch = result.stdout.strip()
    subprocess.run(
        [
            "git",
            "checkout",
            "-b",
            new_branch_name,
        ],
        check=True,
    )
    result = subprocess.run(
        [
            "copier",
            "recopy",  # override local changes when creating a new branch
            "--trust",
            "--defaults",
            "--overwrite",
            f"--data=odoo_version={odoo_version}",
            *(f"--data={d}" for d in data),
        ],
    )
    if result.returncode != 0:
        raise SystemExit("copier update failed, please fix manually")
    result = subprocess.run(
        [
            "git",
            "diff",
            "--diff-filter=U",
            "--quiet",
        ],
    )
    if result.returncode != 0:
        raise SystemExit(
            "There are merge conflicts after copier update, please fix manually"
        )
    _mark_modules_uninstallable(addons_dir)
    if Path(".pre-commit-config.yaml").exists():
        # First run pre-commit on .pre-commit-config.yaml, to exclude
        # addons that are not installable.
        subprocess.run(
            [
                "pre-commit",
                "run",
                "--files",
                ".pre-commit-config.yaml",
            ],
            check=False,
        )
        # Run pre-commit once to let it apply auto fixes.
        subprocess.run(
            [
                "pre-commit",
                "run",
                "--all-files",
            ],
            check=False,
        )
        # Run pre-commit a second time to check that everything is green.
        result = subprocess.run(
            [
                "pre-commit",
                "run",
                "--all-files",
            ],
            check=False,
        )
        if result.returncode != 0:
            raise SystemExit("pre-commit failed, please fix manually")
    subprocess.run(
        [
            "git",
            "add",
            ".",
        ],
        check=True,
    )
    subprocess.run(
        [
            "git",
            "commit",
            "-m",
            f"[MIG] Create {new_branch_name} from {previous_branch} "
            f"for Odoo {odoo_version}",
        ],
        check=True,
    )
