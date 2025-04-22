from typing import Any, AsyncIterator, Dict, List, Optional

from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.models.dto.message_thread_dto import (
    ContentBlockCategory,
    TextBlockData,
)
from app.backend_common.services.llm.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from app.backend_common.services.llm.providers.gemini.prompts.base_prompts.base_gemini_2_point_5_pro import (
    BaseGemini2Point5ProPrompt,
)


class Gemini2Point5ProUrlSummaryGenerator(BaseGemini2Point5ProPrompt):
    prompt_type = "SESSION_SUMMARY_GENERATOR"
    prompt_category = PromptCategories.CODE_GENERATION.value

    def get_prompt(self) -> UserAndSystemMessages:
        # TODO: need to work on prompt
        system_message = """
            You are a highly capable language model assistant. Your job is to thoroughly explain or summarize long-form articles between 16,000 and 25,000 words in depth and detail. 
            You must not omit any content, including code blocks, tables, equations, or structured data. 
            Your explanation should mirror the structure of the original document, ensuring no part is skipped. 
            Your output should be clear, instructional, and highly accurate, without hallucinations. 
            All elements (such as code, tables, equations, and figures) must be preserved, referenced, and explained comprehensively. 
            Maintain the original context, explain rationale and relationships between sections, and ensure the total response does not exceed 16,000 words.
            """

        user_message = f"""
            I have an article that is between 16,000 to 25,000 words. Please provide a detailed explanation of the entire article.
            Follow these instructions:
            Structure: Preserve the structure and flow of the original article. Do not skip any section, appendix, footnote, or embedded note.
                Code Blocks:
                    Include every code snippet as it appears.
                    Explain each snippet thoroughly, including line-by-line explanations where applicable.
                    Describe context, input/output, and usage.
    
                Tables:
                    Reproduce all tables accurately.
                    Explain the content and significance of each table.
    
                Figures & Diagrams:
                    Interpret and describe any figure or diagram mentioned in the article.
                    If textual, reconstruct in markdown or ASCII if helpful.
                Equations:
                    Preserve all mathematical formulas.
                    Explain variables, derivations, and usage.
                Explanatory Style:
                    Be clear, deep, and instructional.
                    Connect ideas logically and show why each part matters.
                    Avoid summarizing. Focus on complete explanation.
            Limits:
                Your explanation should not exceed 16,000 words.
                
            Do not hallucinate or invent content not in the original article.
            Format the output with clear section headers, subheaders, and proper markdown for readability.
        """

        summarization_prompt = f"""
            {user_message}
            Article is given below:
            <article>
                {self.params.get("content")}
            </article>
            
            Send the response in the following format:
            <explanation>
                Your explanation here
            </explanation>
        """

        return UserAndSystemMessages(
            user_message=summarization_prompt,
            system_message=system_message,
        )

    @classmethod
    def _parse_text_block(cls, text_block: TextBlockData) -> Dict[str, Any]:
        summary: Optional[str] = None
        if "<summary>" in text_block.content.text:
            summary = text_block.content.text.split("<summary>")[1].split("</summary>")[0].strip()

        if summary:
            return {"summary": summary}
        raise ValueError("Invalid LLM response format. Summary not found.")

    @classmethod
    def get_parsed_result(cls, llm_response: NonStreamingResponse) -> List[Dict[str, Any]]:

        final_content: List[Dict[str, Any]] = []

        for content_block in llm_response.content:
            if content_block.type == ContentBlockCategory.TOOL_USE_REQUEST:
                raise NotImplementedError("Tool use request not implemented for this prompt")
            elif content_block.type == ContentBlockCategory.TEXT_BLOCK:
                final_content.append(cls._parse_text_block(content_block))

        return final_content

    @classmethod
    async def get_parsed_streaming_events(cls, llm_response: StreamingResponse) -> AsyncIterator[BaseModel]:
        raise NotImplementedError(f"Streaming events not implemented for {cls.prompt_type}")
