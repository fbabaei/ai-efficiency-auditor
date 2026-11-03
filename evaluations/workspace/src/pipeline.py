from typing import Protocol


class Reader(Protocol):
    def read(self, key: str, *, identity: str) -> str: ...


def audit_fixture(reader: Reader, key: str, identity: str) -> tuple[str, str]:
    """Same-run read-only lookup; the fixture guarantees unchanged state."""
    first = reader.read(key, identity=identity)
    second = reader.read(key, identity=identity)
    return first, second
