from uuid import uuid4

from autobuy.control_plane.schemas import ProfileArtifactCheckpointRequest


def test_profile_checkpoint_requires_positive_version() -> None:
    payload = ProfileArtifactCheckpointRequest(
        worker_id=uuid4(),
        lease_id=uuid4(),
        lease_token="x" * 32,
        encrypted_artifact_ref="retailer-profiles/example/1.json.enc",
        artifact_version=1,
    )

    assert payload.artifact_version == 1
