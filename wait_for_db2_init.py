"""Test if the IBM Db2 container with name targget-db2-db2-1 has initialized."""

import subprocess as sp
import sys
from time import sleep, time

TIMEOUT = 5 * 60  # 5 minute timeout
now = time()
while True:
    result = sp.run(  # noqa: S603
        ["docker", "container", "logs", "target-db2-db2-1"],  # noqa: S607
        capture_output=True,
        check=False,
    )
    if b"Setup has completed" in result.stdout:
        print("Setup has completed")  # noqa: T201
        break
    if time() - now > TIMEOUT:
        print("Setup failed before timeout of 5 minutes.")  # noqa: T201
        sys.exit(1)
    print("Setup in progress")  # noqa: T201
    sleep(15)
