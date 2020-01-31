# License AGPLv3 (http://www.gnu.org/licenses/agpl-3.0-standalone.html)
import os
import setuptools


here = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(here, 'README.md')) as f:
    long_description = f.read()


setuptools.setup(
    name='oca-maintainers-tools',
    author='Odoo Community Association (OCA)',
    description='Set of tools to help managing Odoo Community projects',
    long_description=long_description,
    license='APGL3',
    packages=['tools'],
    include_package_data=True,
    use_scm_version=True,
    setup_requires=[
        'setuptools_scm',
    ],
    install_requires=[
        'appdirs',
        'argparse',
        'autopep8',
        'click',
        'configparser',  # for python2 compat
        # We need to pin docutils version, see
        # https://github.com/OCA/maintainer-tools/issues/423
        # Consider carefully before changing this.
        'docutils>=0.15.1,<0.15.1.1',
        'ERPpeek',
        'github3.py>=1',
        'inflection',
        'jinja2',
        'PyYAML',
        'polib',
        'pygments',
        'requests',
        'twine',
        'wheel',
    ],
    python_requires='>=2.7, !=3.0.*, !=3.1.*, !=3.2.*, !=3.3.*, !=3.4.*',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Console',
        'Intended Audience :: Developers',
        'Intended Audience :: Information Technology',
        'License :: OSI Approved :: '
        'GNU Affero General Public License v3 or later (AGPLv3+)',
        'Operating System :: POSIX :: Linux',
        'Programming Language :: Python',
    ],
    entry_points={
        'console_scripts': [
            'oca-github-login = tools.github_login:main',
            'oca-copy-maintainers = tools.copy_maintainers:main',
            'oca-clone-everything = tools.clone_everything:main',
            'oca-set-repo-labels = tools.set_repo_labels:main',
            'oca-odoo-login = tools.odoo_login:main',
            'oca-sync-users = tools.oca_sync_users:main',
            'oca-autopep8 = tools.autopep8_extended:main',
            'oca-gen-addons-table = tools.gen_addons_table:gen_addons_table',
            'oca-massive-change = tools.massive_change:main',
            'oca-migrate-branch = tools.migrate_branch:main',
            'oca-migrate-branch-empty = tools.migrate_branch_empty:main',
            'oca-pypi-upload = tools.pypi_upload:cli',
            'oca-gen-addon-readme = tools.gen_addon_readme:gen_addon_readme',
            'oca-gen-addon-icon = tools.gen_addon_icon:gen_addon_icon',
        ],
    },
)
