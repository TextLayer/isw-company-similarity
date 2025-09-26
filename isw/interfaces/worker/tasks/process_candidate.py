from ....core.controllers.recruitment_controller import RecruitmentController
from ....core.schemas.recruitment_schemas import CandidateMetadataData
from ....core.utils.helpers import safe_get
from ....shared.logging.logger import logger
from ....templates.html import load_html


def process_candidate(data: CandidateMetadataData):
    """
    A simple task to run a candidate's PDF through an automated grading pipeline

    Args:
        data (CandidateMetadataData): The data containing the application and candidate IDs

    Returns:
        str: The recommendation result
    """
    controller = RecruitmentController()

    application_id = data.get("application_id")
    candidate_id = data.get("candidate_id")

    logger.debug(f"Processing candidate {candidate_id} for application {application_id}")
    application_details = controller.get_application_details(id=application_id)

    logger.debug("Fetching job details")
    job_spec = controller.get_job_details(id=safe_get(application_details, "job", "id"))

    logger.debug("Converting candidate resume")
    resume = controller.convert_candidate_resume(id=candidate_id)

    logger.debug("Analyzing candidate resume")
    analysis_result = controller.analyze_candidate_resume(job_spec=job_spec, resume=resume)
    grade = analysis_result.get("grade")
    recommendation = grade.get("recommendation_result", None)

    logger.debug("Creating candidate")
    controller.create_candidate(
        application_id=application_id,
        candidate_id=candidate_id,
        current_interview_stage=safe_get(application_details, "currentInterviewStage", "title"),
        full_name=safe_get(analysis_result, "parsed_resume", "full_name"),
        job_id=job_spec.get("id"),
        recommendation=recommendation,
        resume_text=resume,
    )

    logger.debug("Creating candidate note")
    controller.update_candidate_notes(
        candidate_id=candidate_id,
        note=load_html(
            "candidate_note",
            recommendation_result=recommendation,
            score=grade.get("score", 0.0),
            notes=grade.get("notes", []),
        ),
    )

    logger.debug("Completed candidate processing")
    return recommendation
