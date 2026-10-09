import os
import time

import requests
from dotenv import load_dotenv

load_dotenv(override=True)
url = f"{os.getenv('FCREPO_HOST', 'http://localhost:8080').rstrip('/')}{os.getenv('FCREPO_BASE_PATH', '/fcrepo/rest')}"
username = os.getenv("FCREPO_USERNAME")
password = os.getenv("FCREPO_PASSWORD")
auth = (username, password) if username and password else None
timeout_seconds = int(os.getenv("FCREPO_STARTUP_TIMEOUT", "120"))
deadline = time.monotonic() + timeout_seconds

while time.monotonic() < deadline:
    try:
        response = requests.get(url, auth=auth, timeout=5)
        if response.ok:
            break
        if response.status_code == 401:
            raise SystemExit(f"Fedora rejected the configured credentials at {url}")
    except requests.RequestException:
        pass
    time.sleep(2)
else:
    raise SystemExit(f"Fedora did not become ready at {url} within {timeout_seconds} seconds")

print(f"Fedora is ready at {url}")
