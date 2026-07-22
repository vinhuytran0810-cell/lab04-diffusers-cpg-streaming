from __future__ import annotations

import argparse
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path


DEFAULT_EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    "tests",
    "test",
    "examples",
    "docs",
    "scripts",
    "build",
    "dist",
}


def utc_now() -> str:
    """Trả về thời gian UTC theo chuẩn ISO-8601."""
    return (
        datetime.now(timezone.utc)
        .isoformat()
        .replace("+00:00", "Z")
    )


def get_git_commit(repo_path: Path) -> str:
    """Lấy commit hash hiện tại của repository."""
    try:
        return subprocess.check_output(
            [
                "git",
                "-C",
                str(repo_path),
                "rev-parse",
                "HEAD",
            ],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return "unknown"


def discover_python_files(
    repo_path: Path,
    source_root: str = "src/diffusers",
    excluded_dirs: set[str] | None = None,
) -> list[dict[str, object]]:
    """
    Tìm tất cả file .py trong source_root.

    Kết quả của mỗi file gồm:
    - Đường dẫn tương đối
    - Kích thước file
    """
    repo_path = repo_path.resolve()
    root = (repo_path / source_root).resolve()

    if not root.exists():
        raise FileNotFoundError(
            f"Không tìm thấy thư mục mã nguồn: {root}"
        )

    excluded = excluded_dirs or DEFAULT_EXCLUDED_DIRS
    files: list[dict[str, object]] = []

    for file_path in sorted(root.rglob("*.py")):
        relative_path = file_path.relative_to(repo_path)

        contains_excluded_directory = any(
            part.lower() in excluded
            for part in relative_path.parts
        )

        if contains_excluded_directory:
            continue

        files.append(
            {
                "path": relative_path.as_posix(),
                "size_bytes": file_path.stat().st_size,
            }
        )

    return files


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Tìm các file Python trong repository diffusers."
    )

    parser.add_argument(
        "--repo-path",
        default="data/repos/diffusers",
        help="Đường dẫn đến repository diffusers.",
    )

    parser.add_argument(
        "--source-root",
        default="src/diffusers",
        help="Thư mục mã nguồn bên trong repository.",
    )

    parser.add_argument(
        "--output",
        default="data/samples/python_files.json",
        help="File JSON nhận kết quả.",
    )

    args = parser.parse_args()

    repo_path = Path(args.repo_path)
    output_path = Path(args.output)

    files = discover_python_files(
        repo_path=repo_path,
        source_root=args.source_root,
    )

    payload = {
        "schema_version": "1.0",
        "generated_at": utc_now(),
        "repository": "huggingface/diffusers",
        "commit_hash": get_git_commit(repo_path),
        "source_root": args.source_root,
        "total_files": len(files),
        "total_size_bytes": sum(
            int(item["size_bytes"])
            for item in files
        ),
        "files": files,
    }

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    output_path.write_text(
        json.dumps(
            payload,
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    print(f"Đã tìm thấy {payload['total_files']} file Python.")
    print(f"Tổng dung lượng: {payload['total_size_bytes']} bytes.")
    print(f"Commit hash: {payload['commit_hash']}")
    print(f"Kết quả được ghi vào: {output_path.resolve()}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())