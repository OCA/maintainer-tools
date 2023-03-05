# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
import click
import requests


OCA_TRAVIS_GITHUB_USER = "oca-travis"
OCA_TRAVIS_GITHUB_EMAIL = "oca+oca-travis@odoo-community.org"


class Travis(object):
    def __init__(self, travis_token):
        self.api_url = "https://api.travis-ci.com"
        self.headers = {
            "Travis-API-Version": "3",
            "Authorization": "token " + travis_token,
        }
        self.count = 0

    def request(self, method, url, json=None):
        self.count += 1
        r = requests.request(
            method,
            self.api_url + url,
            headers=self.headers,
            json=json,
        )
        if not r.ok:
            print("travis error:", r.text)
        r.raise_for_status()
        return r.json()

    def get(self, url):
        return self.request("GET", url)

    def post(self, url, json):
        return self.request("POST", url, json=json)

    def delete(self, url):
        return self.request("DELETE", url)

    def patch(self, url, json):
        return self.request("PATCH", url, json=json)

    def set_env_vars(self, org, repo, vars):
        repo_slug = f"{org}%2F{repo}"
        existing_vars = self.get(f"/repo/github/{repo_slug}/env_vars")
        existing_vars_by_name = {v["name"]: v for v in existing_vars["env_vars"]}
        for var_name, var_value in vars.items():
            json = {
                "env_var.name": var_name,
                "env_var.value": var_value,
                "env_var.public": False,
            }
            if var_name in existing_vars_by_name:
                print(f"Updating {var_name} in {repo}")
                var_id = existing_vars_by_name[var_name]["id"]
                self.patch(f"/repo/github/{repo_slug}/env_var/{var_id}", json)
            else:
                print(f"Creating {var_name} in {repo}")
                self.post(f"/repo/github/{repo_slug}/env_vars", json)


@click.command()
@click.option(
    "--travis-token",
    required=True,
    envvar="TRAVIS_TOKEN",
    help="Find your travis token at " "https://travis-ci.com/account/preferences",
)
@click.option("--repo", help="repo name (default=all)")
@click.option(
    "--oca-travis-github-token",
    required=True,
    prompt="oca-travis github token (from OCA Board keepass file)",
    help="Find this in the OCA Board keepass.",
)
def main(repo, oca_travis_github_token, travis_token):
    """Configure Travis for OCA on one or all projects."""
    if repo:
        repos = [repo]
    else:
        from .oca_projects import get_repositories

        repos = get_repositories()
    travis = Travis(travis_token)
    for repo in repos:
        print("Configuring travis for", repo)
        travis.set_env_vars(
            "OCA",
            repo,
            {
                "GITHUB_USER": OCA_TRAVIS_GITHUB_USER,
                "GITHUB_EMAIL": OCA_TRAVIS_GITHUB_EMAIL,
                "GITHUB_TOKEN": oca_travis_github_token,
            },
        )
