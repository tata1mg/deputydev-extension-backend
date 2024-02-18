import json
import time

from openai import OpenAI
from torpedo import CONFIG

config = CONFIG.config

client = OpenAI(api_key=config.get("OPENAI_KEY"))
assistant_id = config.get("ASSISTANT_ID")


async def create_review_thread(diff):
    context = f"Review the following code and add comments (if any) on any line: {diff}"
    print(context)
    return client.beta.threads.create(messages=[{"role": "user", "content": context}])


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
        print(run.status)
        if run.status in ["queued", "in_progress"]:
            print(f"Attempt {attempts + 1} failed. Retrying in {current_interval} seconds.")
            time.sleep(current_interval)
            attempts += 1
        elif run.status in [
            "requires_action",
            "cancelling",
            "cancelled",
            "failed",
            "expired",
        ]:
            break
            # TODO - Log this in sentry with service name and PR id.
            # TODO - If by any reason, the code fails - The customer should be able to view what went wrong in sentry.
        elif run.status == "completed":
            response = await get_response(thread)
            break
        # Increase the interval exponentially, but cap it at max_interval_seconds
        current_interval = min(current_interval * 2, max_interval_seconds)

    return response


async def get_response(thread):
    # TODO - Since assistant API does not support JSON mode, what if it returns back with an invalid JSON
    # TODO - There should be a way to gracefully handle such cases. Maybe log it or call the LLM again to expect correct format.
    return json.loads(
        client.beta.threads.messages.list(thread_id=thread.id).data[0].content[0].text.value.strip("```json")
    )
