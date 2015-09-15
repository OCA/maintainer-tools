
import os
import tempfile
import unittest
from tools import autopep8_extended


class TestAutopep8Extended(unittest.TestCase):
    def setUp(self):
        self.directory_name = tempfile.mkdtemp()

    def run_autopep8_extended(self, fname, msgs):
        """Run autopep8 extended command.
        :param fname: String file name of file to check.
        :param msgs: List of msgs to check.
        """
        cmd = [
            "autopep8_extended.py", "-i",
            "--select=" + ','.join(msgs)
        ] + [fname]
        autopep8_extended.autopep8.main(cmd)

    def run_test(self, msgs, content, content_expected):
        """Run autopep8_extended in a file.
        :param msgs: List of msgs to check.
        :param content: String with source code.
        :param content_expected: String with source code expected.
        """
        fname_tmp1 = os.path.join(self.directory_name, 'tmp1')
        open(fname_tmp1, "w").write(content)
        self.run_autopep8_extended(fname_tmp1, msgs)
        content_returned = open(fname_tmp1).read()
        self.assertEqual(content_returned, content_expected)

    def test_camelcase(self):
        "Test normal case of snake_case to CamelCase"
        msgs = ["CW0001"]
        content = """# -*- coding: utf-8 -*-
hello_word = 3
class hello_world():
    def __init__(self):
        super(hello_world, self).__init__()
        hello_word = 4

hello_world()
parser = hello_world
parsed = hello_world()
"""
        content_expected = """# -*- coding: utf-8 -*-
hello_word = 3
class HelloWorld():
    def __init__(self):
        super(HelloWorld, self).__init__()
        hello_word = 4

HelloWorld()
parser = HelloWorld
parsed = HelloWorld()
"""
        self.run_test(msgs, content, content_expected)

    def test_coding(self):
        "Test coding and encoding lines."
        msgs = ["CW0001"]

        # coding first line
        content = "# -*- coding: utf-8 -*-\nhello_word = 3\n"
        content_expected = content
        self.run_test(msgs, content, content_expected)

        # coding second line
        content = "#\n# -*- coding: utf-8 -*-\nhello_word = 3\n"
        content_expected = content
        self.run_test(msgs, content, content_expected)

        # encoding first line
        content = "# -*- encoding: utf-8 -*-\nhello_word = 3\n"
        content_expected = content
        self.run_test(msgs, content, content_expected)

        # encoding second line
        content = "#\n# -*- encoding: utf-8 -*-\nhello_word = 3\n"
        content_expected = content
        self.run_test(msgs, content, content_expected)

    def test_wrong_camelcase(self):
        """Test wrong case when exists same class name two times
        but different style. Abort changes."""
        msgs = ["CW0001"]
        content = """# -*- coding: utf-8 -*-
class hello_world():
    def __init__(self):
        super(hello_world, self).__init__()

# Two classes with "same name".
class HelloWorld():
    def __init__(self):
        super(hello_world, self).__init__()
"""
        content_expected = content
        self.run_test(msgs, content, content_expected)

    def test_vim_comment(self):
        "Test delete vim comment"
        msgs = ["CW0002"]
        content = """hello1 = 'world1'
# vim:comment
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
#vim:comment
#vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
hello2 = 'world2'
"""
        content_expected = "hello1 = 'world1'\nhello2 = 'world2'\n"
        self.run_test(msgs, content, content_expected)

    def test_coding_comment(self):
        'Test replace coding comment'
        msgs = ["CW0003", "CW0004"]
        content_expected = "# coding: utf-8\nhello = 'world'\n"

        # coding first line
        content = "# -*- coding: utf-8 -*-\nhello = 'world'\n"
        self.run_test(msgs, content, content_expected)

        # coding second line
        content = "\n# -*- coding: utf-8 -*-\nhello = 'world'\n"
        self.run_test(msgs, content, '\n' + content_expected)

        # encoding first line
        content = "# -*- encoding: utf-8 -*-\nhello = 'world'\n"
        self.run_test(msgs, content, content_expected)

        # encoding second line
        content = "\n# -*- encoding: utf-8 -*-\nhello = 'world'\n"
        self.run_test(msgs, content, '\n' + content_expected)

        # Normal coding
        content = "# coding: utf-8\nhello = 'world'\n"
        self.run_test(msgs, content, content_expected)

        # coding missed
        content = "hello = 'world'\n"
        self.run_test(msgs, content, content_expected)

        # anormal coding: third line
        content = "#\n\n\n# -*- encoding: utf-8 -*-\nhello = 'world'\n"
        content_expected = "# coding: utf-8\n" + content
        self.run_test(msgs, content, content_expected)

        # empty file
        self.run_test(msgs, "", "")

        # one empty line
        self.run_test(msgs, "\n", "# coding: utf-8\n\n")


if __name__ == '__main__':
    unittest.main()
