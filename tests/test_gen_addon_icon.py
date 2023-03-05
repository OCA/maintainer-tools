# License AGPLv3 (https://www.gnu.org/licenses/agpl-3.0-standalone.html)
# Copyright (c) 2019 Eficent Business and IT Consulting Services S.L.
#        (http://www.eficent.com)

import os
import subprocess
import sys

from tools.gen_addon_icon import ICONS_DIR, ICON_TYPE


def test_gen_addon_icon(tmp_path):
    addon_dir = tmp_path / "addon"
    addon_dir.mkdir()
    with (addon_dir / "__manifest__.py").open("w") as f:
        f.write("{'name': 'addon'}")
    cmd = [
        sys.executable,
        "-m",
        "tools.gen_addon_icon",
        "--addon-dir",
        str(addon_dir),
    ]
    subprocess.check_output(cmd, stderr=subprocess.STDOUT)
    assert os.path.exists(
        os.path.join(addon_dir._str, ICONS_DIR, "icon.%s" % ICON_TYPE)
    )
