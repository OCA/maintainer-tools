import setuptools

requires = open('requirements.txt', 'r').read().split('/n')

setuptools.setup(setup_requires=['pbr'] + requires,
                 pbr=True,
                 test_suite="tests",
                 package_data={'': ['*.yaml']})
