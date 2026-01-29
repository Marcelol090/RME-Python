"""IO-related exceptions."""


class OTBMParseError(ValueError):
    """Raised when OTBM parsing fails."""

    pass


class ItemsOTBError(ValueError):
    """Raised when items.otb parsing fails."""

    pass


class ItemsXMLError(ValueError):
    """Raised when items.xml cannot be parsed or validated."""

    pass


class SpawnXmlError(ValueError):
    """Raised when spawn XML parsing fails."""

    pass


class HousesXmlError(ValueError):
    """Raised when houses XML parsing fails."""

    pass


class ZonesXmlError(ValueError):
    """Raised when zones XML parsing fails."""

    pass


class SpriteAppearancesError(RuntimeError):
    """Raised when sprite/appearances loading fails."""

    pass
