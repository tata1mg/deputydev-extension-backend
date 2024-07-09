# flake8: noqa
SCRIT_PROMPT = """
        Please perform a code review of the following diff (produced by `git diff` on my code), and provide suggestions for improvement. 
        In addition to PR diff you will be also give you below context 
        1. User story which will help you to understand what was expected from this PR.
        2. Relevant code chunk as you don't have full repo access it will help you to get more context of code.
        3. Line number of code in pr diff is provided in `<>` block. Line number can be positive or negative. 

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
        'confidence_score': '<floating point confidence score of the comment>',
        'bucket_name': '<bucket name of the comment>'
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
            b) Optionally, specify the language for syntax highlighting by adding the language name after the opening triple backticks (e.g.,```python, ```java).
            c) Ensure that the code snippets are clearly separated from the rest of the text for better readability. 
            Example:
            Incorrect comment: "Instead of importing JivaManager inside the function, it is better to import it at the top of the file to avoid redundant imports and improve readability.cfrom app.managers.jiva import JivaManager async def show_boat(request: Request, headers: Headers): response = await JivaManager().show_boat_based_on_ab(headers) return response"
            Corrected version of comment: "Instead of importing `JivaManager` inside the function, it is better to import it at the top of the file to avoid redundant imports and improve readability.\n\n```python\nfrom app.managers.jiva import JivaManager\n\nasync def show_boat(request: Request, headers: Headers):\n    response = await JivaManager().show_boat_based_on_ab(headers)\n    return response\n```\n"

        4. First review the PR using user story 
        - Verify if the changes align with the user story.
        - Provide comments on any business logic that does not adhere to the user story.
            
        5. In the next step must review the PR based on below rules. 
        About rules:
            1. Each rules(L1) defines sub rules(L2) for which we have to make comments.
            2. The comment should be bucketed. bucket names are title of L1 rule. 
            example: for first rule bucket name is CODE_QUALITY  
            3. Don't return L2 level bucket name only L1 level bucket name should be returned.
       
        Rules:
            1. READABILITY: 
                Clarity: Clarity of the code and its readability for other developers.
                Complexity: Complexity of the code and suggestions for simplification.
                Naming Conventions: Use of clear and descriptive names for variables, functions, and classes.
                Type hint missing: Functions should have type hints for input and return types.  
            
            2. MAINTAINABILITY
                Refactoring: Refactoring to improve code maintainability.
                Technical Debt: Areas where technical debt has been identified and needs to be addressed.
                Deep Nesting: Avoidance of deep nesting and overly complex functions.
                Commented Code: Code should not have commented code.
                
            3. REUSABILITY
               In house Libraries:  Suggest user to use in house libraries wherever applicable. Our organisation uses
                                     certain in house libraries for python specific services, suggest user to 
                                     use them in case user is using some alternate library to perform the 
                                     same function if pr diff contains python code.
                                     - torpedo- It a wrapper written over sanic. for python specific code.
                                     - cache_wrapper - Wrapper written over redis. for python specific code.
                                     - mongoose - library to perform mongo operations. for python specific code.
                                     - tortoise_wrapper - library to perform sql operations. for python specific code.
                                     - openapi - for API documentation. for python specific code.  
               
               Class and function reusability: Classes and functions should be reused for already present code.              
            
            4. SECURITY
                Vulnerabilities: Identifying potential security vulnerabilities (e.g., SQL injection, cross-site scripting).
                Data Privacy: Handling of sensitive data and compliance with privacy standards.
                Sensitive Information: Verify sensitive information like auth tokens, credentials should not be present in code.
                
            5. DOCUMENTATION
                Comments and Annotations: Quality and presence of inline comments and annotations in the code.
                API Documentation: Documentation of APIs, including function descriptions and usage examples.
                Readme and Guides: Quality and completeness of project documentation such as README files and user guides.
                
            6. DOCSTRING: 
                Function docstring missing: Verify proper docstring is present for each newly added function. 
                Class docstring missing: If class docstring is missing. 
                Module docstring missing: If module docstring is missing. 
            
            7. TESTING
                Test Coverage: Adequacy of test coverage and identification of untested code paths.
                Test Quality: Feedback on the quality of test cases, including clarity, correctness, and thoroughness.
            
            8. ARCHITECTURE
                Design Patterns: Feedback on the use of design patterns and overall software architecture.
                Modularity: Modularity and reusability of the code.
                Extensibility: Extensibility of the codebase and its components.
            
            9. DEPENDENCIES
                Vulnerability through dependencies
                Feedback around better dependency management
            
            10. ALGORITHM_EFFICIENCY
                Time Complexity: Time complexity of algorithms and suggestions for optimization.
                Space Complexity: Space complexity and recommendations to reduce memory usage.
                Data Structures: Suggestions to use more efficient data structures to improve performance.
            
            11. RESOURCE_MANAGEMENT - [w.r.t the language and framework being used]
                Memory Usage: Comments on memory allocation and suggestions to optimize memory usage.
                CPU Utilization: Feedback on CPU-intensive operations 
            
            12. DATABASE_PERFORMANCE
                Query Optimization: Efficiency of database queries and suggestions for optimization (e.g., indexing, query refactoring).
                Connection Management: Database connection handling and pooling strategies.
            
            13. ERROR
                Runtime Error: If code can produce run time errors.
                Syntax Error: If code has syntext error.
                Logical Error: Identifying logical errors in the code that affect functionality.
                Edge Cases: Pointing out edge cases that the code does not handle properly.
            
            14. CODE_ROBUSTNESS
                Exception Handling: Examine how exceptions are handled in log messages. Avoid using generic exceptions
                                    and recommend proper exception handling. 
                API Errors: We should have handling for downstream api errors.
                Testing : Write unit tests for new features and bug fixes.
                Fallback Mechanisms: Implement fallback mechanisms for critical operations, such as retrying failed
                                     requests or using default values when necessary.
                                     Use circuit breakers to prevent cascading failures in microservices architectures.
                Timeouts and Retries: Set reasonable timeouts for API calls to prevent hanging requests.
                                      Implement retry logic with exponential backoff for transient errors.
                Handle API Errors: Handle downstream api errors.
                
                
            
            15. PERFORMANCE
                Parallel calls: Ask user to execute multiple tasks parallely if tasks are not dependent.
                Caching: - Make sure code caches the frequently accessed information if the information 
                           is coming from downstream service apis, databases. 
                Timeout: - Proper timeout should be added for api calls or any other network calls.
                
            16. LOGGING
                Log Level: Review the use of log levels (e.g., info, warn, error) in log messages. Verify that 
                            log levels accurately reflect the severity of the events being logged.
                Generic logging: Avoid generic logging and examine if the log messages include sufficient information
                            for understanding the context of the logged events.
            
            17. CODE_QUALITY: 
                Code Style: Adherence to coding standards and style guides (e.g., naming conventions, formatting).
                Best Practices: Suggestions to follow coding best practices (e.g., DRY principle, avoiding magic numbers).
                                use http methods like GET, POST, UPDATE, PATCH for their recommended use case.
                                No business logic inside api controller method.
                                Validate request and response using appropriate tools.
                
            18. USER_STORY
                Valid Implementation: Verify if the changes align with the user story. 
        
        6. Must make any comments specific to removed lines on old file line. 
        
"""
