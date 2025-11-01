import re
from typing import List

from deputydev_core.llm_handler.dataclasses.main import TextBlockDelta
from deputydev_core.llm_handler.providers.openrouter_models.prompts.parsers.event_based.text_block_xml_parser import (
    BaseOpenrouterModelTextDeltaParser,
)
from pydantic import BaseModel

from app.main.blueprints.one_dev.models.dto.agent_chats import PlanSteps
from app.main.blueprints.one_dev.services.query_solver.prompts.feature_prompts.code_query_solver.dataclasses.main import (
    TaskPlanBlock,
    TaskPlanBlockContent,
)


class TaskPlanParser(BaseOpenrouterModelTextDeltaParser):
    def __init__(self) -> None:
        super().__init__(xml_tag="task_plan")
        self.task_plan_raw_text = ""

    async def parse_text_delta(self, event: TextBlockDelta, last_event: bool = False) -> List[BaseModel]:
        # since this is one simple tag, we just need to collect all text between the tags
        if event.content.text:
            self.task_plan_raw_text += event.content.text

        # check if we have seen the end tag
        if last_event:
            # extract all steps
            steps = re.findall(r"<step>(.*?)</step>", self.task_plan_raw_text, re.DOTALL)
            all_steps: List[PlanSteps] = []
            for step in steps:
                # Updated regex to handle <completed> tag at the end and capture step description correctly
                step_description_match = re.match(
                    r"^(.*?)(?:<completed>(true|false)</completed>)?$", step.strip(), re.DOTALL
                )
                if step_description_match:
                    step_description = step_description_match.group(1).strip()
                    completed_str = step_description_match.group(2)
                    completed = completed_str == "true" if completed_str else False
                    all_steps.append(
                        PlanSteps(
                            step_description=step_description,
                            is_completed=completed,
                        )
                    )
            self.task_plan_raw_text = ""
            self.start_event_completed = True
            self.event_buffer.append(
                TaskPlanBlock(
                    content=TaskPlanBlockContent(latest_plan_steps=all_steps),
                )
            )

        values_to_return = self.event_buffer
        self.event_buffer = []
        return values_to_return
