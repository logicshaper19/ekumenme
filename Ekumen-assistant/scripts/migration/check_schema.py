#!/usr/bin/env python3
import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal

async def main():
    async with AsyncSessionLocal() as db:
        # Check bbch_stages
        result = await db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'bbch_stages'
            ORDER BY ordinal_position
        """))
        print('BBCH Stages columns:')
        for row in result:
            print(f'  - {row[0]}: {row[1]}')
        
        print()
        
        # Check diseases
        result = await db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'diseases'
            ORDER BY ordinal_position
        """))
        print('Diseases columns:')
        for row in result:
            print(f'  - {row[0]}: {row[1]}')

asyncio.run(main())

