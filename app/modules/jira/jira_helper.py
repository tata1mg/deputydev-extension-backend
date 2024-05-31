class JiraHelper:
    @staticmethod
    def parse_description(content, indent_level=0):
        """

        :param content: Rich text format description
        :param indent_level: indent level adds indentation to the line if it comes under a heading
        :return: returns the description in plain text
        """
        text_output = ""
        for item in content:
            item_type = item.get("type", "")

            if item_type == "paragraph":
                for sub_item in item.get("content", []):
                    if sub_item.get("type") == "text":
                        text_output += " " * indent_level + sub_item.get("text", "") + "\n"
                    else:
                        text_output += JiraHelper.parse_description([sub_item], indent_level)
            elif item_type == "codeBlock":
                text_output += " " * indent_level + "Code Block:\n"
                for sub_item in item.get("content", []):
                    if sub_item.get("type") == "text":
                        text_output += " " * (indent_level + 2) + sub_item.get("text", "") + "\n"
            elif item_type == "table":
                text_output += " " * indent_level + "Table:\n"
                for row in item.get("content", []):
                    for cell in row.get("content", []):
                        text_output += " " * (indent_level + 2) + JiraHelper.parse_description(
                            cell.get("content", []), indent_level + 2
                        )
            elif item_type == "panel":
                panel_type = item.get("attrs", {}).get("panelType", "default")
                text_output += " " * indent_level + f"Panel ({panel_type}):\n"
                for sub_item in item.get("content", []):
                    text_output += JiraHelper.parse_description([sub_item], indent_level + 2)
            elif item_type == "text":
                text_output += " " * indent_level + item.get("text", "") + "\n"
            else:
                # Fallback for unknown types
                for sub_item in item.get("content", []):
                    text_output += JiraHelper.parse_description([sub_item], indent_level)
        return text_output
