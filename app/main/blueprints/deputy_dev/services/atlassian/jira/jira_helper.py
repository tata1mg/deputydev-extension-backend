import re
from typing import Any, Dict, List


class JiraHelper:
    @staticmethod
    def parse_description(content: List[Dict[str, Any]], indent_level: int = 0) -> str:  # noqa: C901
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

    @staticmethod
    def extract_confluence_id_from_description(content: Dict[str, Any]) -> str:
        """
        Extracts Confluence links from the given JIRA story description.

        Args:
            description (str): The description of the JIRA story.
        Returns:
            str: confluence id
        """
        confluence_links = JiraHelper.extract_confluence_ids(content)
        if confluence_links:
            confluence_id = JiraHelper.extract_confluence_id_from_link(confluence_links[0])
            return confluence_id

    @staticmethod
    def extract_confluence_ids(data: Dict[str, Any]) -> List[str]:
        """
        Extracts Confluence links from the given JIRA story description.

        Args:
            description (str): The description of the JIRA story.

        Returns:
            list: A list of Confluence links found in the description.
        """
        links: List[str] = []

        def traverse(content: Dict[str, Any] | List[Dict[str, Any]]) -> None:
            if isinstance(content, dict):
                if (
                    "type" in content
                    and content["type"] == "inlineCard"
                    and "attrs" in content
                    and "url" in content["attrs"]
                ):
                    links.append(content["attrs"]["url"])
                for key, value in content.items():
                    traverse(value)
            elif isinstance(content, list):
                for item in content:
                    traverse(item)

        if "fields" in data and "description" in data["fields"] and "content" in data["fields"]["description"]:
            traverse(data["fields"]["description"]["content"])
        return links

    @staticmethod
    def extract_confluence_id_from_link(link: str) -> str | None:
        pattern = r"/pages/(\d+)/"
        if not link:
            return None
        match = re.search(pattern, link)
        if match:
            return match.group(1)
