from autobuy.orchestration.redis import generate_lease_token


def test_lease_token_is_random_and_hashable() -> None:
    first = generate_lease_token()
    second = generate_lease_token()

    assert first.raw != second.raw
    assert first.digest != second.digest
    assert len(first.digest) == 64
    assert first.raw not in first.digest
