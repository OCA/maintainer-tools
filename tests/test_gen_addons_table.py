import os
import subprocess
import unittest


class TestGenAddonsTable(unittest.TestCase):

    def test_1(self):
        dirname = os.path.dirname(__file__)
        cwd = os.path.join(dirname, 'test_repo')
        gen_addons_table = os.path.join(dirname, '..', 'tools',
                                        'gen_addons_table.py')
        readme_filename = os.path.join(dirname, 'test_repo',
                                       'README.md')
        readme_before = open(readme_filename).read()
        readme_expected_filename = os.path.join(dirname, 'test_repo',
                                                'README.md.expected')
        readme_expected = open(readme_expected_filename).read()
        try:
            res = subprocess.call([gen_addons_table], cwd=cwd)
            self.assertEquals(res, 0, 'gen_addons_table failed')
            readme_after = open(readme_filename).read()
            self.assertEquals(readme_after, readme_expected,
                              'gen_addons_table did not generate '
                              'expected result')
        finally:
            open(readme_filename, 'w').write(readme_before)
