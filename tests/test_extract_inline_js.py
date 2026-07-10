import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "extract_inline_js.py"


class ExtractInlineJsTests(unittest.TestCase):
    def run_tool(self, html):
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "page.html"
            output = Path(tmp) / "inline.js"
            source.write_text(html, encoding="utf-8")
            result = subprocess.run(
                ["python3", str(TOOL), str(source), str(output)],
                capture_output=True,
                text=True,
            )
            content = output.read_text(encoding="utf-8") if output.exists() else None
            return result, content

    def test_extracts_multiple_inline_scripts_as_utf8(self):
        result, content = self.run_tool(
            "<script>const title = '剑魂';</script><script>startGame();</script>"
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(content, "const title = '剑魂';\nstartGame();\n")

    def test_excludes_scripts_with_src_attribute(self):
        result, content = self.run_tool(
            '<script src="app.js">ignored()</script><script>included()</script>'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(content, "included()\n")

    def test_preserves_empty_inline_scripts(self):
        result, content = self.run_tool("<script></script><script>later()</script>")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(content, "\nlater()\n")

    def test_argument_errors_exit_nonzero(self):
        result = subprocess.run(
            ["python3", str(TOOL)], capture_output=True, text=True
        )
        self.assertNotEqual(result.returncode, 0)


if __name__ == "__main__":
    unittest.main()
