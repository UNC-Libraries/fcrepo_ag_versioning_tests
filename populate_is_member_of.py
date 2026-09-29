#!/usr/bin/env python3
"""
Creates a Fedora parent resource and 100 child resources that assert
pcdm:memberOf back to the parent, for testing inbound-reference listing.
"""

import requests
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

load_dotenv()

# --- Config ---
FCREPO_BASE = os.getenv("FCREPO_HOST", "http://localhost:8080") + os.getenv("FCREPO_BASE_PATH")
AUTH = (os.getenv("FCREPO_USERNAME"), os.getenv("FCREPO_PASSWORD"))
NUM_MEMBERS = 10000
NUM_WORKERS = 10

PCDM_NS = "http://pcdm.org/models#"


def create_resource(turtle_body: str, session: requests.Session = requests) -> str:
    """POST a turtle body to the fedora root, returning the new resource URI."""
    resp = session.post(
        FCREPO_BASE + "/",
        auth=AUTH,
        headers={"Content-Type": "text/turtle"},
        data=turtle_body.encode("utf-8"),
    )
    resp.raise_for_status()
    location = resp.headers["Location"]
    print(f"Created: {location}")
    return location


def create_member(i: int, parent_uri: str) -> str:
    """Creates a single member resource pointing back at parent_uri via pcdm:memberOf.

    Uses its own Session so that connections can be safely reused within a
    worker thread without sharing state across threads.
    """
    member_turtle = f"""
    @prefix pcdm: <{PCDM_NS}> .
    <> a <http://example.org/TestMember> ;
       pcdm:memberOf <{parent_uri}> .
    """
    with requests.Session() as session:
        return create_resource(member_turtle, session)


def main():
    # Create the parent/container resource
    parent_uri = create_resource("<> a <http://example.org/TestContainer> .")

    # Create members in parallel, each pointing back at the parent via pcdm:memberOf
    with ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
        futures = [executor.submit(create_member, i, parent_uri) for i in range(NUM_MEMBERS)]
        for future in as_completed(futures):
            # Raise any exception that occurred in a worker thread
            future.result()

    print(f"\nDone. Parent: {parent_uri}")
    print(f"Created {NUM_MEMBERS} members pointing at it via pcdm:memberOf")


if __name__ == "__main__":
    main()