# -*- coding: utf-8 -*-
"""
Data about OCA Projects, with a few helper functions.

OCA_PROJECTS: dictionary of OCA Projects mapped to the list of related
repository names, based on
https://community.odoo.com/page/website.projects_index

OCA_REPOSITORY_NAMES: list of OCA repository names

"""

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
                   ],
    # 'backport': ['OCB',
    #              ],
    'banking': ['bank-payment',
                'bank-statement-reconcile',
                'bank-statement-import',
                'account-payment',
                ],
    'community': ['maintainer-tools',
                  'maintainer-quality-tools',
                  'runbot-addons',
                  ],
    'connector': ['connector',
                  'connector-ecommerce',
                  ],
    'account edge connector': ['connector-accountedge'],
    'connector LIMS': ['connector-lims'],
    'connector CMIS': ['connector-cmis'],
    'connector magento': ['connector-magento'],
    'connector prestashop': ['connector-prestashop'],
    'connector sage': ['connector-sage-50'],
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
    'financial control': ['margin-analysis'],
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
    'l10n-canada': ['l10n-canada'],
    'l10n-china': ['l10n-china'],
    'l10n-colombia': ['l10n-colombia'],
    'l10n-costa-rica': ['l10n-costa-rica'],
    'l10n-finland': ['l10n-finland'],
    'l10n-france': ['l10n-france'],
    'l10n-germany': ['l10n-germany'],
    'l10n-india': ['l10n-india'],
    'l10n-iran': ['l10n-iran'],
    'l10n-ireland': ['l10n-ireland'],
    'l10n-italy': ['l10n-italy'],
    'l10n-luxemburg': ['l10n-luxemburg'],
    'l10n-mexico': ['l10n-mexico'],
    'l10n-netherlands': ['l10n-netherlands'],
    'l10n-norway': ['l10n-norway'],
    'l10n-portugal': ['l10n-portugal'],
    'l10n-romania': ['l10n-romania'],
    'l10n-spain': ['l10n-spain'],
    'l10n-switzerland': ['l10n-switzerland'],
    'l10n-taiwan': ['l10n-taiwan'],
    'l10n-usa': ['l10n-usa'],
    'l10n-united-kingdom': ['l10n-united-kingdom'],
    'l10n-venezuela': ['l10n-venezuela'],
    'logistics': ['carrier-delivery',
                  'stock-logistics-barcode',
                  'stock-logistics-workflow',
                  'stock-logistics-tracking',
                  'stock-logistics-warehouse',
                  'stock-logistics-reporting',
                  'rma',
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
                           'contract',
                           'program',
                           ],
    'tools': ['reporting-engine',
              'report-print-send',
              'webkit-tools',
              'server-tools',
              'community-data-files',
              ],
    'vertical association': ['vertical-association'],
    'vertical hotel': ['vertical-hotel'],
    'vertical ISP': ['vertical-isp'],
    'vertical edition': ['vertical-edition'],
    'vertical medical': ['vertical-medical'],
    'vertical NGO': ['vertical-ngo',
                     # XXX
                     ],
    'vertical construction': ['vertical-construction'],
    'vertical travel': ['vertical-travel'],
    'web': ['web'],
    }


def get_repositories():
    ignored = set([
        'odoo-community.org',
        'community-data-files',
        'contribute-md-template',
        'website',
        ])
    gh = login()
    all_repos = [repo.name for repo in gh.iter_user_repos('OCA')
                 if repo not in ignored]
    return all_repos

try:
    OCA_REPOSITORY_NAMES = get_repositories()
except Exception as exc:
    print exc
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
