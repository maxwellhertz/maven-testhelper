import subprocess
import sys
import os
import logging
from watchdog.observers import Observer
from watchdog.events import (
    FileSystemEvent,
    FileMovedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileSystemEventHandler,
)


class MavenTestEventHandler(FileSystemEventHandler):
    """Re-run Maven tests when some source files change."""

    def __init__(self, root: str, logger=None):
        super().__init__()

        self.root = root
        self.logger = logger or logging.root

        # Determine which Maven command to use.
        mvnw_cmd = os.path.join(root, "mvnw.cmd" if os.name == "nt" else "mvnw")
        self.mvn_cmd = mvnw_cmd if os.path.exists(mvnw_cmd) else "mvn"

    def on_moved(self, event: FileMovedEvent):
        super().on_moved(event)
        self.run_tests(event)

    def on_created(self, event: FileCreatedEvent):
        super().on_created(event)
        self.run_tests(event)

    def on_deleted(self, event: FileDeletedEvent):
        super().on_deleted(event)
        self.run_tests(event)

    def on_modified(self, event: FileModifiedEvent):
        super().on_modified(event)
        self.run_tests(event)

    def run_tests(self, event: FileSystemEvent):
        if event.is_directory or os.path.splitext(event.src_path)[-1] != ".java":
            return

        # TODO only re-run the tests that (directly or indirectly) depend on the changed file
        process = subprocess.Popen(
            [self.mvn_cmd, "test"],
            stdout=subprocess.PIPE,
            universal_newlines=True,
            cwd=self.root,
        )
        while True:
            output = process.stdout.readline()
            print(output.strip())
            return_code = process.poll()
            if return_code is not None:
                # Process has finished, read rest of the output
                for output in process.stdout.readlines():
                    print(output.strip())
                break


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    event_handler = MavenTestEventHandler(path)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    try:
        while observer.is_alive():
            observer.join(1)
    finally:
        observer.stop()
        observer.join()
