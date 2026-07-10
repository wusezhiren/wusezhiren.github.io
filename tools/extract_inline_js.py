#!/usr/bin/env python3
import argparse
from html.parser import HTMLParser
from pathlib import Path


class InlineScriptParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=False)
        self.scripts = []
        self._current = None

    def handle_starttag(self, tag, attrs):
        if tag.lower() == "script" and not any(
            name.lower() == "src" for name, _ in attrs
        ):
            self._current = []

    def handle_data(self, data):
        if self._current is not None:
            self._current.append(data)

    def handle_endtag(self, tag):
        if tag.lower() == "script" and self._current is not None:
            self.scripts.append("".join(self._current))
            self._current = None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("html")
    parser.add_argument("output")
    args = parser.parse_args()

    extractor = InlineScriptParser()
    extractor.feed(Path(args.html).read_text(encoding="utf-8"))
    content = "".join(script + "\n" for script in extractor.scripts)
    Path(args.output).write_text(content, encoding="utf-8")


if __name__ == "__main__":
    main()
