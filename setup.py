import setuptools

setuptools.setup(
    setup_requires=[
        'pbr',
    ],
    pbr=True,
    test_suite="tests",
    package_data={'': ['*.yaml']}
)
