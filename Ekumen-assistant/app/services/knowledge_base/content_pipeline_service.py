"""
Content Pipeline Service for Knowledge Base
Handles importing, processing, and managing legitimate agricultural content
"""

import logging
import asyncio
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from pathlib import Path
import json
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_, func, desc
from sqlalchemy.orm import selectinload

from app.core.database import get_async_db
from app.models.knowledge_base import KnowledgeBaseDocument, DocumentType, DocumentStatus
from app.models.user import User, UserRole, UserStatus
from app.models.organization import Organization
from app.services.knowledge_base.rag_service import RAGService
from app.services.knowledge_base.knowledge_base_workflow_service import KnowledgeBaseWorkflowService

logger = logging.getLogger(__name__)


class ContentPipelineService:
    """
    Service for managing the content pipeline for legitimate agricultural content
    """
    
    def __init__(self):
        self.rag_service = RAGService()
        self.workflow_service = KnowledgeBaseWorkflowService()
        self.content_sources = {
            'ekumen_curated': 'Ekumen-provided content',
            'ephy_database': 'EPHY product specifications',
            'external_apis': 'External data sources',
            'user_uploads': 'User-generated content',
            'ai_generated': 'AI-generated content'
        }
    
    async def import_ekumen_content(
        self,
        content_data: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Import Ekumen-curated content (regulations, safety guides, etc.)
        """
        try:
            # Create Ekumen system organization if it doesn't exist
            ekumen_org = await self._get_or_create_ekumen_organization(db)
            
            # Create system user for Ekumen content
            ekumen_user = await self._get_or_create_ekumen_user(db)
            
            # Process content
            document = KnowledgeBaseDocument(
                id=uuid.uuid4(),
                organization_id=ekumen_org.id,
                uploaded_by=ekumen_user.id,
                filename=content_data['filename'],
                file_path=content_data.get('file_path', f"ekumen-content/{content_data['filename']}"),
                file_type=content_data.get('file_type', 'pdf'),
                file_size_bytes=content_data.get('file_size_bytes'),
                document_type=DocumentType(content_data['document_type']),
                description=content_data.get('description'),
                tags=content_data.get('tags', []),
                visibility='public',
                is_ekumen_provided=True,
                processing_status=DocumentStatus.PENDING,
                workflow_metadata={
                    'source': 'ekumen_curated',
                    'imported_at': datetime.utcnow().isoformat(),
                    'content_category': content_data.get('category', 'general'),
                    'version': content_data.get('version', '1.0'),
                    'language': content_data.get('language', 'fr'),
                    'region': content_data.get('region', 'france'),
                    'validated': True  # Ekumen content is pre-validated
                },
                submission_status='approved',  # Ekumen content is auto-approved
                approved_by=ekumen_user.id,
                approved_at=datetime.utcnow(),
                quality_score=content_data.get('quality_score', 0.95),
                version=content_data.get('version', 1)
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            # Process content for RAG if content is provided
            if 'content' in content_data:
                await self.rag_service.add_document_to_vectorstore(
                    document, content_data['content'], db
                )
                document.processing_status = DocumentStatus.COMPLETED
                await db.commit()
            
            logger.info(f"Imported Ekumen content: {document.filename}")
            
            return {
                'success': True,
                'document_id': str(document.id),
                'message': f"Successfully imported {document.filename}"
            }
            
        except Exception as e:
            logger.error(f"Error importing Ekumen content: {e}")
            await db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    async def import_ephy_content(
        self,
        product_data: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Import EPHY product specifications and safety data
        """
        try:
            # Create Ekumen system organization if it doesn't exist
            ekumen_org = await self._get_or_create_ekumen_organization(db)
            ekumen_user = await self._get_or_create_ekumen_user(db)
            
            # Generate content from EPHY data
            content = self._generate_ephy_content(product_data)
            
            # Create document
            document = KnowledgeBaseDocument(
                id=uuid.uuid4(),
                organization_id=ekumen_org.id,
                uploaded_by=ekumen_user.id,
                filename=f"ephy_{product_data.get('numero_amm', 'unknown')}_spec.pdf",
                file_path=f"ephy-content/{product_data.get('numero_amm', 'unknown')}_spec.pdf",
                file_type='pdf',
                document_type=DocumentType.PRODUCT_SPEC,
                description=f"Fiche technique EPHY pour {product_data.get('libelle', 'Produit')}",
                tags=[
                    'ephy',
                    'produit',
                    'fiche_technique',
                    product_data.get('libelle', '').lower(),
                    product_data.get('type_intrant', '').lower()
                ],
                visibility='public',
                is_ekumen_provided=True,
                processing_status=DocumentStatus.PENDING,
                workflow_metadata={
                    'source': 'ephy_database',
                    'ephy_data': product_data,
                    'imported_at': datetime.utcnow().isoformat(),
                    'numero_amm': product_data.get('numero_amm'),
                    'type_intrant': product_data.get('type_intrant'),
                    'validated': True
                },
                submission_status='approved',
                approved_by=ekumen_user.id,
                approved_at=datetime.utcnow(),
                quality_score=0.90,
                version=1
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            # Process content for RAG
            await self.rag_service.add_document_to_vectorstore(
                document, content, db
            )
            document.processing_status = DocumentStatus.COMPLETED
            await db.commit()
            
            logger.info(f"Imported EPHY content: {product_data.get('libelle', 'Unknown product')}")
            
            return {
                'success': True,
                'document_id': str(document.id),
                'message': f"Successfully imported EPHY product: {product_data.get('libelle')}"
            }
            
        except Exception as e:
            logger.error(f"Error importing EPHY content: {e}")
            await db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    async def batch_import_ephy_products(
        self,
        products: List[Dict[str, Any]],
        db: AsyncSession,
        batch_size: int = 10
    ) -> Dict[str, Any]:
        """
        Batch import EPHY products
        """
        results = {
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for i in range(0, len(products), batch_size):
            batch = products[i:i + batch_size]
            
            for product in batch:
                result = await self.import_ephy_content(product, db)
                if result['success']:
                    results['successful'] += 1
                else:
                    results['failed'] += 1
                    results['errors'].append({
                        'product': product.get('libelle', 'Unknown'),
                        'error': result.get('error', 'Unknown error')
                    })
            
            # Small delay between batches to avoid overwhelming the system
            await asyncio.sleep(0.1)
        
        logger.info(f"Batch import completed: {results['successful']} successful, {results['failed']} failed")
        
        return results
    
    async def import_regulatory_content(
        self,
        regulation_data: Dict[str, Any],
        db: AsyncSession
    ) -> Dict[str, Any]:
        """
        Import French agricultural regulations and guidelines
        """
        try:
            ekumen_org = await self._get_or_create_ekumen_organization(db)
            ekumen_user = await self._get_or_create_ekumen_user(db)
            
            document = KnowledgeBaseDocument(
                id=uuid.uuid4(),
                organization_id=ekumen_org.id,
                uploaded_by=ekumen_user.id,
                filename=regulation_data['filename'],
                file_path=f"regulations/{regulation_data['filename']}",
                file_type=regulation_data.get('file_type', 'pdf'),
                document_type=DocumentType.REGULATION,
                description=regulation_data.get('description'),
                tags=regulation_data.get('tags', ['regulation', 'agriculture', 'france']),
                visibility='public',
                is_ekumen_provided=True,
                processing_status=DocumentStatus.PENDING,
                workflow_metadata={
                    'source': 'ekumen_curated',
                    'content_type': 'regulation',
                    'authority': regulation_data.get('authority', 'DGAL'),
                    'effective_date': regulation_data.get('effective_date'),
                    'expiration_date': regulation_data.get('expiration_date'),
                    'region': regulation_data.get('region', 'france'),
                    'validated': True
                },
                submission_status='approved',
                approved_by=ekumen_user.id,
                approved_at=datetime.utcnow(),
                quality_score=0.98,
                version=1
            )
            
            db.add(document)
            await db.commit()
            await db.refresh(document)
            
            # Process content for RAG
            if 'content' in regulation_data:
                await self.rag_service.add_document_to_vectorstore(
                    document, regulation_data['content'], db
                )
                document.processing_status = DocumentStatus.COMPLETED
                await db.commit()
            
            logger.info(f"Imported regulatory content: {document.filename}")
            
            return {
                'success': True,
                'document_id': str(document.id),
                'message': f"Successfully imported regulation: {document.filename}"
            }
            
        except Exception as e:
            logger.error(f"Error importing regulatory content: {e}")
            await db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    async def cleanup_mock_data(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Remove all mock/test data from knowledge base
        """
        try:
            # Find and delete mock documents
            mock_docs_query = select(KnowledgeBaseDocument).where(
                or_(
                    KnowledgeBaseDocument.filename.like('%test%'),
                    KnowledgeBaseDocument.filename.like('%mock%'),
                    KnowledgeBaseDocument.filename.like('%sample%'),
                    KnowledgeBaseDocument.description.like('%test%'),
                    KnowledgeBaseDocument.description.like('%mock%'),
                    KnowledgeBaseDocument.description.like('%sample%')
                )
            )
            
            result = await db.execute(mock_docs_query)
            mock_docs = result.scalars().all()
            
            deleted_count = 0
            for doc in mock_docs:
                # Remove from vector store if processed
                if doc.processing_status == DocumentStatus.COMPLETED:
                    try:
                        # Note: Vector store cleanup would need to be implemented
                        pass
                    except Exception as e:
                        logger.warning(f"Could not remove document {doc.id} from vector store: {e}")
                
                await db.delete(doc)
                deleted_count += 1
            
            await db.commit()
            
            logger.info(f"Cleaned up {deleted_count} mock documents")
            
            return {
                'success': True,
                'deleted_count': deleted_count,
                'message': f"Successfully removed {deleted_count} mock documents"
            }
            
        except Exception as e:
            logger.error(f"Error cleaning up mock data: {e}")
            await db.rollback()
            return {
                'success': False,
                'error': str(e)
            }
    
    async def get_content_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """
        Get statistics about knowledge base content
        """
        try:
            # Total documents
            total_query = select(func.count(KnowledgeBaseDocument.id))
            total_result = await db.execute(total_query)
            total_docs = total_result.scalar()
            
            # Documents by type
            type_query = select(
                KnowledgeBaseDocument.document_type,
                func.count(KnowledgeBaseDocument.id)
            ).group_by(KnowledgeBaseDocument.document_type)
            type_result = await db.execute(type_query)
            docs_by_type = {row[0].value: row[1] for row in type_result}
            
            # Documents by visibility
            visibility_query = select(
                KnowledgeBaseDocument.visibility,
                func.count(KnowledgeBaseDocument.id)
            ).group_by(KnowledgeBaseDocument.visibility)
            visibility_result = await db.execute(visibility_query)
            docs_by_visibility = {row[0]: row[1] for row in visibility_result}
            
            # Ekumen-provided content
            ekumen_query = select(func.count(KnowledgeBaseDocument.id)).where(
                KnowledgeBaseDocument.is_ekumen_provided == True
            )
            ekumen_result = await db.execute(ekumen_query)
            ekumen_docs = ekumen_result.scalar()
            
            # Processing status
            status_query = select(
                KnowledgeBaseDocument.processing_status,
                func.count(KnowledgeBaseDocument.id)
            ).group_by(KnowledgeBaseDocument.processing_status)
            status_result = await db.execute(status_query)
            docs_by_status = {row[0].value: row[1] for row in status_result}
            
            return {
                'total_documents': total_docs,
                'ekumen_provided': ekumen_docs,
                'user_generated': total_docs - ekumen_docs,
                'by_type': docs_by_type,
                'by_visibility': docs_by_visibility,
                'by_status': docs_by_status
            }
            
        except Exception as e:
            logger.error(f"Error getting content statistics: {e}")
            return {
                'error': str(e)
            }
    
    async def _get_or_create_ekumen_organization(self, db: AsyncSession) -> Organization:
        """
        Get or create Ekumen system organization
        """
        # Try to find existing Ekumen organization
        query = select(Organization).where(
            Organization.name == 'Ekumen Platform'
        )
        result = await db.execute(query)
        org = result.scalar_one_or_none()
        
        if not org:
            # Create Ekumen organization
            org = Organization(
                id=uuid.uuid4(),
                name='Ekumen Platform',
                legal_name='Ekumen SAS',
                siret='00000000000000',  # System organization
                organization_type='government_agency',
                status='active',
                description='Ekumen platform system organization for curated content'
            )
            db.add(org)
            await db.commit()
            await db.refresh(org)
        
        return org
    
    async def _get_or_create_ekumen_user(self, db: AsyncSession) -> User:
        """
        Get or create Ekumen system user
        """
        # Try to find existing Ekumen system user
        query = select(User).where(
            User.email == 'system@ekumen.fr'
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        
        if not user:
            # Create Ekumen system user
            user = User(
                id=uuid.uuid4(),
                email='system@ekumen.fr',
                full_name='Ekumen System',
                role=UserRole.ADMIN.value,  # Use .value to get string
                status=UserStatus.ACTIVE.value,  # Use .value to get string
                is_active=True,
                is_superuser=True,
                is_verified=True
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
        
        return user
    
    def _generate_ephy_content(self, product_data: Dict[str, Any]) -> str:
        """
        Generate content from EPHY product data
        """
        content = f"""
# Fiche Technique EPHY - {product_data.get('libelle', 'Produit')}

## Informations Générales
- **Nom du produit**: {product_data.get('libelle', 'N/A')}
- **Numéro AMM**: {product_data.get('numero_amm', 'N/A')}
- **Type d'intrant**: {product_data.get('type_intrant', 'N/A')}
- **Catégorie**: {product_data.get('categorie', 'N/A')}

## Composition
- **Substance active**: {product_data.get('substance_active', 'N/A')}
- **Concentration**: {product_data.get('concentration', 'N/A')}

## Utilisation
- **Cultures autorisées**: {product_data.get('cultures_autorisees', 'N/A')}
- **Dose d'emploi**: {product_data.get('dose_emploi', 'N/A')}
- **Période d'application**: {product_data.get('periode_application', 'N/A')}

## Sécurité
- **Délai de réentrée**: {product_data.get('delai_reentree', 'N/A')}
- **Délai avant récolte**: {product_data.get('delai_recolte', 'N/A')}
- **ZNT (Zone de Non Traitement)**: {product_data.get('znt', 'N/A')}

## Conditions d'utilisation
- **Conditions météorologiques**: {product_data.get('conditions_meteo', 'N/A')}
- **Équipement de protection**: {product_data.get('equipement_protection', 'N/A')}

## Notes importantes
{product_data.get('notes', 'Aucune note particulière')}

---
*Document généré automatiquement à partir des données EPHY*
*Date de génération: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        return content.strip()


# Global instance
content_pipeline_service = ContentPipelineService()
