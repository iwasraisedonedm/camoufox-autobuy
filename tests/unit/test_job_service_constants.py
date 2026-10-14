from autobuy.control_plane.services.jobs import ACTIVE_JOB_STATUSES
from autobuy.domain.enums import JobStatus


def test_active_job_statuses_include_ambiguous() -> None:
    assert JobStatus.AMBIGUOUS in ACTIVE_JOB_STATUSES


def test_terminal_job_statuses_are_not_active() -> None:
    assert JobStatus.COMPLETED not in ACTIVE_JOB_STATUSES
    assert JobStatus.FAILED not in ACTIVE_JOB_STATUSES
    assert JobStatus.EXPIRED not in ACTIVE_JOB_STATUSES
    assert JobStatus.STOPPED not in ACTIVE_JOB_STATUSES
