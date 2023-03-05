# Copyright (c) 2018 ACSONE SA/NV
# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
import subprocess


def commit_if_needed(paths, message, add=True):
    if add:
        cmd = ["git", "add"] + paths
        subprocess.check_call(cmd)
    cmd = ["git", "diff", "--quiet", "--exit-code", "--cached", "--"] + paths
    r = subprocess.call(cmd)
    if r != 0:
        cmd = ["git", "commit", "-m", message, "--"] + paths
        subprocess.check_call(cmd)
        return True
    else:
        return False
