# -*- coding: utf-8 -*-
# © <YEAR(S)> <AUTHOR(S)>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).
{
    "name": "Module name",
    "summary": "Module summary",
    "version": "8.0.1.0.0",
    "category": "Uncategorized",
    "website": "https://odoo-community.org/",
    "author": "<AUTHOR(S)>, Odoo Community Association (OCA)",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "external_dependencies": {
        "python": [],
        "bin": [],
    },
    "depends": [
        "base",
    ],
    "data": [
        "security/some_model.xml",
        "security/ir.model.access.csv",
        "views/assets.xml",
        "views/res_partner.xml",
        "report/name.xml",
        "wizard/wizard_model.xml",
    ],
    "demo": [
        "demo/res_partner.xml",
    ],
    "qweb": [
        "static/src/xml/module_name.xml",
    ]
}
