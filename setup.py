from setuptools import setup, find_packages

# Retrieve the list of requirements
with open('requirements.txt') as f:
    # Strip leading and trailing spaces
    requirements = [f.strip() for f in f.read().splitlines()]

    # Drop empty lines and comments
    requirements = [f for f in requirements if f and not f.startswith('#')]


setup(
    install_requires=[
        "Cerberus==1.3.4",
        "click==8.0.4",
        "click-didyoumean==0.3.0",
        "configparser==5.2.0",
        "future==0.18.2",
        "ipaddress==1.0.23",
        "pexpect==4.8.0",
        "psutil==5.9.0",
        "pytest==7.0.1",
        "PyYAML==6.0",
        "rich==12.2.0",
        "sh==1.14.2",
        "vsg==3.10.0",
        "vunit-hdl==4.6.0",
    ],
    extras_require={"develop": [
        "ipdb",
        "ipython"
    ]},
)
