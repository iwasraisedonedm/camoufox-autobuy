from autobuy.control_plane.services.workers import (
    REVIEW_RECOVERY_JOB_STATUSES,
    SAFE_RECOVERY_JOB_STATUSES,
)
from autobuy.domain.enums import JobStatus


def test_safe_recovery_states_exclude_irreversible_submission() -> None:
    assert JobStatus.MONITORING in SAFE_RECOVERY_JOB_STATUSES
    assert JobStatus.SUBMITTING not in SAFE_RECOVERY_JOB_STATUSES
    assert JobStatus.AMBIGUOUS not in SAFE_RECOVERY_JOB_STATUSES


def test_checkout_progress_requires_review_after_worker_loss() -> None:
    assert JobStatus.ADDING_TO_CART in REVIEW_RECOVERY_JOB_STATUSES
    assert JobStatus.PURCHASE_AUTHORIZED in REVIEW_RECOVERY_JOB_STATUSES
