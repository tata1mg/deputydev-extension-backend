from typing import Any, Dict, List, Optional
from deputydev_core.utils.singleton import Singleton
from torpedo import CONFIG
from google.oauth2 import service_account
import vertexai
import asyncio
from vertexai.generative_models import GenerativeModel, Content, GenerationConfig, Tool, Part, GenerationResponse

config = CONFIG.config


class GeminiServiceClient(metaclass=Singleton):
    def __init__(self):
        credentials_dict = {
            "type": config["VERTEX"].get("type"),
            "project_id": config["VERTEX"].get("project_id"),
            "private_key_id": config["VERTEX"].get("private_key_id"),
            "private_key": config["VERTEX"].get("private_key"),
            "client_email": config["VERTEX"].get("client_email"),
            "client_id": config["VERTEX"].get("client_id"),
            "auth_uri": config["VERTEX"].get("auth_uri"),
            "token_uri": config["VERTEX"].get("token_uri"),
            "auth_provider_x509_cert_url": config["VERTEX"].get("auth_provider_x509_cert_url"),
            "client_x509_cert_url": config["VERTEX"].get("client_x509_cert_url"),
            "universe_domain": config["VERTEX"].get("universe_domain"),
        }
        credentials = service_account.Credentials.from_service_account_info(credentials_dict)
        vertexai.init(
            project=credentials_dict["project_id"], location=config["VERTEX"].get("location"), credentials=credentials
        )

    async def get_llm_non_stream_response(
        self,
        model_name,
        contents: List[Content],
        system_instruction: Part = None,
        tools: List[Tool] = None,
        response_schema: Optional[Dict[str, Any]] = None,
        temperature: float = 0.5,
        tool_config=None,
        response_mime_type: str = "text/plain",
    ) -> GenerationResponse:
        generation_config = GenerationConfig(
            temperature=temperature,
            max_output_tokens=8192,
            response_mime_type=response_mime_type,
            response_schema=response_schema,
        )
        data = await GenerativeModel(
            model_name=model_name, system_instruction=system_instruction
        ).generate_content_async(contents=contents, generation_config=generation_config, tools=tools)
        return data


async def main():
    query = """
    What are some good tools like GitHub Copilot for code generation and AI-assisted development?
    Please respond in JSON format with the following structure:
    {
      "alternatives": [
        {
          "name": "string",
          "description": "string",
          "platforms": ["string"],
        }
      ]
    }
    Examples:
    {
  "alternatives": [
    {
      "name": "CodeWhisperer",
      "description": "An AI-powered coding assistant by AWS that helps developers write code faster.",
      "platforms": ["VS Code", "JetBrains IDEs"],
    },
    {
      "name": "Tabnine",
      "description": "An AI assistant that uses local models to provide code completions.",
      "platforms": ["VS Code", "JetBrains", "Sublime Text"],
    }
    ]
    }
    """
    response_schema = {
        "type": "object",
        "properties": {
            "alternatives": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "description": {"type": "string"},
                        "platforms": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["name", "description"],
                },
            }
        },
        "required": ["alternatives"],
    }
    contents = [Content(role="user", parts=[Part.from_text("What are some good tools like copilot")])]
    data = await GeminiServiceClient().get_llm_non_stream_response(
        model_name="gemini-2.5-pro-preview-03-25", contents=contents, response_schema=response_schema
    )
    import pdb

    pdb.set_trace()
    return data
    # actual_response = data.candidates[0].content.parts[0].text


# asyncio.run(main())
