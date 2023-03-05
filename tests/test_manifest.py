# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)

import os

from tools import manifest


HERE = os.path.dirname(__file__)
TEST_REPO_DIR = os.path.join(HERE, "test_repo")


def test_manifest_find_addons():
    addons = list(manifest.find_addons(TEST_REPO_DIR))
    assert len(addons) == 1
    assert addons[0][0] == "module1"


def test_manifest_find_addons_uninstallable():
    addons = list(manifest.find_addons(TEST_REPO_DIR, installable_only=False))
    assert len(addons) == 2
    assert set((addons[0][0], addons[1][0])) == set(("module1", "module2"))
