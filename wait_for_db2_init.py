"""Test if the IBM Db2 container with name targget-db2-db2-1 has initialized."""

import subprocess as sp
from time import sleep

while True:
    result = sp.run(  # noqa: S603
        ["docker", "container", "logs", "target-db2-db2-1"],  # noqa: S607
        stdout=sp.PIPE,
        check=False,
    )
    if b"Setup has completed" in result.stdout:
        print("Setup has completed")  # noqa: T201
        break
    print("Setup in progress")  # noqa: T201
    sleep(30)
