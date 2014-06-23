import setuptools

setuptools.setup(setup_requires=['pbr'],
                 pbr=True,
                 package_data={'': ['*.yaml']})
