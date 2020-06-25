from setuptools import setup, find_packages

# Retrieve the current version
exec(open('src/ipbb/_version.py').read())

# Retrieve the list of requirements
with open('requirements.txt') as f:
    # Strip leading and trailing spaces
    requirements = [f.strip() for f in f.read().splitlines()]

    # Drop empty lines and comments
    requirements = [f for f in requirements if f and not f.startswith('#')]


setup(
    name='ipbb',
    version=__version__,
    author='Alessandro Thea',
    author_email='alessandro.thea@stfc.ac.uk',
    url='https://github.com/ipbus/ipbb',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    include_package_data=True,
    install_requires=requirements,
    entry_points='''
        [console_scripts]
        ipbb=ipbb.scripts.builder:main
        ipb-prog=ipbb.scripts.programmer:main
    ''',
)