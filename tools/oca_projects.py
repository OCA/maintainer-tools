# -*- coding: utf-8 -*-
"""
Data about OCA Projects, with a few helper functions.

OCA_PROJECTS: dictionary of OCA Projects mapped to the list of related
repository names, based on
https://odoo-community.org/page/List

OCA_REPOSITORY_NAMES: list of OCA repository names

"""
from __future__ import print_function
from contextlib import contextmanager
import os
import shutil
import subprocess
import tempfile

import appdirs
from github_login import login

ALL = ['OCA_PROJECTS', 'OCA_REPOSITORY_NAMES', 'url']

OCA_PROJECTS = {
    'accounting': ['account-analytic',
                   'account-budgeting',
                   'account-closing',
                   'account-consolidation',
                   'account-financial-tools',
                   'account-financial-reporting',
                   'account-invoice-reporting',
                   'account-invoicing',
                   'account-fiscal-rule',
                   'operating-unit',
                   'intrastat',
                   'mis-builder',
                   'currency',
                   'credit-control',
                   ],
    # 'backport': ['OCB',
    #              ],
    'Apps Store': ['apps-store'],

    'banking': ['bank-payment',
                'account-reconcile',
                'bank-statement-import',
                'account-payment',
                ],
    'community': ['maintainer-tools',
                  'maintainer-quality-tools',
                  'runbot-addons',
                  ],
    'connector': ['connector',
                  'connector-ecommerce',
                  'queue',
                  ],
    'connector AccountEdge': ['connector-accountedge'],
    'connector CMIS': ['connector-cmis'],
    'connector Infor': ['connector-infor'],
    'connector Lengow': ['connector-lengow'],
    'connector LIMS': ['connector-lims'],
    'connector Magento': ['connector-magento'],
    'connector Prestashop': ['connector-prestashop'],
    'connector Sage': ['connector-sage'],
    'connector Salesforce': ['connector-salesforce'],
    'connector WooCommerce': ['connector-woocommerce'],
    'crm sales marketing': ['sale-workflow',
                            'crm',
                            'partner-contact',
                            'sale-financial',
                            'sale-reporting',
                            'commission',
                            'event',
                            'survey',
                            ],
    'document': ['knowledge'],
    'ecommerce': ['e-commerce'],
    'edi': ['edi'],
    'financial control': ['margin-analysis'],
    'Infrastructure': ['infrastructure-dns'],
    'geospatial': ['geospatial'],
    'hr': ['hr-timesheet',
           'hr',
           'department',
           ],
    'connector-odoo2odoo': ['connector-odoo2odoo'],
    'multi-company': ['multi-company'],
    'l10n-argentina': ['l10n-argentina'],
    'l10n-belgium': ['l10n-belgium'],
    'l10n-brazil': ['l10n-brazil'],
    'l10n-cambodia': ['l10n-cambodia'],
    'l10n-canada': ['l10n-canada'],
    'l10n-chile': ['l10n-chile'],
    'l10n-china': ['l10n-china'],
    'l10n-colombia': ['l10n-colombia'],
    'l10n-costa-rica': ['l10n-costa-rica'],
    'l10n-croatia': ['l10n-croatia'],
    'l10n-ecuador': ['l10n-ecuador'],
    'l10n-ethiopia': ['l10n-ethiopia'],
    'l10n-finland': ['l10n-finland'],
    'l10n-france': ['l10n-france'],
    'l10n-germany': ['l10n-germany'],
    'l10n-india': ['l10n-india'],
    'l10n-indonesia': ['l10n-indonesia'],
    'l10n-iran': ['l10n-iran'],
    'l10n-ireland': ['l10n-ireland'],
    'l10n-italy': ['l10n-italy'],
    'l10n-japan': ['l10n-japan'],
    'l10n-luxemburg': ['l10n-luxemburg'],
    'l10n-mexico': ['l10n-mexico'],
    'l10n-morocco': ['l10n-morocco'],
    'l10n-netherlands': ['l10n-netherlands'],
    'l10n-norway': ['l10n-norway'],
    'l10n-peru': ['l10n-peru'],
    'l10n-portugal': ['l10n-portugal'],
    'l10n-romania': ['l10n-romania'],
    'l10n-slovenia': ['l10n-slovenia'],
    'l10n-spain': ['l10n-spain'],
    'l10n-switzerland': ['l10n-switzerland'],
    'l10n-taiwan': ['l10n-taiwan'],
    'l10n-thailand': ['l10n-thailand'],
    'l10n-turkey': ['l10n-turkey'],
    'l10n-usa': ['l10n-usa'],
    'l10n-united-kingdom': ['l10n-united-kingdom'],
    'l10n-venezuela': ['l10n-venezuela'],
    'l10n-vietnam': ['l10n-vietnam'],
    'logistics': ['carrier-delivery',
                  'stock-logistics-barcode',
                  'stock-logistics-workflow',
                  'stock-logistics-tracking',
                  'stock-logistics-warehouse',
                  'stock-logistics-reporting',
                  'rma',
                  'ddmrp',
                  ],
    'manufacturing': ['manufacture',
                      'manufacture-reporting',
                      ],
    'management system': ['management-system'],
    'purchase': ['purchase-workflow',
                 'purchase-reporting',
                 ],
    'product': ['product-attribute',
                'product-kitting',
                'product-variant',
                ],
    'project / services': ['project-reporting',
                           'project-service',
                           'project-agile',
                           'contract',
                           'program',
                           'business-requirement',
                           'connector-redmine',
                           'connector-jira',
                           ],
    'social': ['social'],
    'tools': ['reporting-engine',
              'report-print-send',
              'webkit-tools',
              'server-tools',
              'server-auth',
              'server-env',
              'server-backend',
              'server-brand',
              'server-ux',
              'community-data-files',
              'webhook',
              'interface-github',
              ],
    'vertical association': ['vertical-association'],
    'vertical hotel': ['vertical-hotel'],
    'vertical ISP': ['vertical-isp'],
    'vertical edition': ['vertical-edition'],
    'vertical education': ['vertical-education'],
    'vertical medical': ['vertical-medical'],
    'vertical NGO': ['vertical-ngo',
                     # XXX
                     ],
    'vertical construction': ['vertical-construction'],
    'vertical real state': ['vertical-realstate'],
    'vertical travel': ['vertical-travel'],
    'web': ['web'],
    'website': ['website',
                'website-cms',
                ],
}


NOT_ADDONS = {
    'odoo-community.org',
    'contribute-md-template',
    'maintainer-tools',
    'maintainer-quality-tools',
    'odoo-sphinx-autodoc',
    'openupgradelib',
    'connector-magento-php-extension',
    'OCB',
    'OpenUpgrade',
    'pylint-odoo',
    'oca-custom',
}


BRANCHES = (
    '6.1',
    '7.0',
    '8.0',
    '9.0',
    '10.0',
    '11.0',
)


def get_repositories():
    gh = login()
    all_repos = [repo.name for repo in gh.iter_user_repos('OCA')
                 if repo.name not in NOT_ADDONS]
    return all_repos


def get_repositories_and_branches(branches=BRANCHES):
    gh = login()
    for repo in gh.iter_user_repos('OCA'):
        if repo.name in NOT_ADDONS:
            continue
        for branch in repo.iter_branches():
            if branches and branch.name not in branches:
                continue
            yield repo.name, branch.name


try:
    OCA_REPOSITORY_NAMES = get_repositories()
except Exception as exc:
    print(exc)
    OCA_REPOSITORY_NAMES = []
    for repos in OCA_PROJECTS.itervalues():
        OCA_REPOSITORY_NAMES += repos

OCA_REPOSITORY_NAMES.sort()

_OCA_REPOSITORY_NAMES = set(OCA_REPOSITORY_NAMES)

_URL_MAPPINGS = {'git': 'git@github.com:%s/%s.git',
                 'https': 'https://github.com/%s/%s.git',
                 }


def url(project_name, protocol='git', org_name='OCA'):
    """get the URL for an OCA project repository"""
    if project_name not in _OCA_REPOSITORY_NAMES:
        raise ValueError('Unknown project', project_name)
    return _URL_MAPPINGS[protocol] % (org_name, project_name)


class BranchNotFoundError(RuntimeError):
    pass


@contextmanager
def temporary_clone(project_name, branch, protocol='git', org_name='OCA'):
    """ context manager that clones a git branch and cd to it, with cache """
    # init cache directory
    cache_dir = appdirs.user_cache_dir('oca-mqt')
    repo_cache_dir = os.path.join(
        cache_dir, 'github.com', org_name.lower(), project_name.lower())
    if not os.path.isdir(repo_cache_dir):
        os.makedirs(repo_cache_dir)
        subprocess.check_call(['git', 'init', '--bare'], cwd=repo_cache_dir)
    repo_url = url(project_name, protocol, org_name)
    # fetch all branches into cache
    fetch_cmd = [
        'git', 'fetch', '--quiet',
        repo_url,
        'refs/heads/*:refs/heads/*',
    ]
    subprocess.check_call(fetch_cmd, cwd=repo_cache_dir)
    # check if branch exist
    branches = subprocess.check_output(
        ['git', 'branch'], universal_newlines=True, cwd=repo_cache_dir)
    branches = [b.strip() for b in branches.split()]
    if branch not in branches:
        raise BranchNotFoundError()
    # clone to temp dir, with --reference to cache
    tempdir = tempfile.mkdtemp()
    try:
        clone_cmd = [
            'git', 'clone', '--quiet',
            '--reference', repo_cache_dir,
            '--branch', branch,
            '--',
            repo_url,
            tempdir,
        ]
        subprocess.check_call(clone_cmd)
        cwd = os.getcwd()
        os.chdir(tempdir)
        try:
            yield
        finally:
            os.chdir(cwd)
    finally:
        shutil.rmtree(tempdir)
