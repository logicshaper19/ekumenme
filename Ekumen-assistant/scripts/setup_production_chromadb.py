#!/usr/bin/env python3
"""
Production ChromaDB Setup Script
Sets up ChromaDB for production deployment with proper configuration
"""

import asyncio
import os
import sys
import logging
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.knowledge_base.production_chromadb_service import production_chromadb
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def setup_production_chromadb():
    """Setup ChromaDB for production"""
    try:
        logger.info("🚀 Setting up Production ChromaDB...")
        
        # Initialize ChromaDB
        await production_chromadb.initialize()
        
        # Check health
        health_status = await production_chromadb._health_check()
        if not health_status:
            logger.error("❌ ChromaDB health check failed")
            return False
        
        logger.info("✅ ChromaDB health check passed")
        
        # Get collection stats
        stats = await production_chromadb.get_collection_stats()
        logger.info(f"📊 Collection stats: {stats}")
        
        # Test adding a document
        test_doc = {
            "page_content": "This is a test document for production ChromaDB setup.",
            "metadata": {
                "type": "test",
                "source": "setup_script",
                "timestamp": "2024-01-01T00:00:00Z"
            }
        }
        
        from langchain_core.documents import Document
        test_document = Document(**test_doc)
        
        doc_ids = await production_chromadb.add_documents([test_document])
        logger.info(f"✅ Test document added with IDs: {doc_ids}")
        
        # Test search
        search_results = await production_chromadb.similarity_search(
            "test document production", k=1
        )
        logger.info(f"✅ Search test returned {len(search_results)} results")
        
        # Clean up test document
        await production_chromadb.delete_documents(doc_ids)
        logger.info("✅ Test document cleaned up")
        
        logger.info("🎉 Production ChromaDB setup completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Production ChromaDB setup failed: {e}")
        return False


async def migrate_existing_data():
    """Migrate existing local ChromaDB data to production"""
    try:
        logger.info("🔄 Migrating existing data to production ChromaDB...")
        
        # This would read from local chroma_db directory
        # and transfer to production server
        # Implementation depends on the local data structure
        
        logger.info("⚠️  Data migration not implemented yet")
        logger.info("💡 Manual migration required:")
        logger.info("   1. Export documents from local ChromaDB")
        logger.info("   2. Import to production ChromaDB")
        logger.info("   3. Verify data integrity")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Data migration failed: {e}")
        return False


async def create_backup():
    """Create backup of production ChromaDB"""
    try:
        logger.info("💾 Creating backup of production ChromaDB...")
        
        backup_data = await production_chromadb.backup_collection()
        
        if "error" in backup_data:
            logger.error(f"❌ Backup failed: {backup_data['error']}")
            return False
        
        # Save backup to file
        import json
        backup_file = f"chromadb_backup_{backup_data['backup_timestamp'].replace(':', '-')}.json"
        
        with open(backup_file, 'w') as f:
            json.dump(backup_data, f, indent=2)
        
        logger.info(f"✅ Backup saved to {backup_file}")
        logger.info(f"📊 Backup contains {backup_data['document_count']} documents")
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Backup creation failed: {e}")
        return False


async def main():
    """Main setup function"""
    logger.info("🎯 Production ChromaDB Setup Script")
    logger.info("=" * 50)
    
    # Check environment variables
    required_vars = [
        "CHROMADB_URL",
        "CHROMADB_USERNAME", 
        "CHROMADB_PASSWORD",
        "OPENAI_API_KEY"
    ]
    
    missing_vars = [var for var in required_vars if not getattr(settings, var, None)]
    if missing_vars:
        logger.error(f"❌ Missing required environment variables: {missing_vars}")
        return False
    
    # Setup ChromaDB
    setup_success = await setup_production_chromadb()
    if not setup_success:
        return False
    
    # Create initial backup
    backup_success = await create_backup()
    if not backup_success:
        logger.warning("⚠️  Initial backup failed, but setup completed")
    
    # Migration info
    await migrate_existing_data()
    
    logger.info("=" * 50)
    logger.info("🎉 Production ChromaDB setup completed!")
    logger.info("📋 Next steps:")
    logger.info("   1. Update your application to use production ChromaDB")
    logger.info("   2. Migrate existing data if needed")
    logger.info("   3. Set up monitoring and alerting")
    logger.info("   4. Configure automated backups")
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
