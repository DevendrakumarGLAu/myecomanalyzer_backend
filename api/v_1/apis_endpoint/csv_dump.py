from fastapi import APIRouter, UploadFile, File, Form, HTTPException
import mysql.connector
import pandas as pd
import io

router = APIRouter()

DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "mysql"

def map_dtype_to_mysql(dtype, sample_value=None):
    if pd.api.types.is_integer_dtype(dtype):
        return "INT"
    elif pd.api.types.is_float_dtype(dtype):
        return "FLOAT"
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return "DATETIME"
    else:
        if sample_value:
            try:
                pd.to_datetime(sample_value)
                return "DATETIME"
            except:
                pass
        max_len = max(255, len(str(sample_value)) if sample_value is not None else 255)
        return f"VARCHAR({max_len})"

@router.post("/upload-csv")
async def upload_csv(
    db_name: str = Form(...),
    table_name: str = Form(...),
    file: UploadFile = File(...)
):
    try:
        # Validate DB/table names
        if not db_name.isidentifier():
            raise HTTPException(status_code=400, detail="Invalid database name")
        if not table_name.isidentifier():
            raise HTTPException(status_code=400, detail="Invalid table name")

        # Read CSV into DataFrame
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        df.columns = [col.strip() for col in df.columns]

        # Replace NaN with None for MySQL
        df = df.where(pd.notnull(df), None)

        # Connect to MySQL
        conn = mysql.connector.connect(
            host=DB_HOST,
            user=DB_USER,
            password=DB_PASSWORD,
            database=db_name
        )
        cursor = conn.cursor()

        # Check if table exists
        cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
        table_exists = cursor.fetchone() is not None

        if not table_exists:
            columns_def = []
            for col in df.columns:
                sample_val = df[col].dropna().iloc[0] if not df[col].dropna().empty else None
                col_type = map_dtype_to_mysql(df[col].dtype, sample_val)
                columns_def.append(f"`{col}` {col_type}")
            create_query = f"CREATE TABLE `{table_name}` ({', '.join(columns_def)})"
            cursor.execute(create_query)

        # Build insert query
        columns = ", ".join(f"`{col}`" for col in df.columns)
        placeholders = ", ".join(["%s"] * len(df.columns))
        insert_query = f"INSERT INTO `{table_name}` ({columns}) VALUES ({placeholders})"

        # Insert in chunks
        chunk_size = 1000
        total_rows = len(df)
        rows_inserted = 0

        for start in range(0, total_rows, chunk_size):
            chunk = df.iloc[start:start+chunk_size].values.tolist()
            # convert NaN in chunk to None
            chunk = [[None if pd.isna(val) else val for val in row] for row in chunk]
            if chunk:
                cursor.executemany(insert_query, chunk)
                conn.commit()
                rows_inserted += len(chunk)

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "database": db_name,
            "table": table_name,
            "rows_inserted": rows_inserted,
            "table_created": not table_exists
        }

    except mysql.connector.Error as e:
        raise HTTPException(status_code=500, detail=f"MySQL Error: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))