import sys
from pathlib import Path
from sqlalchemy import create_engine, text

# Ensure repository root (Ekumen-assistant) is on sys.path so `app` imports work
ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from app.core.config import settings

def main():
    print("applying column ensures...", flush=True)
    engine = create_engine(settings.DATABASE_URL_SYNC)
    with engine.begin() as conn:
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS language_preference VARCHAR(10) NOT NULL DEFAULT 'fr'"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS timezone VARCHAR(50) NOT NULL DEFAULT 'Europe/Paris'"))
        conn.execute(text("ALTER TABLE users ADD COLUMN IF NOT EXISTS notification_preferences TEXT"))
    print('Applied column ensures successfully', flush=True)

if __name__ == '__main__':
    main()

