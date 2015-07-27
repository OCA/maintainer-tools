# OCA Guidelines

This page introduces the coding guidelines for projects hosted under OCA. These
guidelines aim to improve the quality of the code: better readability of
source, better maintainability, better stability and fewer regressions.

These are loosely based on the [Odoo Guidelines](https://www.odoo.com/documentation/8.0/reference/guidelines.html)
with adaptations to improve their guidelines and make them more suitable for
this project's own needs. Readers used to the Odoo Guidelines can skip to the
[Differences With Odoo Guidelines](#differences-with-odoo-guidelines)
section.

## Modules

* Use of the singular form in module name (or use "multi"),
  except when compound of module name or object Odoo
  that is already in the plural (i.e. mrp_operations_....).
* Use the [description template](https://github.com/OCA/maintainer-tools/tree/master/template/module)

### Directories

A module is organised in a few directory:

* `controllers/`: contains controllers (http routes)
* `data/`: data xml
* `demo/`: demo xml
* `models/`: models definition
* `report/`: reporting models (BI/analysis), Webkit/RML print report templates
* `static/`: contains the web assets, separated into `css/`, `js/`, `img/`,
  `lib/`, ...
* `views/`: contains the views and templates, and QWeb report print templates
* `wizards/`: wizard model and views

### File naming

For `models`, `views` and `data` declarations, split files by the model
involved, either created or inherited. These files should be named after the
model. For example, demo data for res.partner should go in a file named
demo/res_partner.xml and a view for partner should go in a file named
views/res_partner.xml.

For model named `<main_model>` the following files may be created:

* `models/<main_model>.py`
* `data/<main_model>.xml`
* `demo/<main_model>.xml`
* `templates/<main_model>.xml`
* `views/<main_model>.xml`

For `controller`, the only file should be named `main.py`.

For `static files`, the name pattern is `<module_name>.ext` (i.e.
`static/js/im_chat.js`, `static/css/im_chat.css`, `static/xml/im_chat.xml`,
...). Don't link data (image, libraries) outside Odoo: don't use an url to an
image but copy it in our codebase instead.

The complete tree should looks like

```
addons/<my_module_name>/
|-- __init__.py
|-- __openerp__.py
|-- controllers/
|   |-- __init__.py
|   `-- main.py
|-- data/
|   `-- <main_model>.xml
|-- demo/
|   `-- <inherited_model>.xml
|-- models/
|   |-- __init__.py
|   |-- <main_model>.py
|   `-- <inherited_model>.py
|-- report/
|   |-- __init__.py
|   |-- report.xml
|   |-- <bi_reporting_model>.py
|   |-- report_<rml_report_name>.rml
|   |-- report_<rml_report_name>.py
|   |-- <webkit_report_name>.mako
|-- security/
|   |-- ir.model.access.csv
|   `-- <main_model>_security.xml
|-- static/
|   |-- img/
|   |   |-- my_little_kitten.png
|   |   `-- troll.jpg
|   |-- lib/
|   |   `-- external_lib/
|   `-- src/
|       |-- js/
|       |   `-- <my_module_name>.js
|       |-- css/
|       |   `-- <my_module_name>.css
|       |-- less/
|       |   `-- <my_module_name>.less
|       `-- xml/
|           `-- <my_module_name>.xml
|-- views/
|   |-- <main_model>.xml
|   `-- <inherited_main_model>_views.xml
|   |-- report_<qweb_report>.xml
|-- templates/
|   |-- <main_model>.xml
|   `-- <inherited_main_model>.xml
`-- wizards/
    |-- __init__.py
    |-- <wizard_model>.py
    `-- <wizard_model>.xml
```

Filename should only use only `[a-z0-9_]`

Use correct file permissions: folder 755 and file 644.

## XML files

### Format

When declaring a record in XML,

* Place `id` attribute before `model`
* For field declaration, `name` attribute is first. Then place the `value`
  either in the `field` tag, either in the `eval` attribute, and finally other
  attributes (widget, options, ...) ordered by importance.

* Try to group the record by model. In case of dependencies between
  action/menu/views, the convention may not be applicable.
* Use naming convention defined at the next point
* The tag `<data>` is only used to set not-updatable data with `noupdate=1`

```xml
<record id="view_id" model="ir.ui.view">
    <field name="name">view.name</field>
    <field name="model">object_name</field>
    <field name="priority" eval="16"/>
    <field name="arch" type="xml">
        <tree>
            <field name="my_field_1"/>
            <field name="my_field_2" string="My Label" widget="statusbar" statusbar_visible="draft,sent,progress,done" statusbar_colors='{"invoice_except":"red","waiting_date":"blue"}' />
        </tree>
    </field>
</record>
```

### Naming xml_id

#### Security, View and Action

Use the following pattern:

* For a menu: `<model_name>_menu`
* For a view: `<model_name>_view_<view_type>`, where `view_type` is kanban,
  form, tree, search, ...
* For an action: the main action respects `<model_name>_action`. Others are
  suffixed with `_<detail>`, where `detail` is a underscore lowercase string
  explaining a little bit the action (Should not be long). This is used only if
  multiple action are declared for the model.
* For a group: `<model_name>_group_<group_name>` where `group_name` is the
  name of the group, genrally 'user', 'manager', ...
* For a rule: `<model_name>_rule_<concerned_group>` where `concerned_group` is
  the short name of the concerned group ('user' for the
  'model_name_group_user', 'public' for public user, 'company' for
  multi-company rules, ...).

```xml
<!-- views and menus -->
<record id="model_name_menu" model="ir.ui.menu">
    ...
</record>

<record id="model_name_view_form" model="ir.ui.view">
    ...
</record>

<record id="model_name_view_kanban" model="ir.ui.view">
    ...
</record>

<!-- actions -->
<record id="model_name_action" model="ir.actions.act_window">
    ...
</record>

<record id="model_name_action_child_list" model="ir.actions.act_window">
    ...
</record>

<!-- security -->
<record id="model_name_group_user" model="res.groups">
    ...
</record>

<record id="model_name_rule_public" model="ir.rule">
    ...
</record>

<record id="model_name_rule_company" model="ir.rule">
    ...
</record>
```

#### Inherited XML

A module can extend a view only one time.

The naming rules should be followed even when a view is inherited, the module
name prevents xid conflicts. In the case where a view inherited has a name which
does not follow the guidelines set above, prefer naming the inherited view
after the original over using a name which follows the guidelines. This eases
looking up the original view and other inheritance if they all have the same
name.


```xml
<record id="original_id" model="ir.ui.view">
<field name="inherit_id" ref="original_module.original_id"/>
    ...
</record>
```

## Python

### PEP8 options

Using the linter flake8 can help to see syntax and semantic warning or error.
Project Source Code should adhere to PEP8 and PyFlakes standards with
a few exceptions:

* In `__init__.py` only
    *  F401: `module` imported but unused

### Imports

The imports are ordered as

1. Externals libs (One per line sorted and splitted in python stdlib)
2. Imports of `openerp`
3. Imports from Odoo modules (rarely, and only if necessary)
4. Local imports in the relative form

Inside these 4 groups, the imported lines are alphabetically sorted.

```python
# 1: imports of python lib
import base64
import re
import time
# 2:  imports of openerp
import openerp
from openerp import api, fields, models  # alphabetically ordered
from openerp.tools.safe_eval import safe_eval as eval
from openerp.tools.translate import _
# 3:  imports from odoo modules
from openerp.addons.website.models.website import slug
from openerp.addons.web.controllers.main import login_redirect
# 4: local imports
from . import utils
```

 * Note:
   * You can use [isort](https://pypi.python.org/pypi/isort/) to auto sort import's.
   * Install with `pip install isort` and use with `isort myfile.py`.

### Idioms

* Each python file should have ``# -*- coding: utf-8 -*-`` as first line
* Prefer `%` over `.format()`, prefer `%(varname)` instead of positional.
  This is better for translation and clarity.
* Always favor **Readability** over **conciseness** or using the language
  features or idioms.
* Use list comprehension, dict comprehension, and basic manipulation using
  `map`, `filter`, `sum`, ... They make the code more pythonic, easier to read
   and are generally more efficient
* The same applies for recordset methods: use `filtered`, `mapped`, `sorted`,
  ...
* Exceptions: Use `from openerp.exceptions import Warning as UserError` (v8)
  or `from openerp.exceptions import UserError` (v9)
  or find a more appropriate exception in `openerp.exceptions.py`
* Document your code
    * Docstring on methods should explain the purpose of a function,
      not a summary of the code
    * Simple comments for parts of code which do things which are not
      immediately obvious
    * Too many comments are usually a sign that the code is unreadable needs to
      be refactored
* Use meaningful variable/class/method names
* If a function is too long or too indented due to loops, this is a sign
  that it needs to be refactored into smaller functions
* If a function call, dictionary, list or tuple is broken into two lines,
  break it at the opening symbol. This adds a four space indent to the next
  line instead of starting the next line at the opening symbol.
  Example:
  ```python
  partner_id = fields.Many2one(
      "res.partner",
      "Partner",
      "Required",
  )
  ```
* When making a comma separated list, dict, tuple, ... with one element per
  line, append a comma to the last element. This makes it so the next element
  added only changes one line in the changeset instead of changing the last
  element to simply add a comma.
* If an argument to a function call is not immediately obvious, prefer using
  named parameter.
* Use English variable names and write comments in english. Strings which need
  to be displayed in other languages should be translated using the translation
  system

### Symbols

#### Odoo Python Class

Use camelcase for code in api v8, underscore lowercase notation for old api.

```python
class AccountInvoice(models.Model):
    ...

class account_invoice(orm.Model):
    ...
```

#### Variable name :
* use camelcase for model variable
* use underscore lowercase notation for common variable.
* since new API works with record or recordset instead of id list, don't suffix
  variable name with `_id` or `_ids` if they do not contain an id or a list of
  ids.

```python
ResPartner = self.env['res.partner']
partners = ResPartner.browse(ids)
partner_id = partners[0].id
```

### Field
* `One2Many` and `Many2Many` fields should always have `_ids` as suffix
  (example: sale_order_line_ids)
* `Many2One` fields should have `_id` as suffix
  (example: partner_id, user_id, ...)
* Method conventions
    * Compute Field: the compute method pattern is `_compute_<field_name>`
    * Search method: the search method pattern is `_search_<field_name>`
    * Default method: the default method pattern is `_default_<field_name>`
    * Onchange method: the onchange method pattern is `_onchange_<field_name>`
    * Constraint method: the constraint method pattern is
      `_check_<constraint_name>`
    * Action method: an object action method is prefix with `action_`.
      Its decorator is `@api.multi`, but since it use only one record, add
      `self.ensure_one()` at the beginning of the method.

* Default functions should be declared with a lambda call on self. The reason
  for this is so a default function can be inherited. Assigning a function
  pointer directly to the `default` parameter does not allow for inheritance.

  ```python
  a_field(..., default=lambda self: self._default_get())
  ```

* In a Model attribute order should be
    1. Private attributes (`_name`, `_description`, `_inherit`, ...)
    2. Fields declarations
    3. Default method and `_default_get`
    4. Compute and search methods in the same order than field declaration
    5. Constrains methods (`@api.constrains`) and onchange methods
       (`@api.onchange`)
    6. CRUD methods (ORM overrides)
    7. Action methods
    8. And finally, other business methods.

```python
class Event(models.Model):
    # Private attributes
    _name = 'event.event'
    _description = 'Event'

    # Fields declaration
    name = fields.Char(string='Name', default=_default_name)
    seats_reserved = fields.Integer(
        oldname='register_current',
        string='Reserved Seats',
        store=True,
        readonly=True,
        compute='_compute_seats',
    )
    seats_available = fields.Integer(
        oldname='register_avail',
        string='Available Seats',
        store=True,
        readonly=True,
        compute='_compute_seats',
    )
    price = fields.Integer(string='Price')

    # Default methods
    def _default_name(self):
            ...

    # compute and search fields, in the same order that fields declaration
    @api.multi
    @api.depends('seats_max', 'registration_ids.state')
    def _compute_seats(self):
        ...

    # Constraints and onchanges
    @api.constrains('seats_max', 'seats_available')
    def _check_seats_limit(self):
        ...

    @api.onchange('date_begin')
    def _onchange_date_begin(self):
        ...

    # CRUD methods
    def create(self):
        ...

    # Action methods
    @api.multi
    def action_validate(self):
        self.ensure_one()
        ...

    # Business methods
    def mail_user_confirm(self):
        ...
```

## Javascript

* `use strict;` is recommended for all javascript files
* Use a linter (jshint, ...)
* Never add minified Javascript Libraries
* Use camelcase for class declaration

## CSS

* Prefix all your class with `o_<module_name>` where `module_name` is the
  technical name of the module (`sale`, `im_chat`, ...) or the main route
  reserved by the module (for website module mainly,
  i.e. `o_forum` for website_forum module). The only exception for this rule is
  the webclient: it simply use `o_` prefix.
* Avoid using id
* Use bootstrap native class
* Use underscore lowercase notation to name class

## Tests

As a general rule, a bug fix should come with a unittest which would fail
without the fix itself. This is to assure that regression will not happen in
the future. It also is a good way to show that the fix works in all cases.

New modules or addtions should ideally test all the functions defined. The
coveralls utility will comment on pull requests indicating if coverage
increased or decreased. If it has decreased, this is usually a sign that a test
should be added. The coveralls web interface can also show which lines need
test cases.

## Git

### Commit message

Write a short commit summary without prefixing it. It should not be longer than
50 characters: `This is a commit message`

Then, in the message itself, specify the part of the code impacted by your
changes (module name, lib, transversal object, ...) and a description of the
changes. This part should be multiple lines no longer than 80 characters.

* Commit messages are in English
* Merge proposals should follow the same rules as the title of the propsal is
  the first line of the merge commit and the description corresponds to commit
  description.
* Always put meaning full commit message: commit message should be
  self explanatory (long enough) including the name of the module that
  has been changed and the reason behind that change. Do not use
  single words like "bugfix" or "improvements".
* Avoid commits which simultaneously impacts lots of modules. Try to
  splits into different commits where impacted modules are different
  (It will be helpful when we are going to revert that module
  separately).
* Only make a single commit per logical change set. Do not add commits such as
  "Fix pep8", "Code review" or "Add unittest" if they fix commits which are
   being proposed
* Use present imperative (Fix formating, Remove unused field) avoid appending
  's' to verbs: Fixes, Removes

```
website: remove unused alert div

Fix look of input-group-btn
Bootstrap's CSS depends on the input-group-btn element being the first/last
child of its parent.
This was not the case because of the invisible and useless alert.
```
```
web: add module system to the web client
This commit introduces a new module system for the javascript code.
Instead of using global ...
```

### Review

Peer review is the only way to ensure good quality of the code and to be able
to rely on the others devs. The peer review in this project will be made by
making Merge Proposal. It will serve the following main purposes:

* Having a second look on his work to avoid unintended problems / bugs
* Avoid technical or business design flaws
* Allow the coordination and convergence of the devs by informing community of
  what has been done
* Allow the responsibles to look at every devs and keep the interested people
  informed of what has been done
* Prevent addons incompatibilities when/if possible
* The rationale for peer review has its equivalent in Linus's law, often
  phrased: "Given enough eyeballs, all bugs are shallow"

Meaning "If there are enough reviewers, all problems are easy to solve". Eric
S. Raymond has written influentially about peer review in software development:
 http://en.wikipedia.org/wiki/Software_peer_review.

Please respect a few basic rules:

* Two reviewers must approve a merge proposal in order to be able to merge it
* 5 calendar days must be given to be able to merge it
* A MP can be merged in less that 5 calendar days if and only if it is approved
  by 3 reviewers. If you are in a hurry just send a mail at
  openerp-community-reviewer@lists.launchpad.net or ask by IRC (FreeNode
  server, openobject channel).
* Is the module generic enough to be part of community addons?
* Is the module duplicating features with other community addons?
* Does the documentation allow to understand what it does and how to use it?
* Is the problem it tries to resolve adressed the good way, using good
  concepts?
* Are there some use cases?
* Is there any setup in code? Should not!
* Are there demo data?

Most reference can be found here:
* http://insidecoding.com/2013/01/07/code-review-guidelines/

There are the following important part in a review:

* Start by thanking the contributor / developer for his work. No matter the
  issue of the MP, someone make work for you here, so be thankful for that.
* Be cordial and polite. Nothing is obvious in a MP.
* The description of the changes should be clear enough for you to understand
  his purpose and if apply, contain the reference feature instance in order to
  allow people to run and test the review
* Choose the review tag (comment, approve, rejected, needs information,...)
  and don't forget to add a type of review to let people know:
  * Code review: means you look at the code
  * Test: means you tested it functionally speaking

While making the merge, please respect the author using the `--author` option
when committing. The author is found using the bzr log command. Use the commit
message provided by the contributor if any.

It makes sense to be picky in the following cases:

* The origin/reason for the patch/dev is not documented very well
* No adapted / convenient description written in the `__openerp__.py` file for
  the module
* Tests or scenario are not all green and/or not adapted
* Having tests is very much encouraged
* Issues with license, copyright, authorship
* Respect of Odoo/community conventions
* Code design and best practices



The long description try to explain the **why** not the **what**, the **what**
can be seen in the diff.

## Github

### Teams

* Team name must not contain odoo or openerp
* Team name for localization is "Belgium Maintainers" for Belgium

### Repositories

* Project name must not contain odoo or openerp
* Project name for localization is "l10n_belgium" for Belgium
* Project name for connectors is "connector-magento" for Magento connector

### Issue

* Issues are used for blueprints and bugs.

## Differences With Odoo Guidelines

Not the entire Odoo guidelines fit OCA modules needs. In many cases rules need
to be more stringent. In other cases, conventions are improved for better
maintainability in an ecosystem of many smaller modules.

The differences include:

* [Module Structure](#modules)
    * Using one file per model
    * Separating data and demo data xml folders
    * Not changing xml_ids while inheriting
* [Python](#python)
    * Fuller PEP8 compliance
    * Using relative import for local files
    * More python idioms
    * A way to deal with long comma-separated lines
    * Hints on documentation
* [Fields](#fields)
    * A hint for function defaults
* [Tests Section Added](#tests)
* [Git](#git)
    * No prefixing of commits
    * Default git commit message standards
    * Squashing changes in pull requests when necessary
    * Use of present imperative
* [Github Section](#github)
* [Review Section](#review)
