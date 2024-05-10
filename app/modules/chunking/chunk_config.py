from functools import lru_cache
from typing import List

import git
import yaml
from pydantic import BaseModel


class ChunkConfig(BaseModel):
    """
    Configuration settings for chunking files.
    """

    exclude_dirs: list[str] = [
        ".git",
        "node_modules",
        "build",
        ".venv",
        "venv",
        "patch",
        "packages/blobs",
        "dist",
        "Pipfile.lock",
        "package-lock.json",
    ]
    exclude_exts: list[str] = [
        ".min.js",
        ".min.js.map",
        ".min.css",
        ".min.css.map",
        ".tfstate",
        ".tfstate.backup",
        ".jar",
        ".ipynb",
        ".png",
        ".jpg",
        ".jpeg",
        ".download",
        ".gif",
        ".bmp",
        ".tiff",
        ".ico",
        ".mp3",
        ".wav",
        ".wma",
        ".ogg",
        ".flac",
        ".mp4",
        ".avi",
        ".mkv",
        ".mov",
        ".patch",
        ".patch.disabled",
        ".wmv",
        ".m4a",
        ".m4v",
        ".3gp",
        ".3g2",
        ".rm",
        ".swf",
        ".flv",
        ".iso",
        ".bin",
        ".tar",
        ".zip",
        ".7z",
        ".gz",
        ".rar",
        ".pdf",
        ".doc",
        ".docx",
        ".xls",
        ".xlsx",
        ".ppt",
        ".pptx",
        ".svg",
        ".parquet",
        ".pyc",
        ".pub",
        ".pem",
        ".ttf",
        ".dfn",
        ".dfm",
        ".feature",
        "deputy_dev.yaml",
        "pnpm-lock.yaml",
        "LICENSE",
        "poetry.lock",
    ]


@lru_cache(maxsize=None)
def get_blocked_dirs(repo: git.Repo) -> List[str]:
    """
    Get blocked directories from the repository's deputy_dev.yaml file.

    Args:
        repo (GitRepo): The Git repository.

    Returns:
        List[str]: A list of blocked directories.
    """
    try:
        yaml_content = repo.get_contents("deputy_dev.yaml").decoded_content.decode("utf-8")
        deputy_dev_yaml = yaml.safe_load(yaml_content)
        dirs = deputy_dev_yaml.get("blocked_dirs", [])
        return dirs
    except SystemExit:
        raise SystemExit
    except Exception:
        return []
