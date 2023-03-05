import logging
import sys

from . import github_login
from .config import read_config

_logger = logging.getLogger("clabot-hook")


def setup_logging():
    logging.basicConfig(level=logging.WARNING)


class ClabotHookSetter(object):
    def __init__(self):
        config = read_config()
        self.gh_token = config.get("GitHub", "token")
        self.gh = github_login.login()
        self.gh_org = "OCA"
        self.clabot_secret = config.get("Clabot", "secret")
        if not self.clabot_secret:
            sys.exit("Please configure the Clabot secret in oca.ini")

    def _get_repositories(self):
        for repo in self.gh.repositories_by(self.gh_org):
            yield repo

    def create_or_update_clabot_hook(self):
        projects = self._get_repositories()

        for project in projects:
            self._check_clabot_hook(project)

    def _check_clabot_hook(self, repo):
        hooks = repo.hooks()
        for hook in hooks:
            if hook.config.get("url") == "http://runbot.odoo-community.org:1337":
                _logger.warning("found old clabot hook for %s", repo.name)
                config = dict(hook.config)
                config["url"] = "http://clabot.odoo-community.org:1337"
                hook.edit(config=config)
                _logger.warning("updated old clabot hook for %s", repo.name)
                return hook
            elif hook.config.get("url") == "http://clabot.odoo-community.org:1337":
                _logger.info("found clabot hook for %s", repo.name)
                return hook
        else:
            _logger.warning("Create clabot hook for %s", repo.name)
            hook = repo.create_hook(
                name="web",
                config=self._get_clabot_hook_config(repo),
                events=self._get_clabot_hook_events(repo),
            )
            return hook

    def _get_clabot_hook_config(self, repo):
        return {
            "content_type": "json",
            "insecure_ssl": "0",
            "secret": self.clabot_secret,
            "url": "http://clabot.odoo-community.org:1337",
        }

    def _get_clabot_hook_events(self, repo):
        return ["pull_request"]


if __name__ == "__main__":
    setup_logging()
    setter = ClabotHookSetter()
    setter.create_or_update_clabot_hook()
