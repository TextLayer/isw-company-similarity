from isw.core.controllers.recruitment_controller import RecruitmentController


def candidate_stage_change(data: dict):
    RecruitmentController().candidate_stage_change(
        application_id=data["application_id"],
        candidate_id=data["candidate_id"],
    )
