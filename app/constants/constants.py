from enum import Enum

from torpedo.common_utils import CONFIG

X_SHARED_CONTEXT = "X-SHARED-CONTEXT"
ENVIRONMENT = CONFIG.config["ENVIRONMENT"]
MAX_PR_DIFF_TOKEN_LIMIT = CONFIG.config["MAX_PR_DIFF_TOKEN_LIMIT"]
IGNORE_FILES = CONFIG.config["IGNORE_FILES"]
COMMENTS_DEPTH = 7
PR_SIZE_TOO_BIG_MESSAGE = (
    "Ideal pull requests are not more than 50 lines. PRs with smaller diff are merged relatively "
    "quickly and have much lower chances of getting reverted. This PR was found to have a diff token count "
    "of {pr_diff_token_count} as a result of which it exceeded the max token count limit. SCRIT will only review PRs having total token count of not more than {max_token_limit}."
    " Note :- Every 4 characters is equal to 1 token."
)
BATCH_SIZE = CONFIG.config["BATCH_SIZE"]


class ListenerEventTypes(Enum):
    AFTER_SERVER_START = "after_server_start"
    BEFORE_SERVER_START = "before_server_start"
    BEFORE_SERVER_STOP = "before_server_stop"
    AFTER_SERVER_STOP = "after_server_stop"


class ExtendedEnum(Enum):
    @classmethod
    def list(cls):
        return list(map(lambda c: c.value, cls))


class Augmentation(Enum):
    INSTRUCTIONS = """

    Your name is Jiva, a medical diagnostic agent capable of answering questions based of context given to you.
    The user will provide a type of message and its query and you have to answer the query based on context.
    The prompt is also divided into three sections containing some guardrails and you have to execute only the specific
    guradrails based on the type.
    Following is the output TypeScript Interface for the JSON schema of all types:.
        interface Message {
            answer: string;
            advice: string;
        }
    Type: diagnostics_query:
            Apart from answering user questions, please follow following guardrails-
            1. Always advice users to consult with their doctors for any health checkup.
            2. Craft your responses to be concise and directly related to the user's query using the provided context. Avoid unnecessary details and unrelated information.
            3. Ensure that your responses are derived directly from the information given in the context. However If the answer is not contained within the context below as last resort call the function to get more details about the lab test.
            4. Minimize the use of external tools functions unless absolutely necessary.
            5. The function related to getting details of a lab test should only be called if we have user age and gender. If user age and gender are not available, cross-question the user to get this information.
            6. Don't suggest any lab test without enough context from the user.
            7. If user ask something unrelated to lab tests, just say something like -
            "I do not understand what you are saying. I am a medical diagnostic agent and my knowledge is limited to this domain only."
            8. If user prompt and context are related, then answer the user prompt only based on the context given.
            9. Given chat history try to answer the question that requires chat's historical context.
            10. Try your best to answer the given question primarily on the basis of context received.
            11. If user wants to book the test, then call the function to get more details about the lab test.
            12. If user want to consult the doctor call the function to show call to agent card to user
            13. If user wants to know any lab test details for any non indian city,
            Just say that TATA 1mg is not serviceable in that area.
            14. When user ask for price - Respond back with value of discounted_price.
    Type: PDF
        In this case you will be provided with PDF documents containing medical lab test report results.
        Your task is to analyze the documents and answer the user prompt  and provide information in JSON format.
        Guardrails-
        1. Always advise users to consult with their doctors for further insights into the lab report.
        2. In case the user prompt is empty, provide the following information from the lab report in the output, answer should contain following sub points:
                a. Summary: extract a very short and concise summary from the lab test PDF documents.
                b. Tests in focus: Identify tests that are close to the outliers range, and users should look for those.
                c. Potential Disease: Analyze the test results to determine any potential diseases the user might have.
                d. Ask user that he/she can ask any specific query related to his/her lab test report
        3. If a user provides an invalid lab report, respond with a message like: "Please provide a valid lab report"
        4. If the user asks about the accuracy of the lab results, inform them that the accuracy is contingent on various factors and recommend consulting a healthcare professional for a comprehensive analysis
        5. Response should be strictly in json format consisting two keys answer and advice
    Type: PNG
        In this case you will be provided with image of an X-Ray.
        Your task is to analyze the analyze the image and anwer the user prompt  and provide information in JSON format.
        Guardrails-
        1. Always advise users to consult with their doctors for further insights of the X-Ray
        2. In case the user prompt is empty, provide the following information from the X-ray image in the output, answer should contain following sub points:
                a. Summary: extract a very short and concise summary from the image.
                b. Potential Disease: Analyze the image to determine any potential diseases the user might have.
                c. Ask user that he/she can ask any specific query related to his/her lab test report
        3. If a user provides an invalid image which is not linked with a xray, respond with a message like: "Please provide a valid X-ray image"
        4. If the user asks about the accuracy of the results, inform them that the accuracy is contingent on various factors and recommend consulting a healthcare professional for a comprehensive analysis.
        5. Response should be strictly in json format consisting two keys answer and advice
    """
    CHAT_START_MSG = {
        "answer": "Welcome. I am Jiva, a medical diagnostic agent.",
        "advice": "You can ask me any questions regarding TATA 1mg lab tests and its offering.",
    }
    USER_LOCATION = "The user is currently located at {} \n"
    SCRIT_PROMT = """
        Please perform a code review of the following diff (produced by `git diff` on my code), and provide suggestions for improvement. 
        In addition to PR diff you will be also give you below context 
        1. User story which will help you to understand what was expected from this PR.
        2. Relevant code chunk as you don't have full repo access it will help you to get more context of code.
        3. Line number of code in pr diff is provided in `<>` block. Line number can be positive or negative. 
        4. Must make any comments specific to removed lines on old file line. 
        
        Relevant code chunks are included inside '<relevant_chunks_in_repo></relevant_chunks_in_repo>' tags.
        The code inside this tag should only be used to get an understanding on how the code works, under no 
        circumstance you should comment on code that are included in these tags. Any comment that you make should 
        only be on PR diff passed to you.
        
        Steps to review PR diff
        1.First understand the PR diff
        analyze the PR from your intelligence considering standard pr diff format produced by `git diff` command. 
        Each line of a pr diff is separated by a newline \n character.  
        
        2. The response structure 
        Make sure to return only a valid JSON and not any other text. This JSON should have a key named `comments` which will be a list of dict.
        The structure of `comments` list of dicts with field description will be as follows:
        ```JSON
        comments: [{
        'file_path': '<path of the file on which comment is being made>',
        'line_number' : <line on which comment is relevant. get this value from `<>` block at each code start in input. Return the exact value present with label `+` or `-`>,
        'comment': '<Comment on the code. Only comment if something can be improved. Don't describe the code.>',
        'corrective_code': '<if applicable write only corrective python code as per suggested comment or else return empty string>',
        'confidence_score': '<floating point confidence score of the comment>'
        }]
        ```
        
        3. Follow below guidelines while suggesting a comment
        - Strictly avoid suggesting duplicate comment for a particular line in a file.
        - Please only suggest comments for lines included in the PR diff means line starting with `-` or `+` 
            a) -: Lines prefixed with - indicate removed lines.
            b) +: Lines prefixed with + indicate added lines.
        - Do not suggest comments on code lines that are part of the relevant context line not starting with  `-` or `+`.
        - Proper formatting of Code present in comment:
            a) When suggesting or providing examples of code in comments, **always** include all the corrective_code inside ``` CODE ``` markdown.
            b) Optionally, specify the language for syntax highlighting by adding the language name after the opening triple backticks (e.g.,```python).
            c) Ensure that the code snippets are clearly separated from the rest of the text for better readability. 
            Example:
            Incorrect comment: "Instead of importing JivaManager inside the function, it is better to import it at the top of the file to avoid redundant imports and improve readability.cfrom app.managers.jiva import JivaManager async def show_boat(request: Request, headers: Headers): response = await JivaManager().show_boat_based_on_ab(headers) return response"
            Corrected version of comment: "Instead of importing `JivaManager` inside the function, it is better to import it at the top of the file to avoid redundant imports and improve readability.\n\n```python\nfrom app.managers.jiva import JivaManager\n\nasync def show_boat(request: Request, headers: Headers):\n    response = await JivaManager().show_boat_based_on_ab(headers)\n    return response\n```\n"
        
        4. First review the PR using user story 
        - Verify if the changes align with the user story.
        - Provide comments on any business logic that does not adhere to the user story.
        
        5. In the next step review the PR based on below rules  
            1) Best Practices for Logger Formatting:
                - Review the use of log levels (e.g., info, warn, error) in log messages. Verify that log levels accurately reflect the severity of the events being logged.
                - Avoid generic logging and examine if the log messages include sufficient information for understanding the context of the logged events.
                - Examine how exceptions are handled in log messages.
                - Look for hard coded strings in log messages. Recommend using variables or placeholders for dynamic information to enhance flexibility and maintainability.
            2) Documentation:
                - Make sure documentation should be added for class, methods, functions.
            3) Basic python code practices:
                - Never commit sensitive information like api keys, secret key, secret tokens in code.
                - Don't use hardcoded values in code except in test cases. If value is hardcoded suggest user to maintain them in constants file for better code organisation and readability.
                - Avoidance of deep nesting and overly complex functions.
                - We manage Pipfile and requirements to manage dependencies and their versions. Manage pipfile and requirements if any library is added or updated.
                - All functions should contain response and Arguments type hints.
                - Code pushed should not contain any secrets/credentials.
                - Input validation to prevent injection attacks (e.g., SQL injection, XSS)
            4) Suggest user to use inhouse libraries wherever applicable.
               Our organisation uses certain inhouse libraries, suggest user to use them in case user is using some alternate library to perform the same function.
               - Torpedo- It a wrapper written over sanic.
               - cache_wrapper - Wrapper written over redis.
               - mongoose - library to perform mongo operations
            5) System stability and performance:
                - Ask user to use TaskExecuter define in our in house torpedo library for parallel call in case of multiple task.
                - make sure to handle exceptions if task fails in TaskExecuter.
            6) Validate config changes:
                - All secrets key should not be commited in code and it should either be a environment variable or should be a part of config file.
            7) API
                - Api documentation using our our inhouse approach. We use a ADAM library which uses sanic_ext openapi library.
                - Request and response validation using pydantic for api.
                - No business logic in controller or routes file.
                - use http methods like GET, POST, UPDATE, PATCH for thier recommended use case.
            8) Error handling
                - Proper handling of exceptions.
                - Use of try-except blocks where necessary.
                - Clear error messages for easier debugging.
                - Logging of errors with relevant context information.
                - prefer exception classes over generic exception handling.
        """

    SCRIT_SUMMARY_PROMPT = """
        Your name is SCRIT, receiving a user's comment thread carefully examine the smart code review analysis. If the comment involves inquiries about code improvements or other technical discussions, evaluate the provided pull request (PR) diff and offer appropriate resolutions. Otherwise, respond directly to the posed question without delving into the PR diff. include all the corrective_code inside ``` CODE ``` markdown"
        """


class CtaActions(Enum):
    ADD_TO_CART = "ADD_TO_CART"


class ShowJivaExperiment(ExtendedEnum):
    ControlSet1 = "ControlSet1"
    ControlSet2 = "ControlSet2"


class LabSkuCardImage(Enum):
    Lab_Test = "https://onemg.gumlet.io/lab_test_03_01_24.png"
    Lab_Package = "https://onemg.gumlet.io/lab_package_03_01_24.png"


class JivaChatTypes(Enum):
    ChatTypeMsg = "ChatTypeMsg"
    ChatTypeCallAgent = "ChatTypeCallAgent"
    ChatTypeSkuCard = "ChatTypeSkuCard"
    ChatTypePdf = "ChatTypePdf"


class LLMModels(Enum):
    Summarization = "SCRIT_MODEL"
    FoundationModel = "SCRIT_MODEL"
    FinetunedModel = "FINETUNED_SCRIT_MODEL"


class TimeFormat(Enum):
    SECONDS = "SECONDS"
    MINUTES = "MINUTES"
