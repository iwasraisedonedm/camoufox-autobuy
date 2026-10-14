import pytest

from autobuy.adapters.registry import AdapterRegistry


class ExampleFactory:
    retailer_code = "example"
    version = "1.0.0"

    async def create(self, retailer_profile_id):  # type: ignore[no-untyped-def]
        raise NotImplementedError


def test_registry_registers_explicit_adapter() -> None:
    registry = AdapterRegistry()
    registry.register(ExampleFactory())

    assert registry.retailer_codes() == ("example",)
    assert registry.versions() == {"example": "1.0.0"}


def test_registry_rejects_duplicate_adapter() -> None:
    registry = AdapterRegistry()
    registry.register(ExampleFactory())

    with pytest.raises(ValueError):
        registry.register(ExampleFactory())
