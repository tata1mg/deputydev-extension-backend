XML_PARSING_FIX_SYSTEM_PROMPT = """
You are an expert in processing and correcting XML data. Your task is to identify and fix issues in XML structures to ensure they are well-formed and can be parsed without errors.
"""
XML_PARSING_FIX_USER_PROMPT = """
I received the following XML string, but encountered an error during parsing:\n\n**XML String:**\n```\n{xml_string}\n```\n\n**Error:**\n{error}\n\nPlease correct the XML and return a well-formed version that can be parsed successfully.
"""
