from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.prompts.claude.claude_4_sonnet_custom_code_query_solver_prompt import (
    Claude4CustomCodeQuerySolverPrompt,
)


class Claude4ThinkingCustomCodeQuerySolverPrompt(Claude4CustomCodeQuerySolverPrompt):
    def get_system_prompt(self) -> str:
        system_prompt = super().get_system_prompt()
        additional_prompt = """
        IMPORTANT: As this is extended thinking model **DO NOT** provide <thinking> tag. 
        """
        return additional_prompt + system_prompt
