
from app.backend_common.constants.constants import VCSTypes


def should_skip_trayalabs_request(payload: dict) -> bool:
    """
    Check if a GitHub webhook should be skipped for trayalabs1 organization.

    Args:
        payload (dict): The webhook payload

    Returns:
        bool: True if the webhook should be skipped (early return), False otherwise
    """
    return (payload.get("vcs_type") == VCSTypes.github.value
            and payload.get("organization", {}).get("login") == "trayalabs1")
