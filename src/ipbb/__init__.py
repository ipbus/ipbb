import warnings

__version__ = '1.0.a0+2024.dev1'

# Suppress the following warning message (spurious, since using setuptools 54)
#   /data/tsw/ipbb/ipbb/venv/ipbb/lib64/python3.9/site-packages/cerberus/__init__.py:13: UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30. Refrain from using this package or pin to Setuptools<81.
#     from pkg_resources import get_distribution, DistributionNotFound
warnings.filterwarnings("ignore", category=UserWarning, module='cerberus', message='.*pkg_resources is deprecated as an API')
