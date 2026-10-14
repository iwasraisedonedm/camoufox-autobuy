from autobuy.domain.enums import JobStatus, WorkflowMode


def test_auto_purchase_mode_is_canonical() -> None:
    assert WorkflowMode.AUTO_PURCHASE.value == "auto_purchase"


def test_ambiguous_job_state_is_canonical() -> None:
    assert JobStatus.AMBIGUOUS.value == "ambiguous"
