# -*- coding: utf-8 -*-
# Copyright <YEAR(S)> <AUTHOR(S)>
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
try:
    from . import models
    from . import wizards
    from . import controllers
    from . import report
    from .hooks import pre_init_hook, post_load, post_init_hook, uninstall_hook
except ImportError:
    import logging
    _logger = logging.getLogger(__name__)
    _logger.info("ImportError raised while loading module.")
    _logger.debug("ImportError details:", exc_info=True)
