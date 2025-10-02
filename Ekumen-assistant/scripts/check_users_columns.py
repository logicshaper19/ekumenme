import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Ensure repository root (Ekumen-assistant) is on sys.path so `app` imports work
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.core.config import settings

def main():
    print("checking users columns...", flush=True)
    engine = create_engine(settings.DATABASE_URL_SYNC)
    with engine.connect() as conn:
        res = conn.execute(text("""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_name='users'
              AND column_name IN ('language_preference','timezone','notification_preferences')
            ORDER BY column_name
        """))
        cols = [r[0] for r in res]
        print("present:", cols, flush=True)

if __name__ == '__main__':
    main()

