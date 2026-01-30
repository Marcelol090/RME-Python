"""Configuration-related exceptions."""


class ConfigurationError(ValueError):
    """Raised when configuration is invalid or missing."""

    pass


class ProjectError(ValueError):
    """Raised when project file parsing fails."""

    pass
