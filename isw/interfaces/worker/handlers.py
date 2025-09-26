from typing import Any, Dict

from isw.core.utils.helpers import safe_get
from isw.interfaces.worker.tasks import process_technical_submission


def handle_process_technical_submission(event: Dict[str, Any]):
    """
    Lambda handler for S3 file processing.
    This is just a wrapper -- let the task handle its own errors and validation.
    """
    records = event.get("Records", [])
    record = records[0]

    process_technical_submission(
        {
            "bucket_name": safe_get(record, "s3", "bucket", "name"),
            "key": safe_get(record, "s3", "object", "key"),
        }
    )
