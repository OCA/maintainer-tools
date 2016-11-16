# OCA Guidelines

This page introduces the coding guidelines for projects hosted under OCA. These
guidelines aim to improve the quality of the code: better readability of
source, better maintainability, better stability and fewer regressions.

These are loosely based on the [Odoo Guidelines](https://www.odoo.com/documentation/8.0/reference/guidelines.html)
and [Old Odoo Guidelines](https://doc.odoo.com/contribute/15_guidelines/coding_guidelines_framework.html)
with adaptations to improve their guidelines and make them more suitable for
this project's own needs. Readers used to the Odoo Guidelines can skip to the
[Differences With Odoo Guidelines](#differences-with-odoo-guidelines)
section.

##### Table of Contents

  * [OCA Guidelines](#oca-guidelines)
    * [Modules](#modules)
      * [Version numbers](#version-numbers)
      * [Directories](#directories)
      * [File naming](#file-naming)
      * [Installation hooks](#installation-hooks)
    * [XML files](#xml-files)
      * [Format](#format)
      * [Records](#records)
      * [Naming xml_id](#naming-xml_id)
        * [Security, View and Action](#security-view-and-action)
        * [Inherited XML](#inherited-xml)
      * [External dependencies](#external-dependencies)
        * [`__openerp__.py`](#__openerp__py)
        * [ImportError](#importerror)
        * [README](#user-content-readme)
    * [Python](#python)
      * [PEP8 options](#pep8-options)
      * [Imports](#imports)
      * [Idioms](#idioms)
      * [Symbols](#symbols)
        * [Odoo Python Classes](#odoo-python-classes)
        * [Variable names](#variable-names)
      * [SQL](#sql)
        * [No SQL Injection](#no-sql-injection)
        * [Never commit the transaction](#never-commit-the-transaction)
      * [Do not bypass the ORM](#do-not-bypass-the-orm)
      * [Models](#models)
      * [Fields](#fields)
    * [Javascript](#javascript)
    * [CSS](#css)
    * [Tests](#tests)
    * [Git](#git)
      * [Commit message](#commit-message)
      * [Review](#review)
        * [Please respect a few basic rules:](#please-respect-a-few-basic-rules)
        * [There are the following important parts in a review:](#there-are-the-following-important-parts-in-a-review)
        * [It makes sense to be picky in the following cases:](#it-makes-sense-to-be-picky-in-the-following-cases)
    * [Github](#github)
      * [Teams](#teams)
      * [Repositories](#repositories)
      * [Issues](#issues)
    * [Differences With Odoo Guidelines](#differences-with-odoo-guidelines)
  * [Backporting Odoo Modules](#backporting-odoo-modules)

## Modules

* Use of the singular form in module name (or use "multi"),
  except when compound of module name or object Odoo
  that is already in the plural (i.e. `mrp_operations_...`).
* If your module's purpose is to serve as a base for other modules, prefix its
  name with `base_`. I.e. `base_location_nuts`.
* When creating a localization module, prefix its name with `l10n_CC_`, where
  `CC` is its country code. I.e. `l10n_es_pos`.
* When extending an Odoo module, prefix yours with that module's name. I.e.
  `mail_forward`.
* When combining an Odoo module with another from OCA, Odoo's name goes before.
  I.e., if you want to combine Odoo's `crm` with OCA's `partner_firstname`, the
  name should be `crm_partner_firstname`.
* Use the [description template](https://github.com/OCA/maintainer-tools/tree/master/template/module) but remove sections with no meaningful content.
* In the `__openerp__.py`/`__manifest__.py`  manifest file:
  * Avoid empty keys
  * Make sure it has the `license` and `images` keys.
  * Make sure the text `,Odoo Community Association (OCA)` is appended
    to the `author` text.
* Don't use your company logo or your corporate branding. Using the website, the author and the list of contributors is enough for people to know about your employer/company and contact you.

### Version numbers

The version number in the module manifest should be the Odoo major
version (e.g. `8.0`) followed by the module `x.y.z` version numbers.
For example: `8.0.1.0.0` is expected for the first release of an 8.0
module.

The `x.y.z` version numbers follow the semantics `breaking.feature.fix`:

  * `x` increments when the data model or the views had significant
    changes. Data migration might be needed, or depending modules might
    be affected.
  * `y` increments when non-breaking new features are added. A module
    upgrade will probably be needed.
  * `z` increments when bugfixes were made. Usually a server restart
    is needed for the fixes to be made available.

If applicable, breaking changes are expected to include instructions
or scripts to perform migration on current installations.


### Directories

A module is organized in a few directories:

* `controllers/`: contains controllers (http routes)
* `data/`: data xml
* `demo/`: demo xml
* `models/`: model definitions
* `report/`: reporting models (BI/analysis), Webkit/RML print report templates
* `static/`: contains the web assets, separated into `css/`, `js/`, `img/`,
  `lib/`, ...
* `views/`: contains the views and templates, and QWeb report print templates
* `wizards/`: wizard model and views
* `examples/`: external files


### File naming

For `models`, `views` and `data` declarations, split files by the model
involved, either created or inherited. These files should be named after the
model. For example, demo data for res.partner should go in a file named
`demo/res_partner.xml` and a view for partner should go in a file named
`views/res_partner.xml`. An exception can be made when the model is a 
model intended to be used only as a one2many model nested on the main 
model. In this case, you can include the model definition inside it.
Example `sale.order.line` model can be together with `sale.order` in
the file `models/sale_order.py`.

For model named `<main_model>` the following files may be created:

* `models/<main_model>.py`
* `data/<main_model>.xml`
* `demo/<main_model>.xml`
* `templates/<main_model>.xml`
* `views/<main_model>.xml`

For `controller`, if there is only one file it should be named `main.py`.
If there are several controller classes or functions you can split them into
several files.

For `static files`, the name pattern is `<module_name>.ext` (i.e.
`static/js/im_chat.js`, `static/css/im_chat.css`, `static/xml/im_chat.xml`,
...). Don't link data (image, libraries) outside Odoo: don't use an url to an
image but copy it in our codebase instead.

### Installation hooks
When **`pre_init_hook`**, **`post_init_hook`** and **`uninstall_hook`** are
used, they should be placed in **`hooks.py`** located at the root of module
directory structure and keys in the manifest file keeps the same as the
following

```python
{
    ...
    'pre_init_hook': 'pre_init_hook',
    'post_init_hook': 'post_init_hook',
    'uninstall_hook': 'uninstall_hook',
    ...
}
```

Remember to add into the **`__init__.py`** the following imports as
needed. For example:
```python
...
from .hooks import pre_init_hook
from .hooks import post_init_hook
from .hooks import uninstall_hook
...
```

The complete tree should look like this:

```
addons/<my_module_name>/
|-- __init__.py
|-- __openerp__.py
|-- hooks.py
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
|-- tests/
|   |-- __init__.py
|   |-- <test_file>.py
|   |-- <test_file>.yml
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
|-- examples/
|   |-- my_example.csv
```

Filenames should use only `[a-z0-9_]`

Use correct file permissions: folders 755 and files 644.

## XML files

### Format

When declaring a record in XML:

* Place `id` attribute before `model`
* For field declarations, the `name` attribute is first. Then place the `value`
  either in the `field` tag, either in the `eval` attribute, and finally other
  attributes (widget, options, ...) ordered by importance.
* Try to group the records by model. In case of dependencies between
  action/menu/views, the convention may not be applicable.
* Use naming convention defined at the next point
* The tag `<data>` is only used to set not-updatable data with `noupdate=1`
* Do not prefix the xmlid by the current module's name
  (`<record id="view_id"...`, not `<record id="current_module.view_id"...`)


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

### Records

* For records of model `ir.filters` use explicit `user_id` field.

```xml
<record id="filter_id" model="ir.filters">
    <field name="name">Filter name</field>
    <field name="model_id">filter.model</field>
    <field name="user_id" eval="False"/>
</record>
```

More info [here](https://github.com/odoo/odoo/pull/8218)

### Naming xml_id

#### Security, View and Action

Use the following pattern:

* For a menu: `<model_name>_menu`
* For a view: `<model_name>_view_<view_type>`, where `view_type` is kanban,
  form, tree, search, ...
* For an action: the main action respects `<model_name>_action`. Others are
  suffixed with `_<detail>`, where `detail` is an underscore lowercase string
  explaining the action (should not be long). This is used only if
  multiple actions are declared for the model.
* For a group: `<model_name>_group_<group_name>` where `group_name` is the
  name of the group, generally 'user', 'manager', ...
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
name prevents xid conflicts. In the case where an inherited view has a name
which does not follow the guidelines set above, prefer naming the inherited
view after the original over using a name which follows the guidelines. This
eases looking up the original view and other inheritance if they all have the
same name.


```xml
<record id="original_id" model="ir.ui.view">
<field name="inherit_id" ref="original_module.original_id"/>
    ...
</record>
```


Use of `<... position="replace">` is not recommended because
could show the error `Element ... cannot be located in parent view`
from other inherited views with this field.

If you need to use this option, it must have an explicit comment
explaining why it is absolutely necessary and also use a
high value in its `priority` (greater than 100 is recommended) to avoid the error.


```xml
<record id="view_id" model="ir.ui.view">
    <field name="name">view.name</field>
    <field name="model">object_name</field>
    <field name="priority">110</field> <!--Priority greater than 100-->
    <field name="arch" type="xml">
        <!-- It is necessary because...-->
        <xpath expr="//field[@name='my_field_1']" position="replace"/>
    </field>
</record>
```

Also, we can hide an element from the view using `invisible="1"`.


### External dependencies

#### `__openerp__.py`
If your module uses extra dependencies of python or binaries you should add
the `external_dependencies` section to `__openerp__.py`.

```python
{
    'name': 'Example Module',
    ...
    'external_dependencies': {
        'bin': [
            'external_dependency_binary_1',
            'external_dependency_binary_2',
            ...
            'external_dependency_binary_N',
        ],
        'python': [
            'external_dependency_python_1',
            'external_dependency_python_2',
            ...
            'external_dependency_python_N',
        ],
    },
    ...
    'installable': True,
}
```

An entry in `bin` needs to be in `PATH`, check by running
`which external_dependency_binary_N`.

An entry in `python` needs to be in `PYTHONPATH`, check by running
`python -c "import external_dependency_python_N"`.

#### ImportError
In python files where you use external dependencies you will
need to add `try-except` with a debug log.

```python
try:
    import external_dependency_python_N
    import external_dependency_python_M
    EXTERNAL_DEPENDENCY_BINARY_N_PATH = tools.find_in_path('external_dependency_binary_N')
    EXTERNAL_DEPENDENCY_BINARY_M_PATH = tools.find_in_path('external_dependency_binary_M')
except (ImportError, IOError) as err:
    _logger.debug(err)
```
This rule doesn't apply to the test files since these files are loaded only when
running tests and in such a case your module and their external dependencies are installed.

#### README
If your module uses extra dependencies of python or binaries, please explain
how to install them in the `README.rst` file in the section `Installation`.


## Python

### PEP8 options

Using the linter flake8 can help to see syntax and semantic warnings or errors.
Project Source Code should adhere to PEP8 and PyFlakes standards with
a few exceptions:

* In `__init__.py` only
    *  F401: `module` imported but unused

### Imports

The imports are ordered as

1. Standard library imports
2. Known third party imports (One per line sorted and split in python stdlib)
3. Odoo imports (`openerp`)
4. Imports from Odoo modules (rarely, and only if necessary)
5. Local imports in the relative form
6. Unknown third party imports (One per line sorted and split in python stdlib)

Inside these 6 groups, the imported lines are alphabetically sorted.

```python
# 1: imports of python lib
import base64
import logging
import re
import time

# 2: import of known third party lib
import lxml

# 3:  imports of openerp
import openerp
from openerp import api, fields, models  # alphabetically ordered
from openerp.tools.safe_eval import safe_eval
from openerp.tools.translate import _

# 4:  imports from odoo modules
from openerp.addons.website.models.website import slug
from openerp.addons.web.controllers.main import login_redirect

# 5: local imports
from . import utils

# 6: Import of unknown third party lib
_logger = logging.getLogger(__name__)
try:
  import external_dependency_python_N
except ImportError:
  _logger.debug('Cannot `import external_dependency_python_N`.')
```

 * Note:
   * You can use [isort](https://pypi.python.org/pypi/isort/) to automatically
     sort imports.
   * Install with `pip install isort` and use with `isort myfile.py`.

### Idioms

* Each python file should have
  ``# coding: utf-8`` or ``# -*- coding: utf-8 -*-`` as first line
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
    * Too many comments are usually a sign that the code is unreadable and
      needs to be refactored
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
* Use English variable names and write comments in English. Strings which need
  to be displayed in other languages should be translated using the translation
  system
* Avoid use of ``api.v7`` decorator in new code, unless there is already an API
  fragmentation in parent methods.

### Symbols

#### Odoo Python Classes

Use UpperCamelCase for code in api v8, underscore lowercase notation for old
api.

```python
class AccountInvoice(models.Model):
    ...

class account_invoice(orm.Model):
    ...
```

#### Variable names
* Use underscore lowercase notation for common variables (snake_case)
* Since new API works with records or recordsets instead of id lists, don't
  suffix variable names with `_id` or `_ids` if they do not contain an ids or
  lists of ids.

```python
    ...
    res_partner = self.env['res.partner']
    partners = res_partner.browse(ids)
    partner_id = partners[0].id
```

* Use underscore uppercase notation for global variables or constants
```python
...
CONSTANT_VAR1 = 'Value'
...
class...
...
```

### SQL

#### No SQL Injection
Care must be taken not to introduce SQL injections vulnerabilities when using manual SQL queries. The vulnerability is present when user input is either incorrectly filtered or badly quoted, allowing an attacker to introduce undesirable clauses to a SQL query (such as circumventing filters or executing **UPDATE** or **DELETE** commands).

The best way to be safe is to never, NEVER use Python string concatenation (+) or string parameters interpolation (%) to pass variables to a SQL query string.

The second reason, which is almost as important, is that it is the job of the database abstraction layer (psycopg2) to decide how to format query parameters, not your job! For example psycopg2 knows that when you pass a list of values it needs to format them as a comma-separated list, enclosed in parentheses!

```python
# the following is very bad:
#   - it's a SQL injection vulnerability
#   - it's unreadable
#   - it's not your job to format the list of ids
cr.execute('select distinct child_id from account_account_consol_rel ' +
           'where parent_id in ('+','.join(map(str, ids))+')')

# better
cr.execute('SELECT DISTINCT child_id '\
           'FROM account_account_consol_rel '\
           'WHERE parent_id IN %s',
           (tuple(ids),))
```

This is very important, so please be careful also when refactoring, and most importantly do not copy these patterns!

Here is a [memorable example](http://www.bobby-tables.com) to help you remember what the issue is about (but do not copy the code there).

Before continuing, please be sure to read the online documentation of pyscopg2 to learn of to use it properly:

  - [The problem with query parameters](http://initd.org/psycopg/docs/usage.html#the-problem-with-the-query-parameters)
  - [How to pass parameters with psycopg2](http://initd.org/psycopg/docs/usage.html#passing-parameters-to-sql-queries)
  - [Advanced parameter types](http://initd.org/psycopg/docs/usage.html#adaptation-of-python-values-to-sql-types)

#### Never commit the transaction

The OpenERP/OpenObject framework is in charge of providing the transactional context for all RPC calls. The principle is that a new database cursor is opened at the beginning of each RPC call, and committed when the call has returned, just before transmitting the answer to the RPC client, approximately like this:

```python
def execute(self, db_name, uid, obj, method, *args, **kw):
    db, pool = pooler.get_db_and_pool(db_name)
    # create transaction cursor
    cr = db.cursor()
    try:
        res = pool.execute_cr(cr, uid, obj, method, *args, **kw)
        cr.commit() # all good, we commit
    except Exception:
        cr.rollback() # error, rollback everything atomically
        raise
    finally:
        cr.close() # always close cursor opened manually
    return res
```

If any error occurs during the execution of the RPC call, the transaction is rolled back atomically, preserving the state of the system.

Similarly, the system also provides a dedicated transaction during the execution of tests suites, so it can be rolled back or not depending on the server startup options.

The consequence is that if you manually call `cr.commit()` anywhere there is a very high chance that you will break the system in various ways, because you will cause partial commits, and thus partial and unclean rollbacks, causing among others:

 - inconsistent business data, usually data loss ;
 - workflow desynchronization, documents stuck permanently ;
 - tests that can't be rolled back cleanly, and will start polluting the database, and triggering error (this is true even if no error occurs during the transaction);

Unless:

 - You have created your own database cursor explicitly! And the situations where you need to do that are exceptional!
   And by the way if you did create your own cursor, then you need to handle error cases and proper rollback, as well as properly close the cursor when you're done with it.

   And contrary to popular belief, you do not even need to call `cr.commit()` in the following situations:

   - in the `_auto_init()` method of an `models.Model` object: this is taken care of by the addons initialization method, or by the ORM transaction when creating custom models
   - in reports: the `commit()` is handled by the framework too, so you can update the database even from within a report
   - within `models.TransientModel` methods: these methods are called exactly like regular `models.Model` ones, within a transaction and with the corresponding `cr.commit()`/`rollback()` at the end ;
   - etc. (see general rule above if you have in doubt!)

 - All `cr.commit()` calls outside of the server framework from now on must have an explicit comment explaining why they are absolutely necessary, why they are indeed correct, and why they do not break the transactions. Otherwise they can and will be removed!

 - You can avoid the `cr.commit` using `cr.savepoint` method.

  ```python
    try:
        with cr.savepoint():
            # Create a savepoint and rollback this section if any exception is raised.
            method1()
            method2()
    # Catch here any exceptions if you need to.
    except (except_class1, except_class2):
        # Add here the logic if anything fails. NOTE: Don't need rollback sentence.
        pass

  ```

 - You can isolate a transaction for a valid `cr.commit` using `Environment`:

  ```python
    with openerp.api.Environment.manage():
        with openerp.registry(self.env.cr.dbname).cursor() as new_cr:
            # Create a new environment with new cursor database
            new_env = api.Environment(new_cr, self.env.uid, self.env.context)
            # with_env replace original env for this method
            self.with_env(new_env).write({'name': 'hello'})  # isolated transaction to commit
            new_env.cr.commit()  # Don't show a invalid-commit in this case
        # You don't need close your cr because is closed when finish "with"
    # You don't need clear caches because is cleared when finish "with"
  ```


### Do not bypass the ORM

You should never use the database cursor directly when the ORM can do the same thing! By doing so you are bypassing all the ORM features, possibly the transactions, access rights and so on.

And chances are that you are also making the code harder to read and probably less secure (see also next guideline):

```python
# very very wrong
cr.execute('select id from auction_lots where auction_id in (' +
           ','.join(map(str, ids)) + ') and state=%s and obj_price>0',
           ('draft',))
auction_lots_ids = [x[0] for x in cr.fetchall()]

# no injection, but still wrong
cr.execute('select id from auction_lots where auction_id in %s '
           'and state=%s and obj_price>0',
           (tuple(ids), 'draft',))
auction_lots_ids = [x[0] for x in cr.fetchall()]

# better
auction_lots_ids = self.search(cr, uid, [
    ('auction_id', 'in', ids),
    ('state', '=', 'draft'),
    ('obj_price', '>', 0),
])
```

### Models
* Model names
    * Use dot lowercase name for models. Example: `sale.order`
    * Use name in a singular form. `sale.order` instead of `sale.orders`
* Method conventions
    * Compute Field: the compute method pattern is `_compute_<field_name>`
    * Inverse method: the inverse method pattern is `_inverse_<field_name>`
    * Search method: the search method pattern is `_search_<field_name>`
    * Default method: the default method pattern is `_default_<field_name>`
    * Onchange method: the onchange method pattern is `_onchange_<field_name>`
    * Constraint method: the constraint method pattern is
      `_check_<constraint_name>`
    * Action method: an object action method is prefix with `action_`.
      Its decorator is `@api.multi`, but since it use only one record, add
      `self.ensure_one()` at the beginning of the method.
    * `@api.one` method: For v8 is recommended use `@api.multi` and avoid use
      `@api.one`, for compatibility with v9 where is deprecated `@api.one`.
* In a Model attribute order should be
    1. Private attributes (`_name`, `_description`, `_inherit`, ...)
    2. Default method and `_default_get`
    3. Fields declarations
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

    # Default methods
    def _default_name(self):
            ...

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


### Fields
* `One2Many` and `Many2Many` fields should always have `_ids` as suffix
  (example: sale_order_line_ids)
* `Many2One` fields should have `_id` as suffix
  (example: partner_id, user_id, ...)
* If the technical name of the field (the variable name) is the same to the
  string of the label, don't put `string` parameter for new API fields, because
  it's automatically taken. If your variable name contains "_" in the name,
  they are converted to spaces when creating the automatic string and each word
  is capitalized.
  (example: old api `'name': fields.char('Name', ...)`
            new api `'name': fields.Char(...)`)
* Default functions should be declared with a lambda call on self. The reason
  for this is so a default function can be inherited. Assigning a function
  pointer directly to the `default` parameter does not allow for inheritance.

  ```python
  a_field(..., default=lambda self: self._default_get())
  ```

## Javascript

* `use strict;` is recommended for all javascript files
* Use a linter (jshint, ...)
* Never add minified Javascript libraries
* Use UpperCamelCase for class declarations

## CSS

* Prefix all your classes with `o_<module_name>` where `module_name` is the
  technical name of the module (`sale`, `im_chat`, ...) or the main route
  reserved by the module (for website module mainly,
  i.e. `o_forum` for website_forum module). The only exception for this rule is
  the webclient: it simply use `o_` prefix.
* Avoid using ids
* Use bootstrap native classes
* Use underscore lowercase notation to name classes

## Tests

As a general rule, a bug fix should come with a unittest which would fail
without the fix itself. This is to assure that regression will not happen in
the future. It also is a good way to show that the fix works in all cases.

New modules or additions should ideally test all the functions defined. The
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
* Always put meaningful commit messages: commit messages should be
  self explanatory (long enough) including the name of the module that
  has been changed and the reason behind that change. Do not use
  single words like "bugfix" or "improvements".
* Avoid commits which simultaneously impact lots of modules. Try to
  split into different commits where impacted modules are different.
  This is helpful if we need to revert changes on a module separately.
* Only make a single commit per logical change set. Do not add commits such as
  "Fix pep8", "Code review" or "Add unittest" if they fix commits which are
   being proposed
* Use present imperative (Fix formatting, Remove unused field) avoid appending
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
to rely on the other developers. The peer review in this project will be
managed through Pull Requests. It will serve the following main purposes:

* Having a second look on a code snippet to avoid unintended problems / bugs
* Avoid technical or business design flaws
* Allow the coordination and convergence of the developers by informing the
  community of what has been done
* Allow the responsibles to look at every devs and keep the interested people
  informed of what has been done
* Prevent addon incompatibilities when/if possible
* The rationale for peer review has its equivalent in Linus's law, often
  phrased: "Given enough eyeballs, all bugs are shallow"

Meaning "If there are enough reviewers, all problems are easy to solve". Eric
S. Raymond has written influentially about peer review in software development:
 http://en.wikipedia.org/wiki/Software_peer_review.

#### Please respect a few basic rules:

* Two reviewers must approve a merge proposal in order to be able to merge it
* 5 calendar days must be given to be able to merge it
* A PR can be merged in less than 5 calendar days if and only if it is approved
  by 3 reviewers. If you are in a hurry just send a mail at
  contributors@odoo-community.org or ask by IRC (FreeNode
  oca, openobject channel).
* At least one of the review above must be from a member of the PSC or having
  write access on the repository (here one of the
  [OCA Core Maintainers](https://odoo-community.org/project/core-maintainers-55)
  can do the job. You can notify them on Github using '@OCA/core-maintainers')
* Is the module generic enough to be part of community addons?
* Is the module duplicating features with other community addons?
* Does the documentation allow to understand what it does and how to use it?
* Is the problem it tries to resolve adressed the good way, using good
  concepts?
* Are there some use cases?
* Is there any setup in code? Should not!
* Are there demo data?

Further reading:
* https://insidecoding.wordpress.com/2013/01/07/code-review-guidelines/

#### There are the following important parts in a review:

* Start by thanking the contributor / developer for their work. No matter the
  issue of the PR, someone has done work for you, so be thankful for that.
* Be cordial and polite. Nothing is obvious in a PR.
* The description of the changes should be clear enough for you to understand
  their purpose and, if applicable, contain a demo in order to
  allow people to run and test the code
* Choose the review tag (comment, approve, rejected, needs information,...)
  and don't forget to add a type of review to let people know:
  * Code review: means you look at the code
  * Test: means you tested it functionally speaking

While making the merge, please respect the author using the `--author` option
when committing. The author is found using the git log command. Use the commit
message provided by the contributor if any.

#### It makes sense to be picky in the following cases:

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

Pull requests can be closed if:

* there is no activity for 6 months

## Github

### Teams

* Team name must not contain odoo or openerp
* Team name for localization is "Belgium Maintainers" for Belgium

### Repositories

#### Naming

* Project name must not contain odoo or openerp
* Project name for localization is "l10n-belgium" for Belgium
* Project name for connectors is "connector-magento" for Magento connector

#### Branch configuration
Python packages to install, must be preferably, define in requirements.txt than travis.yml file. 
Requirements.txt avoid to repeat packages in all travis.yml files of repositories in case of using with oca_dependencies.txt file.

### Issues

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
    * Add guideline to use external dependencies
    * Define a separated file for installation hooks
* [XML](#xml-files)
    * Avoid use current module in xml_id
    * Use explicit `user_id` field for records of model `ir.filters`
* [Python](#python)
    * Use Python standards
    * Fuller PEP8 compliance
    * Use ``# coding: utf-8`` or ``# -*- coding: utf-8 -*-`` in first line
    * Using relative import for local files
    * More python idioms
    * A way to deal with long comma-separated lines
    * Hints on documentation
    * Don't use CamelCase for model variables
    * Use underscore uppercase notation for global variables or constants
* [SQL](#sql)
    * Add section for No SQL Injection
    * Add section for don't bypass the ORM
    * Add section for never commit the transaction
* [Field](#field)
    * A hint for function defaults
    * Use default label string if is possible
    * Add the inverse method pattern
* [Tests Section Added](#tests)
* [Git](#git)
    * No prefixing of commits
    * Default git commit message standards
    * Squashing changes in pull requests when necessary
    * Use of present imperative
* [Github Section](#github)
* [Review Section](#review)

# Backporting Odoo Modules

Suggesting a backport of a module among an OCA repository is possible, but you
must respect a few rules:

 * You need to keep the license of the module coded by Odoo SA
 * You need to add the OCA as author (and Odoo SA of course)
 * You need to make the module "OCA compatible" : PEP8, OCA convention and so
   on so it won't break our CI like runbot, Travis and so.
 * You need to add a disclaimer in the Readme with the following text:
```
**This module is a backport from Odoo SA and as such, it is not included in the OCA CLA. That means we do not have a copy of the copyright on it like all other OCA modules.**
```
