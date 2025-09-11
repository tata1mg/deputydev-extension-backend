from typing import Any, AsyncIterator, Dict, List, Optional

from deputydev_core.llm_handler.dataclasses.main import (
    NonStreamingResponse,
    StreamingResponse,
    UserAndSystemMessages,
)
from deputydev_core.llm_handler.models.dto.message_thread_dto import (
    ContentBlockCategory,
    MessageData,
    TextBlockData,
)
from deputydev_core.llm_handler.providers.google.prompts.base_prompts.base_gemini_2_point_5_pro_prompt_handler import (
    BaseGemini2Point5ProPromptHandler,
)
from pydantic import BaseModel

from app.backend_common.dataclasses.dataclasses import PromptCategories
from app.backend_common.utils.sanic_wrapper import CONFIG


class Gemini2Point5ProUrlSummaryGenerator(BaseGemini2Point5ProPromptHandler):
    prompt_type = "URL_SUMMARY_GENERATOR"
    prompt_category = PromptCategories.CODE_GENERATION.value
    # MAX_CONTENT_SIZE is number of words, via dividing by 5 we are checking number of words
    max_content_size = int(CONFIG.config["BINARY"]["URL_CONTENT_READER"]["MAX_CONTENT_SIZE"] / 5)

    def get_prompt(self) -> UserAndSystemMessages:
        system_message = f"""
            You are a highly capable language model assistant. Your job is to thoroughly cut down long-form articles ranging in total size {self.max_content_size} and {self.max_content_size + 10000} words in depth and detail without lossing any data. 
            You must not omit any content, including code blocks, tables, equations, or structured data. 
            Your explanation should mirror the structure of the original document, ensuring no part is skipped. 
            Your output should be clear, instructional, and highly accurate, without hallucinations. 
            All elements (such as code, tables, equations) must be preserved, referenced, and explained comprehensively. 
            Maintain the original context, explain rationale and relationships between sections, and ensure the total response does not exceed {self.max_content_size} words.
            """

        user_message = f"""
            I am providing articles. The total size of the combined articles ranges from {self.max_content_size} to {self.max_content_size + 10000} words. 
            Please provide a detailed explanation of the entire article in not more than {self.max_content_size} words based solely on its content.
            
            Instructions:
            
            1. Structure:
               - Preserve the original structure and flow of the article.
               - Do not omit any sections, appendices, footnotes, or embedded notes.
            
            2. Content Elements:
               - Code Blocks:
                 - Include every code snippet exactly as it appears.
                 - Only provide explanations if they are present in the article.
                 - Do not add line-by-line explanations unless explicitly provided.
            
               - Tables:
                 - Reproduce all tables accurately.
                 - Explain content only if explanations are present in the article.
            
               - Equations:
                 - Preserve all mathematical formulas.
                 - Explain variables, derivations, and usage only as described in the article.
            
            3. Explanatory Style:
               - Be clear and instructional, strictly adhering to the article's explanations.
               - Connect ideas only as presented in the article.
               - Avoid summarizing or interpreting content beyond what is provided.
            
            4. Constraints:
               - Do not exceed {self.max_content_size} words.
               - Do not add personal thoughts, interpretations, or external information.
               - Refrain from hallucinating or inventing content not present in the original article.
               - Provide exactly the same number of articles as given.
            
            5. Formatting:
               - Use clear section headers and subheaders.
               - Apply proper markdown formatting for readability.
        """
        summarization_prompt = f"""
            {user_message}
            Input Example: 
            <articles>
                Content of URL {{url_link_1}}: 
                    {{url content}}
                Content of URL {{url_link_2}}: 
                    {{url content}}
            </articles>
            
            Output Example:
            <explanation>
                Explanation of URL {{url_link_1}}: 
                    {{url explanation}}
                Explanation of URL {{url_link_2}}: 
                   {{url explanation}}
            </explanation>
            
            Article is given below (Number of article = {self.params.get("content").count("Content of URL")}):
            <articles>
                {self.params.get("content")}
            </articles>
            
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
        explanation: Optional[str] = None
        if "<explanation>" in text_block.content.text:
            explanation = text_block.content.text.split("<explanation>")[1].split("</explanation>")[0].strip()

        if explanation:
            return {"explanation": explanation}
        raise ValueError("Invalid LLM response format. Explanation not found.")

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

    @classmethod
    async def get_parsed_response_blocks(cls, response_block: List[MessageData]) -> List[BaseModel]:
        raise NotImplementedError("This method must be implemented in the child class")
