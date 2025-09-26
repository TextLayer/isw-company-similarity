from concurrent.futures import ThreadPoolExecutor
from functools import cached_property

from isw.core.commands.base import ReadCommand
from isw.core.errors.validation import ValidationException
from isw.core.schemas.recruitment_schemas import JobData, Resume, ResumeGrade, job_schema
from isw.core.services.llm import ChatClient
from isw.core.utils.llm import extract_output
from isw.templates.prompts import load_prompt


class AnalyzeCandidateResumeCommand(ReadCommand):
    extraction_max_tokens = 750  # keep our extractions shortish
    extraction_temperature = 0.0  # keep our extractions stable and predictable
    grader_temperature = 0.0  # keep our grader stable and predictable

    def __init__(self, job_spec: JobData, resume: str = ""):
        self.job_spec = job_spec
        self.resume = resume

    @cached_property
    def chat_client(self) -> ChatClient:
        return ChatClient()

    def execute(self):
        """Spawn three extraction prompts in parallel, and then grade the combined results"""
        parsed_result = self.execute_parser()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [
                executor.submit(method, parsed_result)
                for method in [
                    self.execute_extraction_of_experience,
                    self.execute_extraction_of_flags,
                    self.execute_extraction_of_qualifications,
                ]
            ]
            extracted_results = [future.result() for future in futures]

        return {
            "grade": self.execute_grader(extracted_results),
            "parsed_resume": parsed_result,
        }

    def execute_extraction(self, prompt: str) -> str:
        """Templated client chat call to standardize extraction prompts"""
        return extract_output(
            self.chat_client.chat(
                max_tokens=self.extraction_max_tokens,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Extract"},
                ],
                temperature=self.extraction_temperature,
            )
        )

    def execute_extraction_of_experience(self, resume_formatted: dict) -> str:
        """Extract the work experience of the resume"""
        return self.execute_extraction(
            load_prompt(
                "resume_extraction_experience",
                education=resume_formatted.get("education", []),
                projects=resume_formatted.get("projects", []),
                work=resume_formatted.get("experiences", []),
                target_role_context={
                    "title": self.job_spec.get("title"),
                    "description": self.job_spec.get("description"),
                },
            )
        )

    def execute_extraction_of_qualifications(self, resume_formatted: dict) -> str:
        """Extract the qualifications of the resume"""
        return self.execute_extraction(
            load_prompt(
                "resume_extraction_qualifications",
                description=self.job_spec.get("description"),
                **self.job_spec.get("qualifications", {}),
                **resume_formatted,
            )
        )

    def execute_extraction_of_flags(self, resume_formatted: dict) -> str:
        """Extract the green and red flags of the resume"""
        return self.execute_extraction(
            load_prompt(
                "resume_extraction_flags",
                awards=resume_formatted.get("awards", []),
                certifications=resume_formatted.get("certifications", []),
                education=resume_formatted.get("education", []),
                experiences=resume_formatted.get("experiences", []),
                flags_green=self.job_spec.get("flags", {}).get("green", []),
                flags_red=self.job_spec.get("flags", {}).get("red", []),
                projects=resume_formatted.get("projects", []),
                publications=resume_formatted.get("publications", []),
                presentations=resume_formatted.get("presentations", []),
                skills=resume_formatted.get("skills", {}),
            )
        )

    def execute_grader(self, resume_extraction_results: list[str]) -> dict:
        """Grade the combined results of the three extractions"""
        [experience, flags, requirements] = resume_extraction_results
        prompt = load_prompt(
            "resume_grader",
            experience=experience,
            flags=flags,
            requirements=requirements,
        )

        return extract_output(
            self.chat_client.structured_output(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": "Generate recommendation"},
                ],
                structured_output=ResumeGrade,
                temperature=self.grader_temperature,
            )
        ).model_dump()

    def execute_parser(self) -> dict:
        """Parse the resume into a structured format"""
        prompt = load_prompt("resume_parser")
        return extract_output(
            self.chat_client.structured_output(
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": f"Parse the resume: {self.resume}"},
                ],
                structured_output=Resume,
                temperature=self.extraction_temperature,
            )
        ).model_dump()

    def validate(self):
        """Validate the job spec and resume"""
        self.job_spec = job_schema.load(self.job_spec)

        if not self.resume:
            raise ValidationException("Resume text required to analyze")

        pass
