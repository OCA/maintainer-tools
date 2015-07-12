#!/usr/bin/env python
"""
modoornize
"""
import simplejson
from pystache import handlebars
import sys
from os.path import join, dirname, exists


def main():
    from optparse import OptionParser
    parser = OptionParser()
    option = parser.add_option
    option('-t', "--template",
           dest="template_path",
           help="Specify an alternate README template in mustache format",
           metavar="README")
    option('-f', "--force",
           dest="force", action="store_true",
           help="Force generation of README.rst if already present")
    option('-m', "--manifest",
           dest="manifest", action="store_true",
           help="rewrite addon manifest")
    option('-l', "--legacy",
           dest="legacy", action="store_true",
           help="use legacy name __openerp__.py instead of"
           " __odoo__.py for manifest name")

    (options, args) = parser.parse_args()
    print(options)
    copyright, meta = make_readme(template_path=options.template_path,
                                  force=options.force)
    if options.manifest:
        rewrite_meta_data(copyright, meta,
                          "__openerp__.py" if options.legacy
                          else "__odoo__.py")


def make_readme(template_path=None, template=None, force=False):
    """ make a README.rst from __openerp__.py and a template """
    copyright, meta = parse_meta_data('__openerp__.py')

    if not force and exists('README.rst'):
        return copyright, meta

    if template is None:
        if template_path is None:
            template_path = resource('template/module/README.rst.mustache')
        with open(template_path) as data:
            template = data.read().decode('utf8')

    def under(text, char='='):
        return text + '\n' + unicode(char) * len(text)

    meta['project_repo'] = 'FIXME-project_repo'
    meta['module_name'] = 'FIXME-module_name'
    # FIXME extract data
    meta['contributors'] = [{'name': 'Your Name',
                             'email': 'your.name@your.email.provider',
                             'github': 'defunkt'
                             }]

    renderer = handlebars.Renderer()
    renderer.register_helper('=', under)
    rendered = renderer.render(template, meta)

    with open('README.rst', 'wb') as out:
        out.write(rendered.encode('utf8'))

    return copyright, meta


def rewrite_meta_data(copyright, meta, name="__odoo__.py"):
    if 'description' in meta:
        del meta['description']

    with open(name, 'wb') as out:
        out.write(copyright)
        json = simplejson.dumps(meta, indent=' '*4)
        data = json.replace(': false',
                            ': False').replace(': true',
                                               ': True')
        out.write(data)
        out.write('\n')


def parse_meta_data(name="__openerp__.py"):
    meta = None
    with open(name) as oerp:
        data = oerp.read()
        jstart = data.find('{')
        copyright, meta = data[:jstart], eval(data[jstart:])
        for k in meta:
            val = meta[k]
            if isinstance(val, basestring):
                meta[k] = val.decode('utf8')

    return copyright, meta


def resource(path):
    """ get a resource relative to this script's install path """
    return join(dirname(sys.argv[0]), '..', path)


if __name__ == "__main__":
    main()
