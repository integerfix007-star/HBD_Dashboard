import os
from pathlib import Path

def get_upload_base_dir():
    # 1. Prioritize the Environment Variable from your .env file
    custom_dir = os.getenv("LOCAL_UPLOAD_DIR")

    if custom_dir:
        base = Path(custom_dir)
    else:
        # 2. Fallback to the explicit Docker volume path
        # DO NOT use tempfile.gettempdir() inside Docker for shared volumes
        base = Path("/app/tmp/uploads")

    base.mkdir(parents=True, exist_ok=True)
    return base