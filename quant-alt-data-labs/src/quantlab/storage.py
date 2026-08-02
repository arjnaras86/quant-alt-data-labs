from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = PROJECT_ROOT / "data"
DATA_DIRECTORY.mkdir(parents=True, exist_ok=True)


def save_frame(
    df: pd.DataFrame,
    filename: str,
    table_name: str | None = None,
) -> Path:
    """
    Save a DataFrame to the project's data directory.

    CSV saving always runs.

    PostgreSQL saving runs only when DATABASE_URL contains
    a real database connection string.
    """
    output_path = DATA_DIRECTORY / filename
    df.to_csv(output_path, index=False)

    print(
        f"Saved CSV: {output_path}",
        flush=True,
    )

    database_url = os.getenv("DATABASE_URL", "").strip()

    placeholder_values = {
        "",
        "none",
        "null",
        "your_database_url",
        "postgresql+psycopg://postgres:your_password@localhost:5432/quant_lab",
    }

    if database_url.lower() in placeholder_values:
        print(
            "PostgreSQL not configured; CSV output only.",
            flush=True,
        )
        return output_path

    if not table_name:
        return output_path

    try:
        from sqlalchemy import create_engine

        engine = create_engine(
            database_url,
            connect_args={"connect_timeout": 5},
        )

        df.to_sql(
            table_name,
            engine,
            if_exists="replace",
            index=False,
            method="multi",
        )

        print(
            f"Saved PostgreSQL table: {table_name}",
            flush=True,
        )

    except Exception as error:
        print(
            "PostgreSQL save skipped because the connection failed:",
            error,
            flush=True,
        )

    return output_path


def load_frame(filename: str) -> pd.DataFrame:
    """
    Load a CSV file from the project data directory.
    """
    input_path = DATA_DIRECTORY / filename

    if not input_path.exists():
        raise FileNotFoundError(
            f"Could not find data file: {input_path}"
        )

    return pd.read_csv(input_path)