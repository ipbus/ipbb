from setuptools import setup, find_packages

# Retrieve the list of requirements
with open('requirements.txt') as f:
    # Strip leading and trailing spaces
    requirements = [f.strip() for f in f.read().splitlines()]

    # Drop empty lines and comments
    requirements = [f for f in requirements if f and not f.startswith('#')]


setup(
    install_requires=[
        "Cerberus==1.3.2",
        "click==7.1.2",
        "click-didyoumean==0.0.3",
        "configparser==5.0.2",
        "future==0.18.2",
        "ipaddress==1.0.23",
        "ipdb==0.13.7",
        "ipython==7.16.1",
        "pexpect==4.8.0",
        "psutil==5.8.0",
        "pytest==6.2.2",
        "PyYAML==5.4.1",
        "rich==10.1.0",
        "sh==1.14.1",
        "vsg==3.0.0",
    ],
    extras_require={"develop": [
        "ipdb",
        "ipython"
    ]},
)