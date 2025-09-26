from isw.core.controllers.workflows_controller import WorkflowsController


def handle_update_prompts(data: dict):
    """
    Update the prompt templates with the latest prompts from the service provider.
    """
    WorkflowsController().update_prompts(data.get("provider_name"))
