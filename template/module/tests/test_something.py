# -*- coding: utf-8 -*-
# Copyright <YEAR(S)> <AUTHOR(S)>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp.tests.common import HttpCase, TransactionCase


class SomethingCase(TransactionCase):
    def setUp(self, *args, **kwargs):
        super(SomethingCase, self).setUp(*args, **kwargs)

        # TODO Replace this for something useful or delete this method
        self.do_something_before_all_tests()

    def tearDown(self, *args, **kwargs):
        # TODO Replace this for something useful or delete this method
        self.do_something_after_all_tests()

        return super(SomethingCase, self).tearDown(*args, **kwargs)

    def test_something(self):
        """First line of docstring appears in test logs.

        Other lines do not.

        Any method starting with ``test_`` will be tested.
        """
        pass


class UICase(HttpCase):
    def test_ui_web(self):
        """Test backend tests."""
        self.phantom_js("/web/tests?mod=module_name", "", login="admin")

    def test_ui_website(self):
        """Test frontend tour."""
        self.phantom_js(
            url_path="/",
            code="odoo.__DEBUG__.services['web.Tour']"
                 ".run('test_module_name', 'test')",
            ready="odoo.__DEBUG__.services['web.Tour'].tours.test_module_name",
            login="admin")
