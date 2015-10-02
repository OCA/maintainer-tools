import setuptools

PACKAGES = ['oca']

setuptools.setup(name='oca',
                 description="OCA maintainer tools",
                 namespace_packages=['oca'],
                 setup_requires=['pbr'],
                 pbr=True,
                 test_suite="tests",
                 package_data={'': ['*.yaml']})
