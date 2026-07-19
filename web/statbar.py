"""Small helper module so __init__.py can point ComfyUI's WEB_DIRECTORY at
this folder without hardcoding path-join logic in the package root.
ComfyUI serves everything in WEB_DIRECTORY as static files under
/extensions/<package_name>/..., which is how statbar.css and the JS
extension actually reach the browser.
"""

from __future__ import annotations
import os

WEB_DIR = os.path.dirname(os.path.abspath(__file__))


def asset_path(*parts: str) -> str:
    return os.path.join(WEB_DIR, *parts)
