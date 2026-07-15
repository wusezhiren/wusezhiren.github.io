#!/usr/bin/env python3
"""Capture browser DOM/screenshots and an ffmpeg frame movie without fake evidence."""
import argparse
import hashlib
import http.server
import json
import shutil
import socketserver
import subprocess
import threading
import time
from pathlib import Path
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1]

class EvidencePreParser(HTMLParser):
    def __init__(self):
        super().__init__(); self.in_pre = False; self.value = []
    def handle_starttag(self, tag, attrs):
        if tag == "pre" and dict(attrs).get("id") == "dof70-evidence-result": self.in_pre = True
    def handle_endtag(self, tag):
        if tag == "pre": self.in_pre = False
    def handle_data(self, data):
        if self.in_pre: self.value.append(data)

def parse_evidence(html):
    parser = EvidencePreParser(); parser.feed(html)
    if not parser.value: raise ValueError("missing evidence result JSON")
    return json.loads("".join(parser.value))

def validate_evidence(result, scenario):
    required = {"ready": True, "scenario": scenario["id"], "class": scenario["class"], "state": scenario["state"],
                "targetKind": scenario["targetKind"], "targetMode": scenario["targetMode"], "branch": scenario["targetMode"],
                "hit": scenario["hit"], "migration": scenario["migration"]}
    errors = [f"{key} mismatch" for key, value in required.items() if result.get(key) != value]
    checks = result.get("checks")
    if not isinstance(checks, dict) or not checks or not all(value is True for value in checks.values()): errors.append("evidence checks are not all true")
    if result.get("errors") != []: errors.append("evidence result contains errors")
    return errors

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def build_evidence_url(transport, scenario, port):
    query = scenario["query"]
    # The page's screenshot controls use shot/st; evidence records the explicit
    # class/state contract as well, so provide both without changing the source manifest.
    query += f"&class={scenario['class']}&state={scenario['state']}"
    if transport == "file":
        return (ROOT / "index.html").as_uri() + query
    return f"http://127.0.0.1:{port}/index.html{query}"

def chrome_args(browser, url, *, dump_dom=False, screenshot=None, transport="file"):
    args = [browser, "--headless=new", "--no-sandbox", "--disable-gpu"]
    if transport == "file":
        args.append("--allow-file-access-from-files")
    if dump_dom:
        args.append("--dump-dom")
    if screenshot is not None:
        args.append(f"--screenshot={screenshot}")
    args.append(url)
    return args

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="assets/dof70/evidence")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--transport", choices=("file", "http"), default="file")
    args = parser.parse_args()
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    browser = next((shutil.which(x) for x in ("chromium", "chromium-browser", "google-chrome") if shutil.which(x)), None)
    ffmpeg = shutil.which("ffmpeg")
    scenarios = json.loads((ROOT / "tools/dof70_browser_scenarios.json").read_text())['scenarios']
    errors = []
    if not browser: errors.append("missing Chromium browser (tried chromium, chromium-browser, google-chrome)")
    if not ffmpeg: errors.append("missing ffmpeg")
    server = None
    if args.transport == "http":
        class EvidenceRequestHandler(http.server.SimpleHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def end_headers(self):
                self.send_header("Connection", "close")
                super().end_headers()

        handler = lambda *a, **kw: EvidenceRequestHandler(*a, directory=str(ROOT), **kw)
        socketserver.ThreadingTCPServer.allow_reuse_address = True
        server = socketserver.ThreadingTCPServer(("127.0.0.1", args.port), handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    artifacts = []
    try:
        if browser:
            for scenario in scenarios:
                url = build_evidence_url(args.transport, scenario, args.port)
                try:
                    dom = subprocess.run(chrome_args(browser, url, dump_dom=True, transport=args.transport), cwd=ROOT, text=True, capture_output=True, timeout=45)
                    if dom.returncode: errors.append(f"{scenario['id']}: dump-dom exit {dom.returncode}: {dom.stderr[-300:]}")
                    try:
                        errors.extend(f"{scenario['id']}: {error}" for error in validate_evidence(parse_evidence(dom.stdout), scenario))
                    except (ValueError, json.JSONDecodeError) as exc:
                        errors.append(f"{scenario['id']}: invalid evidence result: {exc}")
                    if errors: continue
                except subprocess.TimeoutExpired:
                    errors.append(f"{scenario['id']}: dump-dom timed out")
                    continue
                image = out / scenario['out']
                try:
                    shot = subprocess.run(chrome_args(browser, url, screenshot=image, transport=args.transport), cwd=ROOT, capture_output=True, timeout=45)
                except subprocess.TimeoutExpired:
                    errors.append(f"{scenario['id']}: screenshot timed out")
                    continue
                if shot.returncode: errors.append(f"{scenario['id']}: screenshot exit {shot.returncode}")
                elif image.is_file(): artifacts.append({"type": "screenshot", "scenario": scenario, "path": image})
        if ffmpeg and not errors:
            # A deterministic numbered sequence makes the movie reproducible from captured frames.
            frames = []
            for i, item in enumerate(artifacts):
                frame = out / f"frame-{i:03d}.png"; shutil.copyfile(item["path"], frame); frames.append(frame)
            movie = out / "dof70-evidence.mp4"
            result = subprocess.run([ffmpeg, "-y", "-framerate", "2", "-i", str(out / "frame-%03d.png"), "-vf", "scale=trunc(iw/2)*2:trunc(ih/2)*2", "-c:v", "libx264", "-pix_fmt", "yuv420p", str(movie)], cwd=ROOT, capture_output=True, text=True, timeout=120)
            if result.returncode: errors.append(f"ffmpeg exit {result.returncode}: {result.stderr[-300:]}")
            elif movie.is_file(): artifacts.append({"scenario": None, "path": movie})
    finally:
        if server:
            server.shutdown(); server.server_close()
    manifest = {"version": 1, "status": "PASS" if not errors else "BLOCKED", "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "transport": args.transport, "urls": {scenario["id"]: build_evidence_url(args.transport, scenario, args.port) for scenario in scenarios}, "checks": ["file://" if args.transport == "file" else "http.server", "dump-dom", "screenshots", "ffmpeg movie"], "scenarios": scenarios, "artifacts": [{"type": "screenshot" if item["scenario"] else "movie", "scenario": item["scenario"]["id"] if item["scenario"] else None, "query": item["scenario"]["query"] if item["scenario"] else None, "path": str(item["path"].relative_to(ROOT)), "sha256": sha(item["path"])} for item in artifacts], "errors": errors}
    manifest_path = out / "manifest.json"; manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
