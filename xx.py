import re
import asyncio
from typing import AsyncIterator, List, Tuple, Optional

class AsyncXMLStreamParser:
    def __init__(self, tags: List[str]):
        self.tags = tags
        self.buffer = ""
        self.inside_tag = None  # Stores the active tag when inside one
        self.start_index = None
        self.tag_patterns = {tag: (re.compile(f"<{tag}[^>]*>"), re.compile(f"</{tag}>")) for tag in tags}

    async def parse_stream(self, data_stream: AsyncIterator[str]) -> AsyncIterator[Tuple[Optional[str], str]]:
        """
        Async generator that processes an incoming data stream and emits events.
        
        Yields:
            (tag, content) if inside a matching tag.
            (None, content) for unmatched data.
        """
        async for data in data_stream:
            self.buffer += data  # Append new data

            if self.inside_tag is None:  # Looking for a start tag
                for tag, (start_pattern, end_pattern) in self.tag_patterns.items():
                    start_match = start_pattern.search(self.buffer)
                    if start_match:
                        self.inside_tag = tag
                        self.start_index = start_match.end()
                        break

            if self.inside_tag:  # Looking for a closing tag
                _, end_pattern = self.tag_patterns[self.inside_tag]
                end_match = end_pattern.search(self.buffer)
                if end_match:
                    content = self.buffer[self.start_index:end_match.start()]
                    self.buffer = self.buffer[end_match.end():]  # Remove processed data
                    tag = self.inside_tag
                    self.inside_tag = None
                    self.start_index = None
                    yield (tag, content.strip())  # Emit extracted content

            # Emit unmatched data
            unmatched_data = self._extract_unmatched_data()
            if unmatched_data:
                yield (None, unmatched_data)

    def _extract_unmatched_data(self) -> str:
        """
        Extracts and removes any leading unmatched data before an XML start tag.
        """
        for tag, (start_pattern, _) in self.tag_patterns.items():
            start_match = start_pattern.search(self.buffer)
            if start_match:
                unmatched = self.buffer[:start_match.start()]
                self.buffer = self.buffer[start_match.start():]  # Keep the start tag in buffer
                return unmatched.strip()
        
        # No start tag found, return entire buffer and clear it
        unmatched = self.buffer
        self.buffer = ""
        return unmatched.strip() if unmatched.strip() else ""

# Example usage with an async generator
async def simulate_stream():
    """Simulates an async data stream with fragmented XML."""
    data_chunks = [
        "Some random te", 
        "xt before <message>Hel",
        "lo</message> and ",
        "<event>Another</ev",
        "ent> followed by more",
        " text."
    ]
    for chunk in data_chunks:
        await asyncio.sleep(0.5)  # Simulate async delay
        yield chunk

async def main():
    parser = AsyncXMLStreamParser(["message", "event"])
    async for tag, content in parser.parse_stream(simulate_stream()):
        if tag:
            print(f"Parsed Event: <{tag}>{content}</{tag}>")
        else:
            print(f"Unmatched Data: {content}")

asyncio.run(main())
