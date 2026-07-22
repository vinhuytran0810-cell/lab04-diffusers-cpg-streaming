from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def stable_id(*parts: Any) -> str:
    """
    Tạo một ID SHA-256 ổn định từ các thành phần đầu vào.

    Cùng một tập giá trị đầu vào luôn sinh ra cùng một ID.
    Hàm này sẽ được dùng cho node, edge và file.
    """
    normalized = "::".join(
        "" if part is None else str(part)
        for part in parts
    )

    return hashlib.sha256(
        normalized.encode("utf-8")
    ).hexdigest()


def file_content_hash(
    file_path: Path,
    chunk_size: int = 1024 * 1024,
) -> str:
    """
    Tính SHA-256 của nội dung file theo từng khối.

    Cách đọc theo chunk giúp không phải nạp toàn bộ file
    vào bộ nhớ cùng lúc.
    """
    digest = hashlib.sha256()

    with file_path.open("rb") as file:
        while chunk := file.read(chunk_size):
            digest.update(chunk)

    return digest.hexdigest()