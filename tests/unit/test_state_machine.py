import pytest

from autobuy.domain.enums import JobStatus
from autobuy.domain.errors import DomainError
from autobuy.domain.state_machine import validate_transition


def test_happy_path_transition_is_allowed() -> None:
    validate_transition(JobStatus.MONITORING, JobStatus.ITEM_FOUND)


def test_illegal_transition_is_rejected() -> None:
    with pytest.raises(DomainError):
        validate_transition(JobStatus.MONITORING, JobStatus.ORDER_CONFIRMED)
