import hashlib

from autobuy.orchestration.redis import generate_lease_token


def test_lease_token_digest_matches_sha256() -> None:
    token = generate_lease_token()
    expected = hashlib.sha256(token.raw.encode("utf-8")).hexdigest()

    assert token.digest == expected
