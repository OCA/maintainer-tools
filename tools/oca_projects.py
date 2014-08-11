# -*- coding: utf-8 -*-
"""
Data about OCA Projects, with a few helper functions.

OCA_PROJECTS: dictionary of OCA Projects mapped to the list of related repository names
OCA_REPOSITORY_NAMES: list of OCA repository names

"""

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
    ## 'backport': ['OCB',
    ##              ],
    'banking': ['banking',
                'bank-statement-reconcile',
                'account-payment',
                ],
    'community':['maintainers-tools',
                 'maintainer-quality-tools',
                 'runbot-addons',
                 ],
    'connector': ['connector',
                  'connector-ecommerce',
                  ],
    'account edge connector': ['connector-accountedge'],
    'connector lims': ['connector-lims'],
    'connector magento': ['connector-magento'],
    'connector prestashop': ['connector-prestashop'],
    'connector sage': ['connector-sage-50'],
    'crm sales': ['sale-workflow',
                  'crm',
                  'partner-contact',
                  'sale-financial',
                  'sale-reporting',
                  'commission',
                  ],
    'document': ['knowledge'],
    'ecommerce': ['e-commerce'],


    }

OCA_REPOSITORY_NAMES = []
for repos in OCA_PROJECTS.itervalues():
    OCA_REPOSITORY_NAMES += repos
OCA_REPOSITORY_NAMES.sort()

_OCA_REPOSITORY_NAMES = set(OCA_REPOSITORY_NAMES)

_URL_MAPPINGS = {'git': 'git@github.com:OCA/%s.git',
                 'https': 'https://github.com/OCA/%s.git',
                 }
def url(project_name, protocol='git'):
    """get the URL for an OCA project repository"""
    if project_name not in _OCA_REPOSITORY_NAMES:
        raise ValueError('Unknown project', project_name)
    return _URL_MAPPINGS[protocol] % project_name
