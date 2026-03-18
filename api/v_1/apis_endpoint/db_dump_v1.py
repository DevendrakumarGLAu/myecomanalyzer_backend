from fastapi import APIRouter, HTTPException
import subprocess
import os
from datetime import datetime

router = APIRouter()

DB_USER = "root"
DB_PASSWORD = "mysql"
DB_NAME = "myecomanalyzer"
BACKUP_DIR = "backups"

@router.get("/dump")
def dump_database():
    try:
        # Ensure backup directory exists
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # File name with timestamp
        filename = f"{DB_NAME}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        filepath = os.path.join(BACKUP_DIR, filename)

        # ✅ Use list instead of shell=True (safer)
        command = [
            "mysqldump",
            f"-u{DB_USER}",
            f"-p{DB_PASSWORD}",
            DB_NAME
        ]

        # Write output to file
        with open(filepath, "w") as f:
            result = subprocess.run(command, stdout=f, stderr=subprocess.PIPE, text=True)

        # ✅ Proper error handling
        if result.returncode != 0:
            raise HTTPException(status_code=500, detail=result.stderr)

        return {
            "status": "success",
            "file": filepath
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))