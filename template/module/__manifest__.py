# -*- coding: utf-8 -*-
# Copyright <YEAR(S)> <AUTHOR(S)>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Module name",
    "summary": "Module summary",
    "version": "11.0.1.0.0",
    "development_status": "Alpha|Beta|Production/Stable|Mature",
    "category": "Uncategorized",
    "website": "https://github.com/OCA/<repo>" or "https://github.com/OCA/<repo>/tree/<branch>/<addon>",
    "author": "<AUTHOR(S)>, Odoo Community Association (OCA)",
    "maintainers": [],
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "pre_init_hook": "pre_init_hook",
    "post_init_hook": "post_init_hook",
    "post_load": "post_load",
    "uninstall_hook": "uninstall_hook",
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "base",
    ],
    "data": [
        "security/some_model_security.xml",
        "security/ir.model.access.csv",
        "templates/assets.xml",
        "views/report_name.xml",
        "views/res_partner_view.xml",
        "wizards/wizard_model_view.xml",
    ],
    "demo": [
        "demo/assets.xml",
        "demo/res_partner_demo.xml",
    ],
    "qweb": [
        "static/src/xml/module_name.xml",
    ]
}
