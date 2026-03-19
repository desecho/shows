"""Converters."""


class ConverterBase:
    """Base class for converters."""

    def to_python(self, value: str) -> str:
        """To python."""
        return value

    def to_url(self, value: str) -> str:
        """To URL."""
        return value


class ListConverter(ConverterBase):
    """List converter."""

    regex = "watched|watching|to-watch"
