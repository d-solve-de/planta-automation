"""Exception hierarchy used across the package.

Catching :class:`PlantaFillerError` at the CLI boundary is enough to turn
every expected failure into a readable message and a non-zero exit code.
"""


class PlantaFillerError(Exception):
    """Base class for all errors raised on purpose by planta_filler."""


class ValidationError(PlantaFillerError):
    """User input (CLI arguments, files) is invalid."""


class BrowserError(PlantaFillerError):
    """The browser could not be started or the page is not what we expect."""


class LoginRequiredError(BrowserError):
    """The timesheet did not appear, most likely because no session is logged in."""


class ReferenceFileError(PlantaFillerError):
    """A reference CSV is missing, malformed or has the wrong dimensions."""
