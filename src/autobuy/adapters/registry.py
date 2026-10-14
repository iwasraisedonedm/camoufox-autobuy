"""Registry for explicitly supported retailer adapters."""

from __future__ import annotations

from autobuy.adapters.base import RetailerAdapterFactory


class AdapterRegistry:
    def __init__(self) -> None:
        self._factories: dict[str, RetailerAdapterFactory] = {}

    def register(self, factory: RetailerAdapterFactory) -> None:
        code = factory.retailer_code.strip().casefold()
        if not code:
            raise ValueError("Retailer adapter code cannot be empty")
        if code in self._factories:
            raise ValueError(f"Retailer adapter already registered: {code}")
        self._factories[code] = factory

    def get(self, retailer_code: str) -> RetailerAdapterFactory:
        code = retailer_code.strip().casefold()
        try:
            return self._factories[code]
        except KeyError as exc:
            raise KeyError(f"Unsupported retailer adapter: {code}") from exc

    def retailer_codes(self) -> tuple[str, ...]:
        return tuple(sorted(self._factories))

    def versions(self) -> dict[str, str]:
        return {code: factory.version for code, factory in self._factories.items()}
