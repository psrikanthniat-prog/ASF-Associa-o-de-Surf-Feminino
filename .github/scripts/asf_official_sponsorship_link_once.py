#!/usr/bin/env python3
"""Apply the approved ASF sponsorship link once, on the feature branch only."""
from pathlib import Path
import hashlib
import os
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BRANCH = "fix/official-sponsorship-link"
EXPECTED_BEFORE = "fb6b4030965d8e789db121419e45e4b4d4949260"
EXPECTED_AFTER = "e861f53f8f96398b31c2aaa2240623bb3cc405c0"
OLD_LINE = "      <a href=\"parcerias/\" style=\"display:inline-flex;align-items:center;justify-content:center;padding:13px 20px;background:rgba(255,255,255,.12);color:#fff;border:1px solid rgba(255,255,255,.35);border-radius:999px;font-weight:800;text-decoration:none;\">Ver parcerias atuais</a>"
NEW_LINE = "      <a href=\"https://patrocinio.asf.surf/\" target=\"_blank\" rel=\"noopener noreferrer\" aria-label=\"Patroc\u00ednio oficial ASF (abre em nova aba)\" style=\"display:inline-flex;align-items:center;justify-content:center;padding:13px 20px;background:rgba(255,255,255,.12);color:#fff;border:1px solid rgba(255,255,255,.35);border-radius:999px;font-weight:800;text-decoration:none;\">Patroc\u00ednio oficial ASF</a>"


def git_blob_sha(data):
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def main():
    actual_branch = subprocess.check_output(
        ["git", "branch", "--show-current"], cwd=ROOT, text=True
    ).strip()
    if actual_branch != BRANCH or os.environ.get("GITHUB_REF_NAME", BRANCH) != BRANCH:
        raise SystemExit("Refusing to run outside the approved feature branch")
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise SystemExit("Refusing to edit a dirty working tree")
    page = ROOT / "index.html"
    before = page.read_bytes()
    if git_blob_sha(before) != EXPECTED_BEFORE:
        raise SystemExit("index.html changed since approval; refusing to overwrite it")
    old = OLD_LINE.encode("utf-8")
    new = NEW_LINE.encode("utf-8")
    if before.count(old) != 1 or b"https://patrocinio.asf.surf/" in before:
        raise SystemExit("Unexpected link placement or an existing sponsorship link")
    after = before.replace(old, old + b"\n" + new, 1)
    if git_blob_sha(after) != EXPECTED_AFTER:
        raise SystemExit("Generated content does not match the approved patch")
    if after.replace(b"\n" + new, b"", 1) != before:
        raise SystemExit("Unexpected edits outside the new sponsorship link")
    page.write_bytes(after)
    try:
        subprocess.run([sys.executable, "scripts/test_free_content.py"], cwd=ROOT, check=True)
        subprocess.run(["node", "--test", "tests/home-guides-partners.test.cjs"], cwd=ROOT, check=True)
        changed = subprocess.check_output(["git", "diff", "--name-only"], cwd=ROOT, text=True).splitlines()
        if changed != ["index.html"]:
            raise RuntimeError("Unexpected changed paths: " + repr(changed))
    except BaseException:
        page.write_bytes(before)
        raise
    Path(__file__).unlink()
    print("Approved sponsorship link applied and tests passed; temporary helper removed.")


if __name__ == "__main__":
    main()
