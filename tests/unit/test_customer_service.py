from autobuy.control_plane.services.customers import normalize_email


def test_email_normalization_is_stable() -> None:
    assert normalize_email(" User@Example.COM ") == "user@example.com"
