from setuptools import setup, find_packages

setup(
    name='ipbb',
    version='2.7',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'Click-didyoumean',
        'TextTable',
        'Sh',
        'Pexpect'
    ],
    entry_points='''
        [console_scripts]
        ipbb=ipbb.scripts.builder:main
        ipb-prog=ipbb.scripts.programmer:main
    ''',
)