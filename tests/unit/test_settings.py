from autobuy.settings import Settings


def test_settings_use_safe_defaults() -> None:
    settings = Settings()
    assert settings.environment == "local"
    assert settings.api_port == 8000
