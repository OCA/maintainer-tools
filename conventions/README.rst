Team
====

* Team name must not contain odoo or openerp
* Team name for localization is "Belgium Maintainers" for Belgium

Project / Repository
====================

* Project name must not contain odoo or openerp
* Project name for localization is "l10n_Belgium" for Belgium
* Project name for connectors is "connector-magento" for Magento connector

Branch
======


Module
======

* Prefer the use of the singular form in module name (or use 'multi')
* Use the description template (rst or html) provided on http://github.com/oca/maintainer-tools

Python Code
===========

* Follow Python PEP 8: https://www.python.org/dev/peps/pep-0008/ 
* Do not use deprecated features

XML Code
========

JS Code
=======

Menu
====

Reporting
=========

Translation
===========

Security
========

Tests
=====

Demo data
=========

Migration
=========

Issue
=====

* Issues are used for blueprints and bugs.

Commit
======

* Write a helpful commit message
* Use a commit tag in each message. This tag should be one of:

  * [IMP] for improvements
  * [FIX] to fix bugs
  * [REF] to refactor (improvements of the source code, without changing the functionality or behavior. See http://en.wikipedia.org/wiki/Refactoring for further details)
  * [ADD] to add new resources
  * [REM] to remove resources

Always put a meaningful commit message. Commit message should be self explanatory including the name of the module that has been changed. No more "bugfix" or "improvements" anymore! (the only single word commit message accepted is "merge")

e.g:

 Not Correct : git commit -m “[FIX]: reverted bad revision (cannot install new db)
 with revision number:525425”

 Correct : git commit -m “[FIX]: reverted bad revision (cannot install new db)
 with revision number id: qdp@tinyerp.com-20090602143202-ehmntlift166mrnn”

 Not Correct : git commit -m "Issue 568889 : typo corrected"

 Correct : git commit -m "[FIX] fixes #568889 - account module: typo corrected"

Note

 How to handle translations ?
 use [IMP] if you translated a message in a po file
 use [ADD] if you added an new po file

Avoid big commits
Don't make a commit that will impact lots of modules. Try to split it into different commits where impacted modules are different (It will be helpful when we are going to revert that module separately).

Pull request
============

Review
======

Peer review is the only way to ensure good quality of the code and to be able to rely on the others devs. The peer review in this project will be made by making Merge Proposal. It will serve the following main purposes:

* Having a second look on his work to avoid unintended problems / bugs
* Avoid technical or business design flaws
* Allow the coordination and convergence of the devs by informing community of what has been done
* Allow the responsibles to look at every devs and keep the interested people informed of what has been done
* Prevent addons incompatibilities when/if possible
* The rationale for peer review has its equivalent in Linus's law, often phrased: "Given enough eyeballs, all bugs are shallow"

Meaning "If there are enough reviewers, all problems are easy to solve". Eric S. Raymond has written influentially about peer review in software development: http://en.wikipedia.org/wiki/Software_peer_review.

Please respect a few basic rules:

* Two reviewers must approve a merge proposal in order to be able to merge it
* 5 calendar days must be given to be able to merge it
* A MP can be merged in less that 5 calendar days if and only if it is approved by 3 reviewers. If you are in a hurry just send a mail at openerp-community-reviewer@lists.launchpad.net or ask by IRC (FreeNode server, openobject channel).
* Is the module generic enough to be part of community addons?
* Is the module duplicating features with other community addons?
* Does the documentation allow to understand what it does and how to use it?
* Is the problem it tries to resolve adressed the good way, using good concepts?
* Are there some use cases?
* Is there any setup in code? Should not!
* Are there demo data?

Most reference can be found here: http://insidecoding.com/2013/01/07/code-review-guidelines/

There are the following important part in a review:

* Start by thanking the contributor / developer for his work. No matter the issue of the MP, someone make work for you here, so be thankful for that.
* Be cordial and polite. Nothing is obvious in a MP.
* The description of the changes should be clear enough for you to understand his purpose and if apply, contain the reference feature instance in order to allow people to run and test the review
* Choose the review tag (comment, approve, rejected, needs information,...) and don't forget to add a type of review to let people know:

  * Code review: means you look at the code
  * Test: means you tested it functionally speaking

While making the merge, please respect the author using the “--author” option when committing. The author is found using the bzr log command. Use the commit message provided by the contributor if any.

It makes sense to be picky in the following cases:

* The origin/reason for the patch/dev is not documented very well
* No adapted / convenient description written in the __openerp__.py file for the module
* Tests or scenario are not all green and/or not adapted
* Having tests is very much encouraged
* Issues with license, copyright, authorship
* Respect of Odoo/community conventions
* Code design and best practices
