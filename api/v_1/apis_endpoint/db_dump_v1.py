from fastapi import APIRouter, Depends, HTTPException
import subprocess
import os
import re
from datetime import datetime
from dotenv import load_dotenv
import psycopg2

from api.auth import require_staff_user

load_dotenv()

router = APIRouter(dependencies=[Depends(require_staff_user)])

# Source (Production) DB settings — no insecure fallback defaults. These
# previously hardcoded real production Supabase credentials directly in
# source. Read lazily (not at import time) so a missing env var only fails
# this router's own endpoints rather than crashing the whole app on startup.
SOURCE_HOST = os.getenv("SOURCE_DB_HOST")
SOURCE_PORT = os.getenv("SOURCE_DB_PORT", "6543")
SOURCE_DB = os.getenv("SOURCE_DB_NAME", "postgres")
SOURCE_USER = os.getenv("SOURCE_DB_USER")
SOURCE_PASSWORD = os.getenv("SOURCE_DB_PASSWORD")


def _require_source_db_config():
    missing = [
        name for name, val in [
            ("SOURCE_DB_HOST", SOURCE_HOST),
            ("SOURCE_DB_USER", SOURCE_USER),
            ("SOURCE_DB_PASSWORD", SOURCE_PASSWORD),
        ] if not val
    ]
    if missing:
        raise HTTPException(status_code=500, detail=f"Missing required env vars: {', '.join(missing)}")

# Target (Local) DB settings
TARGET_HOST = os.getenv("TARGET_DB_HOST", "localhost")
TARGET_PORT = os.getenv("TARGET_DB_PORT", "5432")
TARGET_DB = os.getenv("TARGET_DB_NAME", "postgres")  # can fallback to postgres or myecomanalyzer
TARGET_USER = os.getenv("TARGET_DB_USER", "postgres")
TARGET_PASSWORD = os.getenv("TARGET_DB_PASSWORD", "postgres")

BACKUP_DIR = "backups"

def python_fallback_dump(filepath: str):
    """Fallback dump using psycopg2 to fetch schemas and write SQL INSERT commands directly."""
    conn = psycopg2.connect(
        host=SOURCE_HOST,
        port=SOURCE_PORT,
        dbname=SOURCE_DB,
        user=SOURCE_USER,
        password=SOURCE_PASSWORD
    )
    try:
        with conn.cursor() as cur:
            # Fetch all public user tables
            cur.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_type = 'BASE TABLE'
                ORDER BY table_name;
            """)
            tables = [row[0] for row in cur.fetchall()]

            with open(filepath, "w", encoding="utf-8") as f:
                f.write(f"-- PostgreSQL Database Dump (Python psycopg2 Fallback)\n")
                f.write(f"-- Source: {SOURCE_HOST}:{SOURCE_PORT}/{SOURCE_DB}\n")
                f.write(f"-- Date: {datetime.now().isoformat()}\n\n")

                # Basic PostgreSQL settings
                f.write("SET statement_timeout = 0;\n")
                f.write("SET lock_timeout = 0;\n")
                f.write("SET client_encoding = 'UTF8';\n")
                f.write("SET standard_conforming_strings = on;\n")
                f.write("SET check_function_bodies = false;\n\n")

                for table in tables:
                    f.write(f"-- Table Data: {table}\n")
                    
                    # Fetch table columns
                    cur.execute("""
                        SELECT column_name 
                        FROM information_schema.columns 
                        WHERE table_name = %s AND table_schema = 'public'
                        ORDER BY ordinal_position;
                    """, (table,))
                    columns = [row[0] for row in cur.fetchall()]
                    
                    if not columns:
                        continue
                        
                    column_str = ", ".join([f'"{col}"' for col in columns])
                    
                    # Fetch table rows
                    cur.execute(f'SELECT {column_str} FROM "{table}";')
                    rows = cur.fetchall()
                    
                    for row in rows:
                        vals = []
                        for val in row:
                            if val is None:
                                vals.append("NULL")
                            elif isinstance(val, (int, float)):
                                vals.append(str(val))
                            elif isinstance(val, bool):
                                vals.append("TRUE" if val else "FALSE")
                            else:
                                # Escape single quotes
                                clean_val = str(val).replace("'", "''")
                                vals.append(f"'{clean_val}'")
                                
                        vals_str = ", ".join(vals)
                        f.write(f'INSERT INTO "{table}" ({column_str}) VALUES ({vals_str});\n')
                    f.write("\n")
    finally:
        conn.close()

@router.get("/dump")
def dump_database():
    _require_source_db_config()
    try:
        # Ensure backup directory exists
        os.makedirs(BACKUP_DIR, exist_ok=True)

        # File name with timestamp
        filename = f"prod_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.sql"
        filepath = os.path.join(BACKUP_DIR, filename)

        # Try using pg_dump first
        try:
            env = os.environ.copy()
            env["PGPASSWORD"] = SOURCE_PASSWORD

            command = [
                "pg_dump",
                "-h", SOURCE_HOST,
                "-p", str(SOURCE_PORT),
                "-U", SOURCE_USER,
                "-d", SOURCE_DB,
                "-F", "p"
            ]

            with open(filepath, "w", encoding="utf-8") as f:
                result = subprocess.run(
                    command,
                    stdout=f,
                    stderr=subprocess.PIPE,
                    env=env,
                    text=True
                )

            if result.returncode != 0:
                raise RuntimeError(result.stderr)
                
            method = "pg_dump"

        except (FileNotFoundError, RuntimeError) as e:
            python_fallback_dump(filepath)
            method = "python_psycopg2_fallback"

        return {
            "status": "success",
            "message": "Backup created successfully from production to local",
            "method_used": method,
            "file": filepath,
            "filename": filename
        }

    except Exception as e:
        if os.path.exists(filepath):
            try:
                os.remove(filepath)
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))

_BACKUP_FILENAME_RE = re.compile(r"^prod_backup_\d{8}_\d{6}\.sql$")


@router.post("/restore")
def restore_database(filename: str | None = None):
    try:
        if not filename:
            # Find the latest SQL backup file in the backups folder
            if not os.path.exists(BACKUP_DIR):
                raise HTTPException(status_code=404, detail="No backups directory found.")
            files = [f for f in os.listdir(BACKUP_DIR) if f.endswith(".sql")]
            if not files:
                raise HTTPException(status_code=404, detail="No SQL backup files found.")
            files.sort()
            filename = files[-1]

        # Only ever accept exactly the filename shape /dump generates — blocks
        # path traversal (../..) and any other file on disk being targeted.
        filename = os.path.basename(filename)
        if not _BACKUP_FILENAME_RE.match(filename):
            raise HTTPException(status_code=400, detail="Invalid backup filename")

        filepath = os.path.join(BACKUP_DIR, filename)
        if not os.path.exists(filepath):
            raise HTTPException(status_code=404, detail=f"File {filename} not found.")

        # Connect to local database
        conn = psycopg2.connect(
            host=TARGET_HOST,
            port=TARGET_PORT,
            dbname=TARGET_DB,
            user=TARGET_USER,
            password=TARGET_PASSWORD
        )
        conn.autocommit = True
        
        # Read the file and execute SQL lines
        with conn.cursor() as cur:
            with open(filepath, "r", encoding="utf-8") as f:
                sql_content = f.read()

            # Execute SQL
            # We can split by semicolon to execute queries or just run the block
            cur.execute(sql_content)

        conn.close()

        return {
            "status": "success",
            "message": f"Successfully restored data from {filename} to local database '{TARGET_DB}'"
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))