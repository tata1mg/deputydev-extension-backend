from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.backend_app_creator.prompts.claude.claude_4_sonnet_backend_app_creator_prompt import (
    Claude4BackendAppCreatorPrompt,
)


class Claude4ThinkingBackendAppCreatorPrompt(Claude4BackendAppCreatorPrompt):
    def get_system_prompt(self):
        system_prompt = super().get_system_prompt()
        additional_prompt = """
        IMPORTANT: As this is extended thinking model **DO NOT** provide <thinking> tag. 
        """
        return additional_prompt + system_prompt
