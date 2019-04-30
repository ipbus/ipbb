from setuptools import setup, find_packages

exec(open('src/ipbb/_version.py').read())

setup(
    name='ipbb',
    # python_requires='<2.8',
    version=__version__,
    author='Alessandro Thea',
    author_email='alessandro.thea@stfc.ac.uk',
    url='https://github.com/ipbus/ipbb',
    packages=find_packages('src'),
    package_dir={'': 'src'},
    package_data={'': 'externals'},
    include_package_data=True,
    install_requires=[
        'Click',
        'Click-didyoumean',
        'TextTable',
        'Sh',
        'Pexpect',
        'PsUtil',
        'ipaddress',
        'IPython',
        'IPdb',
        'PyTest',
        'PyYAML',
        'configparser',
        'Future',
        'Six',
    ],
    entry_points='''
        [console_scripts]
        ipbb=ipbb.scripts.builder:main
        ipb-prog=ipbb.scripts.programmer:main
    ''',
)