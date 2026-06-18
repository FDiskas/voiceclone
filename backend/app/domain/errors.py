"""Domain-level errors. The API layer maps these to HTTP responses."""


class DomainError(Exception):
    """Base class for all expected, user-correctable domain errors."""


class ValidationError(DomainError):
    """A value object or entity was given invalid input."""


class ProfileNotFoundError(DomainError):
    """A voice profile was requested by an id that does not exist."""


class AudioConversionError(DomainError):
    """Uploaded/recorded audio could not be decoded into usable wav."""


class SynthesisError(DomainError):
    """The voice engine failed to produce audio for a request."""
