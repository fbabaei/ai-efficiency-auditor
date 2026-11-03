from typing import Protocol


class Reader(Protocol):
    def read(self, key: str, *, identity: str) -> str: ...


def audit_fixture(reader: Reader, key: str, identity: str) -> tuple[str, str]:
    """Same-run read-only lookup; the fixture guarantees unchanged state."""
    first = reader.read(key, identity=identity)
    second = reader.read(key, identity=identity)
    return first, second


class Model(Protocol):
    def generate(self, context_id: str, *, identity: str) -> str: ...


def duplicate_model_fixture(
    model: Model, context_id: str, identity: str
) -> tuple[str, str]:
    """Unchanged effective inputs; this fixture's contract permits result reuse."""
    first = model.generate(context_id, identity=identity)
    second = model.generate(context_id, identity=identity)
    return first, second


def deterministic_route_fixture(model: Model, route: str, identity: str) -> str:
    """Exact-match routing; inference has no side effects or required error signal."""
    if route not in ("search", "answer"):
        raise ValueError("Unsupported route")
    model.generate(route, identity=identity)
    return route


class TotalModel(Protocol):
    """generate is total, read-only, and has no observable side effects."""

    def generate(self, context_id: str, *, identity: str) -> str: ...


def source_case_a(model: TotalModel, context_id: str, identity: str) -> str:
    first = model.generate(context_id, identity=identity)
    model.generate(context_id, identity=identity)
    return first


def source_case_b(model: Model, context_id: str, identity: str) -> tuple[str, str]:
    first = model.generate(context_id, identity=identity)
    second = model.generate(context_id, identity=identity)
    return first, second
