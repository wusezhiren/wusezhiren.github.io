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
from urllib.parse import urljoin

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", default="assets/dof70/evidence")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    out = ROOT / args.output_dir
    out.mkdir(parents=True, exist_ok=True)
    browser = next((shutil.which(x) for x in ("chromium", "chromium-browser", "google-chrome") if shutil.which(x)), None)
    ffmpeg = shutil.which("ffmpeg")
    scenarios = json.loads((ROOT / "tools/dof70_browser_scenarios.json").read_text())['scenarios']
    errors = []
    if not browser: errors.append("missing Chromium browser (tried chromium, chromium-browser, google-chrome)")
    if not ffmpeg: errors.append("missing ffmpeg")
    handler = lambda *a, **kw: http.server.SimpleHTTPRequestHandler(*a, directory=str(ROOT), **kw)
    server = socketserver.TCPServer(("127.0.0.1", args.port), handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
    artifacts = []
    try:
        if browser:
            for scenario in scenarios:
                url = f"http://127.0.0.1:{args.port}/index.html{scenario['query']}"
                try:
                    dom = subprocess.run([browser, "--headless", "--no-sandbox", "--disable-gpu", "--dump-dom", url], cwd=ROOT, text=True, capture_output=True, timeout=45)
                    if dom.returncode: errors.append(f"{scenario['id']}: dump-dom exit {dom.returncode}: {dom.stderr[-300:]}")
                    if 'id="dof70-evidence-result"' not in dom.stdout: errors.append(f"{scenario['id']}: missing evidence result element")
                except subprocess.TimeoutExpired:
                    errors.append(f"{scenario['id']}: dump-dom timed out")
                    continue
                image = out / scenario['out']
                try:
                    shot = subprocess.run([browser, "--headless", "--no-sandbox", "--disable-gpu", f"--screenshot={image}", url], cwd=ROOT, capture_output=True, timeout=45)
                except subprocess.TimeoutExpired:
                    errors.append(f"{scenario['id']}: screenshot timed out")
                    continue
                if shot.returncode: errors.append(f"{scenario['id']}: screenshot exit {shot.returncode}")
                elif image.is_file(): artifacts.append(image)
        if ffmpeg and not errors:
            # A deterministic numbered sequence makes the movie reproducible from captured frames.
            frames = []
            for i, image in enumerate(artifacts):
                frame = out / f"frame-{i:03d}.png"; shutil.copyfile(image, frame); frames.append(frame)
            movie = out / "dof70-evidence.mp4"
            result = subprocess.run([ffmpeg, "-y", "-framerate", "2", "-i", str(out / "frame-%03d.png"), "-c:v", "libx264", "-pix_fmt", "yuv420p", str(movie)], cwd=ROOT, capture_output=True, text=True, timeout=120)
            if result.returncode: errors.append(f"ffmpeg exit {result.returncode}: {result.stderr[-300:]}")
            elif movie.is_file(): artifacts.append(movie)
    finally:
        server.shutdown(); server.server_close()
    manifest = {"version": 1, "status": "PASS" if not errors else "BLOCKED", "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "checks": ["http.server", "dump-dom", "screenshots", "ffmpeg movie"], "scenarios": [s['id'] for s in scenarios], "artifacts": [{"path": str(p.relative_to(ROOT)), "sha256": sha(p)} for p in artifacts], "errors": errors}
    manifest_path = out / "manifest.json"; manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
    print(json.dumps(manifest, indent=2))
    return 0 if not errors else 1

if __name__ == "__main__":
    raise SystemExit(main())
