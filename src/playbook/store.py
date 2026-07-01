"""Playbook read/write and git commit helper."""

from __future__ import annotations

import re
import subprocess
from pathlib import Path


def read_playbook(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def write_playbook(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")


def current_version(content: str) -> int:
    match = re.search(r"Playbook v(\d+)", content, re.IGNORECASE)
    return int(match.group(1)) if match else 1


def bump_version(content: str, new_version: int) -> str:
    return re.sub(
        r"(Playbook v)\d+",
        rf"\g<1>{new_version}",
        content,
        count=1,
        flags=re.IGNORECASE,
    )


def commit_playbook(repo_root: Path, message: str) -> str:
    script = repo_root / "scripts" / "commit_playbook.sh"
    result = subprocess.run(
        ["bash", str(script), message],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    output = (result.stdout or "") + (result.stderr or "")
    if result.returncode != 0:
        raise RuntimeError(f"Playbook commit failed: {output.strip()}")
    return output.strip()
