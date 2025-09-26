import uuid

from isw.core.controllers.recruitment_controller import RecruitmentController
from isw.core.utils.recruitment import (
    extract_application_id_from_storage_key,
    extract_candidate_id_from_storage_key,
)


def process_technical_submission(data: dict):
    bucket_name = data["bucket_name"]
    key = data["key"]

    application_id = extract_application_id_from_storage_key(key)
    candidate_id = extract_candidate_id_from_storage_key(key)
    recruitment_controller = RecruitmentController()
    stash_path = f"/assessment-{uuid.uuid4()}"

    candidate_details = recruitment_controller.get_candidate_details(id=candidate_id)

    submission_path = recruitment_controller.download_technical_submission(
        bucket_name=bucket_name,
        key=key,
        stash_path=stash_path,
    )

    recruitment_controller.upload_technical_submission(
        application_id=application_id,
        candidate_id=candidate_details["id"],
        candidate_name=candidate_details["name"],
        path=submission_path,
        repo_name="textlayer-interview",
    )

    recruitment_controller.cleanup_technical_submission(
        stash_path=stash_path,
    )
