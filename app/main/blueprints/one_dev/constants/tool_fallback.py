EXCEPTION_RAISED_FALLBACK = """
                When attempting to call your requested tool, we encountered an error:

                • Tool Name: {tool_name}
                • Error Type: {error_type}
                • Error Message: {error_message}

                Please do one of the following:

                1. **Try a different tool** that can fulfill your need.
                2. **Adjust your parameters** of your tool request.
                3. If you were trying to read a file, verify the file path exists and provide correct file path
                4. If you were searching, try different search terms

                Remember to:
                - Verify your tool parameters before making the request
                - Retry with same tool or if error persists, use alternative tools if one fails
 """