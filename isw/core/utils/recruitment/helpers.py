from isw.core.errors import ValidationException


def extract_application_id_from_storage_key(key: str) -> str:
    """
    Extract the application ID from a storage key.
    e.g. submissions/application-123/candidate-456.zip

    Args:
        key (str): The storage key to extract the candidate ID from.

    Returns:
        str: The candidate ID.
    """
    try:
        return key.split("/")[1]
    except Exception as e:
        raise ValidationException("Application ID missing from storage key") from e


def extract_candidate_id_from_storage_key(key: str) -> str:
    """
    Extract the candidate ID from a storage key.
    e.g. submissions/application-123/candidate-456.zip

    Args:
        key (str): The storage key to extract the candidate ID from.

    Returns:
        str: The candidate ID.
    """
    try:
        return key.split("/").pop().split(".")[0]
    except Exception as e:
        raise ValidationException("Candidate ID missing from storage key") from e


def format_storage_key_with_candidate_details(application_id: str, candidate_id: str, prefix: str) -> str:
    """Format a storage key with candidate details."""
    return f"{prefix}/{application_id}/{candidate_id}.zip"
