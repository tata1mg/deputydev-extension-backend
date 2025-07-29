NO_TOOL_USE_FALLBACK_PROMPT = """
You just responded without calling any tool:

You **must** wrap every multi-step reasoning or final review in a TOOL_USE_REQUEST block from the list of tools provided to you.  

If you need more context first, use the tools provided.  
Once you’ve gathered everything, call **PARSE_FINAL_RESPONSE**  tool with a with tool request ad JSON matching its schema:
"""

EXCEPTION_RAISED_FALLBACK = """
When attempting to call your requested tool, we encountered an error:

  • Tool: {tool_name} 
  • Input: {tool_input}  
  • Error: {error_message}

Please do one of the following:

1. **Try a different tool** that can fulfill your need.  
2. **Adjust your parameters** of your tool request.
3. If you were trying to read a file, verify the file path exists and provide correct file path
4. If you were searching, try different search terms

Remember to:
- Always use tools in TOOL_USE_REQUEST blocks
- Verify your tool parameters before making the request
- Use alternative tools if one fails
"""

EXCEPTION_RAISED_FALLBACK_EXTENSION = """
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
