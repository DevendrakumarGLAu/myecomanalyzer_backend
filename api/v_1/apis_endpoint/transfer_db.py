import os
import subprocess
from dotenv import load_dotenv

load_dotenv()

SOURCE_HOST = os.getenv("SOURCE_DB_HOST")
SOURCE_DB = os.getenv("SOURCE_DB_NAME")
SOURCE_USER = os.getenv("SOURCE_DB_USER")
SOURCE_PASSWORD = os.getenv("SOURCE_DB_PASSWORD")

TARGET_HOST = os.getenv("TARGET_DB_HOST")
TARGET_DB = os.getenv("TARGET_DB_NAME")
TARGET_USER = os.getenv("TARGET_DB_USER")
TARGET_PASSWORD = os.getenv("TARGET_DB_PASSWORD")


def transfer_database():
    try:
        print("Starting DB transfer...")

        source_env = os.environ.copy()
        source_env["PGPASSWORD"] = SOURCE_PASSWORD

        target_env = os.environ.copy()
        target_env["PGPASSWORD"] = TARGET_PASSWORD

        dump_process = subprocess.Popen(
            [
                "pg_dump",
                "-h", SOURCE_HOST,
                "-U", SOURCE_USER,
                "-d", SOURCE_DB,
                "-F", "c"
            ],
            env=source_env,
            stdout=subprocess.PIPE
        )

        restore_process = subprocess.run(
            [
                "pg_restore",
                "-h", TARGET_HOST,
                "-U", TARGET_USER,
                "-d", TARGET_DB,
                "--clean",
                "--no-owner"
            ],
            env=target_env,
            stdin=dump_process.stdout,
            capture_output=True,
            text=True
        )

        dump_process.stdout.close()
        dump_process.wait()

        if restore_process.returncode != 0:
            print("ERROR:", restore_process.stderr)
            return False

        print("Transfer completed successfully")
        return True

    except Exception as e:
        print("Transfer failed:", str(e))
        return False


if __name__ == "__main__":
    transfer_database()