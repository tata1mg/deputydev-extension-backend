import json
import time

from openai import OpenAI
from sanic.log import logger
from app.backend_common.utils.sanic_wrapper import CONFIG

config = CONFIG.config

client = OpenAI(api_key=config.get("OPENAI_KEY"))
assistant_id = config.get("ASSISTANT_ID")


async def create_gpt_request(context, data):
    completion = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {
                "role": "system",
                "content": context,
            },
            {"role": "user", "content": data},
        ],
    )
    # Extract and return the generated response
    return completion.choices[0].message.content


async def correct_json_response(data):
    context = (
        "Given a string that is supposed to represent JSON, the goal is to generate a revised version of the "
        "string that adheres to the JSON format. The input string may contain errors or inconsistencies, "
        "and the output should be a valid JSON representation. Focus on fixing any syntax issues, missing or "
        "mismatched brackets, or other common problems found in JSON strings.: "
    )
    return await create_gpt_request(context, data)


async def comment_processor(data):
    context = (
        "Your name is SCRIT, receiving a user's comment thread carefully examine the smart code review analysis. If "
        "the comment involves inquiries about code improvements or other technical discussions, evaluate the provided "
        "pull request (PR) diff and offer appropriate resolutions. Otherwise, respond directly to the posed question "
        "without delving into the PR diff. include all the corrective_code inside ``` CODE ``` markdown"
    )
    return await create_gpt_request(context, data)


async def create_run_id(thread):
    return client.beta.threads.runs.create(thread_id=thread.id, assistant_id=assistant_id)


async def check_run_status(run, thread):
    return client.beta.threads.runs.retrieve(thread_id=thread.id, run_id=run.id)


async def poll_for_success(thread, run):
    attempts = 0
    max_attempts = 10
    initial_interval_seconds = 5
    max_interval_seconds = 60
    current_interval = initial_interval_seconds
    response = None
    while attempts < max_attempts:
        run = await check_run_status(run, thread)
        logger.info(run.status)
        if run.status in ["queued", "in_progress"]:
            logger.info(f"Attempt {attempts + 1} failed. Retrying in {current_interval} seconds.")
            time.sleep(current_interval)
            attempts += 1
        elif run.status in [
            "requires_action",
            "cancelling",
            "cancelled",
            "failed",
            "expired",
        ]:
            logger.error(f"Run failed with status: {run.status}, error: {run.last_error}")
            break
        elif run.status == "completed":
            response = await get_response(thread)
            break
        # Increase the interval by 10 sec, but cap it at max_interval_seconds
        current_interval = min(current_interval + 10, max_interval_seconds)
    logger.info(f"AI Response: {response}")
    return response


async def get_response(thread):
    generated_response = ""
    try:
        response = client.beta.threads.messages.list(thread_id=thread.id)
        generated_response = response.data[0].content[0].text.value
        return json.loads(generated_response.strip("```json"))
    except Exception as e:
        # Log the error and handle it gracefully
        logger.error(f"Error occurred while parsing JSON response: {e}")
        # If needed, you can make additional calls or implement a fallback mechanism here
        return json.loads(correct_json_response(generated_response))
