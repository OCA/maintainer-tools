# -*- coding: utf-8 -*-
"""
Create and modify labels on github to have same labels and same color
on all repo

To use, install PyGithub

git clone git@github.com:jacquev6/PyGithub --branch develop_v2
cd PyGithub
virtualenv env
source env/bin/activate
pip install -r requirements.txt
python setup.py install
cd ..
python -c "import PyGithub"

python edit_tags.py
"""
import PyGithub
import getpass

all_repos = [
    'maintainers-tools',
    'maintainer-quality-tools',
    'OCB',
    # addons
    'account-analytic',
    'account-budgeting',
    'account-closing',
    'account-consolidation',
    'account-financial-reporting',
    'account-financial-tools',
    'account-fiscal-rule',
    'account-invoice-reporting',
    'account-invoicing',
    'account-payment',
    'bank-statement-reconcile',
    'banking',
    'carrier-delivery',
    'commission',
    'connector',
    'connector-accountedge',
    'connector-ecommerce',
    'connector-lims',
    'connector-magento',
    'connector-sage-50',
    'crm',
    'department',
    'e-commerce',
    'geospatial',
    'hr',
    'hr-timesheet',
    'knowledge',
    'l10n-belgium',
    'l10n-italy',
    'l10n-luxembourg',
    'l10n-spain',
    'l10n-switzerland',
    'management-system',
    'manufacture',
    'manufacture-reporting',
    'margin-analysis',
    'multi-company',
    'partner-contact',
    'product-attribute',
    'product-kitting',
    'product-variant',
    'program',
    'project-reporting',
    'project-service',
    'purchase-reporting',
    'purchase-workflow',
    'report-print-send',
    'reporting-engine',
    'rma',
    'sale-financial',
    'sale-reporting',
    'sale-workflow',
    'server-tools',
    'stock-logistics-barcode',
    'stock-logistics-reporting',
    'stock-logistics-tracking',
    'stock-logistics-warehouse',
    'stock-logistics-workflow',
    'vertical-construction',
    'vertical-hotel',
    'vertical-isp',
    'vertical-medical',
    'vertical-ngo',
    'vertical-travel',
    'web',
    'webkit-tools',
    ]

OWNER = 'OCA'

# here is the list of labels we need in each repo
all_labels = {
    'bug': 'fc2929',
    'duplicate': 'cccccc',
    'enhancement': '84b6eb',
    'help wanted': '159818',
    'invalid': 'e6e6e6',
    'question': 'cc317c',
    'needs fixing': 'eb6420',
    'needs review': 'fbca04',
    'work in progress': '0052cc',
    'wontfix': 'ffffff',
    }


login = raw_input("login: ")
password = getpass.getpass(login + '@github.com: ')

g = PyGithub.BlockingBuilder().Login(login, password).Build()

OCA = g.get_user('OCA')

for repo_str in all_repos:
    repo = OCA.get_repo(repo_str)

    labels = repo.get_labels()
    existing_labels = dict((l.name, l.color) for l in labels)

    to_create = []
    to_change_color = []
    for needed_label in all_labels:
        if needed_label not in existing_labels.keys():
            to_create.append(needed_label)
        elif existing_labels[needed_label] != all_labels[needed_label]:
            to_change_color.append(needed_label)

    extra_labels = [l for l in existing_labels if l not in all_labels]

    if to_create:
        print ('Repo %s - Create %s missing labels'
               % (repo_str, len(to_create)))

        try:
            for label_name in to_create:
                repo.create_label(label_name, all_labels[label_name])
        except PyGithub.Blocking._exceptions.ObjectNotFoundException:
            print ("Impossible to create a label on '%s'!"
                   " Please check you access right to this repository."
                   % repo_str)

    if to_change_color:
        print ('Repo %s - Update %s labels with wrong color'
               % (repo_str, len(to_change_color)))

        try:
            for label_name in to_change_color:
                label = repo.get_label(label_name)
                label.edit(color=all_labels[label_name])
        except PyGithub.Blocking._exceptions.ObjectNotFoundException:
            print ("Impossible to update a label on '%s'!"
                   " Please check you access right to this repository."
                   % repo_str)

    if extra_labels:
        print ('Repo %s - Found %s extra labels'
               % (repo_str, len(extra_labels)))
        for label_name in extra_labels:
            print label_name
