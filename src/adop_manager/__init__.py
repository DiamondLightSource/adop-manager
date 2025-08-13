"""Top level API.

.. data:: __version__
    :type: str

    Version number as calculated by https://github.com/pypa/setuptools_scm
"""

from ._version import __version__
from .app import AdOpManager
from .dataaccess import ConfigXmlParser

__all__ = ["__version__", "AdOpManager", "ConfigXmlParser"]
