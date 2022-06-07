from setuptools import setup, find_packages
import sys

if sys.version_info <= (3,7):
    install_requires = ["click==7.1.2"]
else:
    install_requires = ["click==8.1.3"]

install_requires += [
        "Cerberus==1.3.4",
        "click-didyoumean==0.3.0",
        "configparser==5.2.0",
        "ipaddress==1.0.23",
        "pexpect==4.8.0",
        "psutil==5.9.0",
        "pytest==7.0.1",
        "PyYAML==6.0",
        "rich==12.4.4",
        "sh==1.14.2",
        # "vsg==3.10.0",
        "vunit-hdl==4.6.0",
    ]

setup(
    install_requires=install_requires,
    extras_require={"develop": [
        "ipdb",
        "ipython"
    ]},
)
