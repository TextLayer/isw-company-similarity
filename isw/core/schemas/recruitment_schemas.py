import json
from enum import StrEnum
from typing import List, Optional, TypedDict

from marshmallow import Schema, fields, validate
from pydantic import Field, model_validator
from vaul import StructuredOutput

from isw.core.schemas.base import TypedSchema


class ApplicationMetadataSchema(Schema):
    application_id = fields.Str(required=True)
    bucket_name = fields.Str(required=True)
    candidate_id = fields.Str(required=True)
    storage_key_prefix = fields.Str(required=True)


class CandidateMetadataData(TypedDict, total=False):
    application_id: str
    candidate_id: str


@TypedSchema.implements(CandidateMetadataData)
class CandidateMetadataSchema(Schema):
    application_id = fields.Str(required=True, validate=validate.Length(min=1))
    candidate_id = fields.Str(required=True, validate=validate.Length(min=1))


class CandidateDetailsData(TypedDict, total=False):
    application_id: str
    candidate_id: str
    current_interview_stage: str
    created_at: str
    embedding: Optional[List[float]]
    full_name: str
    job_id: str
    recommendation: str
    resume_text: str
    updated_at: str


@TypedSchema.implements(CandidateDetailsData)
class CandidateDetailsSchema(Schema):
    application_id = fields.Str(required=True)
    candidate_id = fields.Str(required=True)
    current_interview_stage = fields.Str(required=True)
    created_at = fields.Str(required=True)
    embedding = fields.List(fields.Float(), required=False, default=[])
    full_name = fields.Str(required=True)
    job_id = fields.Str(required=True)
    recommendation = fields.Str(required=True)
    resume_text = fields.Str(required=True)
    updated_at = fields.Str(required=True)


class CandidateNoteSchema(Schema):
    candidate_id = fields.Str(required=True)
    note = fields.Str(required=True)


class DownloadTechnicalSubmissionSchema(Schema):
    bucket_name = fields.Str(required=True)
    key = fields.Str(required=True)
    stash_path = fields.Str(required=True)


class GithubAppSchema(Schema):
    app_id = fields.Str(required=True)
    installation_id = fields.Str(required=True)
    private_key = fields.Str(required=True)


class JobFlagData(TypedDict, total=False):
    flag: str
    reasons: Optional[List[str]]


class JobFlagsData(TypedDict, total=False):
    green: Optional[List[JobFlagData]]
    red: Optional[List[JobFlagData]]


class JobQualificationsData(TypedDict, total=False):
    bonus: Optional[List[str]]
    preferred: Optional[List[str]]
    required: Optional[List[str]]


class JobData(TypedDict, total=False):
    description: str
    expectations: Optional[str]
    flags: Optional[JobFlagsData]
    id: Optional[str]
    qualifications: Optional[JobQualificationsData]
    responsibilities: Optional[List[str]]
    title: str


@TypedSchema.implements(JobFlagData)
class JobFlagSchema(TypedSchema):
    flag = fields.Str(required=True)
    reasons = fields.List(fields.Str(), required=False)


@TypedSchema.implements(JobFlagsData)
class JobFlagsSchema(TypedSchema):
    green = fields.List(fields.Nested(JobFlagSchema), required=False)
    red = fields.List(fields.Nested(JobFlagSchema), required=False)


@TypedSchema.implements(JobQualificationsData)
class JobQualificationsSchema(TypedSchema):
    bonus = fields.List(fields.Str(), required=False)
    preferred = fields.List(fields.Str(), required=False)
    required = fields.List(fields.Str(), required=False)


@TypedSchema.implements(JobData)
class JobSchema(TypedSchema):
    description = fields.Str(required=True)
    expectations = fields.Str(required=False)
    flags = fields.Nested(JobFlagsSchema, required=False)
    id = fields.Str(required=False)  # note: used to sync w/ ATS
    qualifications = fields.Nested(JobQualificationsSchema, required=False)
    responsibilities = fields.List(fields.Str(), required=False)
    title = fields.Str(required=True)


class JobsQuerySchema(Schema):
    page = fields.Int(required=False)
    results_per_page = fields.Int(required=False)
    search_query = fields.Str(required=False)


class RecommendationOption(StrEnum):
    STRONGLY_RECOMMEND = "Strongly recommend"
    RECOMMEND = "Recommend"
    NEUTRAL = "Neutral"
    NOT_RECOMMEND = "Not recommended"


class ResumeContactInfo(StructuredOutput):
    email: str = Field(description="Email address")
    phone: Optional[str] = Field(description="Phone number")
    linkedin: Optional[str] = Field(description="LinkedIn profile")
    github: Optional[str] = Field(description="GitHub profile")
    medium: Optional[str] = Field(description="Medium profile")
    website: Optional[str] = Field(description="Personal website or portfolio")
    location: Optional[str] = Field(description="Address")


class ResumeEducation(StructuredOutput):
    achievements: Optional[List[str]] = Field(
        default_factory=list, description="Notable achievements, honors, or relevant coursework"
    )
    degree: Optional[str] = Field(description="Degree type (e.g., BS, MS, PhD)")
    end_date: Optional[str] = Field(description="End date or 'Present' (YYYY-MM format if available)")
    field_of_study: Optional[str] = Field(description="Major or field of study")
    institution: str = Field(description="Name of educational institution")
    start_date: Optional[str] = Field(description="Start date (YYYY-MM format if available)")


class ResumeExperience(StructuredOutput):
    achievements: Optional[List[str]] = Field(default_factory=list, description="Key achievements and accomplishments")
    company: str = Field(description="Company or organization name")
    description: Optional[str] = Field(description="Role description and responsibilities")
    end_date: Optional[str] = Field(description="End date or 'Present' (YYYY-MM format if available)")
    location: Optional[str] = Field(description="Work location")
    position: str = Field(description="Job title or position")
    start_date: Optional[str] = Field(description="Start date (YYYY-MM format if available)")


class ResumePublications(StructuredOutput):
    date: str = Field(description="Publication date (YYYY-MM-DD format)")
    publication_type: Optional[str] = Field(description="Type of publication (e.g., article, book, conference paper)")
    title: str = Field(description="Title of the publication or presentation")
    url: Optional[str] = Field(description="URL of the publication or presentation")


class ResumeSkills(StructuredOutput):
    cloud_platforms: Optional[List[str]] = Field(default_factory=list, description="Cloud platforms and services")
    databases: Optional[List[str]] = Field(default_factory=list, description="Database technologies")
    frameworks_libraries: Optional[List[str]] = Field(default_factory=list, description="Frameworks and libraries")
    languages: Optional[List[str]] = Field(
        default_factory=list, description="Spoken/written languages with proficiency levels"
    )
    programming_languages: Optional[List[str]] = Field(default_factory=list, description="Programming languages")
    tools_technologies: Optional[List[str]] = Field(default_factory=list, description="Other tools and technologies")


class ResumePresentation(StructuredOutput):
    date: Optional[str] = Field(description="Date of the presentation")
    description: Optional[str] = Field(description="Description of the presentation")
    location: Optional[str] = Field(description="Location of the presentation")
    title: str = Field(description="Title of the presentation")


class ResumeProject(StructuredOutput):
    description: Optional[str] = Field(description="Description of the project")
    end_date: Optional[str] = Field(description="End date of the project")
    start_date: Optional[str] = Field(description="Start date of the project")
    title: str = Field(description="Title of the project")


class Resume(StructuredOutput):
    awards: Optional[List[str]] = Field(default_factory=list, description="Awards")
    certifications: Optional[List[str]] = Field(default_factory=list, description="Certifications")
    contact_info: ResumeContactInfo = Field(description="Contact information")
    education: List[ResumeEducation] = Field(default_factory=list, description="Educational background")
    experiences: List[ResumeExperience] = Field(default_factory=list, description="Professional experiences")
    full_name: str = Field(description="Full name")
    professional_title: Optional[str] = Field(description="Current or desired professional title")
    publications: Optional[List[ResumePublications]] = Field(default_factory=list, description="Publications")
    presentations: Optional[List[ResumePresentation]] = Field(default_factory=list, description="Presentations")
    projects: Optional[List[ResumeProject]] = Field(default_factory=list, description="Projects")
    skills: ResumeSkills = Field(description="Skills and competencies")

    @model_validator(mode="before")
    @classmethod
    def parse_json_strings(cls, data):
        if isinstance(data, dict):
            for key, value in data.items():
                if isinstance(value, str):
                    try:
                        data[key] = json.loads(value)
                    except json.JSONDecodeError:
                        pass
        return data


class ResumeGrade(StructuredOutput):
    notes: List[str] = Field(default_factory=list, description="Justification for the recommendation")
    recommendation_result: RecommendationOption = Field(description="Recommendation for the candidate")
    score: float = Field(description="Overall recommendation score", ge=0.0, le=1.0)


class UploadTechnicalSubmissionSchema(Schema):
    application_id = fields.Str(required=True)
    candidate_id = fields.Str(required=True)
    candidate_name = fields.Str(required=True)
    path = fields.Str(required=True)
    repo_name = fields.Str(required=True)


application_metadata_schema = ApplicationMetadataSchema()
candidate_metadata_schema = CandidateMetadataSchema()
candidate_note_schema = CandidateNoteSchema()
candidate_details_schema = CandidateDetailsSchema()
download_technical_submission_schema = DownloadTechnicalSubmissionSchema()
github_app_schema = GithubAppSchema()
job_schema = JobSchema()
jobs_query_schema = JobsQuerySchema()
upload_technical_submission_schema = UploadTechnicalSubmissionSchema()
