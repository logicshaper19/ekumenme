"""
Products API endpoints
Handles French agricultural product database operations
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional
import logging

from app.core.database import get_async_db
from app.models.user import User
from app.schemas.product import (
    ProductSearchRequest, ProductResponse, ProductUsageResponse,
    ProductCompatibilityResponse, ProductStatisticsResponse,
    CropStatisticsResponse, SubstanceStatisticsResponse,
    ProductValidationRequest, ProductCompatibilityRequest
)
from app.services.shared.auth_service import AuthService
from app.services.infrastructure.product_service import ProductService

logger = logging.getLogger(__name__)

router = APIRouter()
auth_service = AuthService()
product_service = ProductService()

@router.get("/search", response_model=List[ProductResponse])
async def search_products(
    search_term: Optional[str] = Query(None, description="Terme de recherche"),
    product_type: Optional[str] = Query(None, description="Type de produit (MFSC ou PPP)"),
    crop_filter: Optional[str] = Query(None, description="Filtre par culture"),
    limit: int = Query(50, ge=1, le=1000, description="Nombre maximum de résultats"),
    offset: int = Query(0, ge=0, description="Décalage pour la pagination"),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Rechercher des produits agricoles autorisés
    
    Args:
        search_term: Terme de recherche (nom produit, AMM, substance)
        product_type: Type de produit (MFSC ou PPP)
        crop_filter: Filtre par culture
        limit: Nombre maximum de résultats
        offset: Décalage pour la pagination
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        List[ProductResponse]: Liste des produits correspondants
    """
    try:
        from app.models.product import ProductType
        
        product_type_enum = None
        if product_type:
            try:
                product_type_enum = ProductType(product_type.upper())
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Type de produit invalide. Utilisez 'MFSC' ou 'PPP'"
                )
        
        products = await product_service.search_products(
            db=db,
            search_term=search_term,
            product_type=product_type_enum,
            crop_filter=crop_filter,
            limit=limit,
            offset=offset
        )
        
        return products
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Product search error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la recherche de produits"
        )

@router.get("/amm/{numero_amm}", response_model=ProductResponse)
async def get_product_by_amm(
    numero_amm: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtenir un produit par son numéro AMM
    
    Args:
        numero_amm: Numéro AMM du produit
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        ProductResponse: Détails du produit
    """
    try:
        product = await product_service.get_product_by_amm(db, numero_amm)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produit avec le numéro AMM {numero_amm} non trouvé"
            )
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get product by AMM error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du produit"
        )

@router.get("/name/{nom_produit}", response_model=ProductResponse)
async def get_product_by_name(
    nom_produit: str,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtenir un produit par son nom
    
    Args:
        nom_produit: Nom du produit
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        ProductResponse: Détails du produit
    """
    try:
        product = await product_service.get_product_by_name(db, nom_produit)
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Produit avec le nom '{nom_produit}' non trouvé"
            )
        
        return product
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get product by name error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération du produit"
        )

@router.get("/substance/{substance_name}", response_model=List[ProductResponse])
async def get_products_by_substance(
    substance_name: str,
    limit: int = Query(50, ge=1, le=1000),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtenir les produits contenant une substance active spécifique
    
    Args:
        substance_name: Nom de la substance active
        limit: Nombre maximum de résultats
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        List[ProductResponse]: Liste des produits contenant la substance
    """
    try:
        products = await product_service.get_products_by_substance(
            db=db,
            substance_name=substance_name,
            limit=limit
        )
        
        return products
        
    except Exception as e:
        logger.error(f"Get products by substance error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des produits par substance"
        )

@router.get("/crop/{crop_name}", response_model=List[ProductResponse])
async def get_products_for_crop(
    crop_name: str,
    limit: int = Query(50, ge=1, le=1000),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtenir les produits autorisés pour une culture spécifique
    
    Args:
        crop_name: Nom de la culture
        limit: Nombre maximum de résultats
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        List[ProductResponse]: Liste des produits autorisés pour la culture
    """
    try:
        products = await product_service.get_products_for_crop(
            db=db,
            crop_name=crop_name,
            limit=limit
        )
        
        return products
        
    except Exception as e:
        logger.error(f"Get products for crop error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des produits pour la culture"
        )

@router.post("/validate-usage", response_model=ProductUsageResponse)
async def validate_product_usage(
    validation_request: ProductValidationRequest,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Valider l'utilisation d'un produit pour une culture et une dose
    
    Args:
        validation_request: Données de validation
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        ProductUsageResponse: Résultat de la validation
    """
    try:
        result = await product_service.validate_product_usage(
            db=db,
            numero_amm=validation_request.numero_amm,
            crop_name=validation_request.crop_name,
            dose=validation_request.dose,
            unit=validation_request.unit
        )
        
        return ProductUsageResponse(**result)
        
    except Exception as e:
        logger.error(f"Product usage validation error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la validation de l'utilisation du produit"
        )

@router.post("/check-compatibility", response_model=ProductCompatibilityResponse)
async def check_product_compatibility(
    compatibility_request: ProductCompatibilityRequest,
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Vérifier la compatibilité entre deux produits
    
    Args:
        compatibility_request: Données de vérification de compatibilité
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        ProductCompatibilityResponse: Résultat de la vérification de compatibilité
    """
    try:
        result = await product_service.check_product_compatibility(
            db=db,
            product1_amm=compatibility_request.product1_amm,
            product2_amm=compatibility_request.product2_amm
        )
        
        return ProductCompatibilityResponse(**result)
        
    except Exception as e:
        logger.error(f"Product compatibility check error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la vérification de compatibilité des produits"
        )

@router.get("/statistics", response_model=ProductStatisticsResponse)
async def get_product_statistics(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtenir les statistiques de la base de données des produits
    
    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        ProductStatisticsResponse: Statistiques des produits
    """
    try:
        stats = await product_service.get_product_statistics(db)
        
        return ProductStatisticsResponse(**stats)
        
    except Exception as e:
        logger.error(f"Get product statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des statistiques"
        )

@router.get("/statistics/crops", response_model=List[CropStatisticsResponse])
async def get_crop_statistics(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtenir les statistiques par culture
    
    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        List[CropStatisticsResponse]: Statistiques par culture
    """
    try:
        stats = await product_service.get_crop_statistics(db)
        
        return [CropStatisticsResponse(**stat) for stat in stats]
        
    except Exception as e:
        logger.error(f"Get crop statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des statistiques par culture"
        )

@router.get("/statistics/substances", response_model=List[SubstanceStatisticsResponse])
async def get_substance_statistics(
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtenir les statistiques par substance active
    
    Args:
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        List[SubstanceStatisticsResponse]: Statistiques par substance active
    """
    try:
        stats = await product_service.get_substance_statistics(db)
        
        return [SubstanceStatisticsResponse(**stat) for stat in stats]
        
    except Exception as e:
        logger.error(f"Get substance statistics error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des statistiques par substance"
        )

@router.get("/buffer-zones", response_model=List[ProductResponse])
async def get_products_with_buffer_zones(
    limit: int = Query(50, ge=1, le=1000),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtenir les produits nécessitant des zones de non-traitement (ZNT)
    
    Args:
        limit: Nombre maximum de résultats
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        List[ProductResponse]: Liste des produits avec ZNT
    """
    try:
        products = await product_service.get_products_with_buffer_zones(
            db=db,
            limit=limit
        )
        
        return products
        
    except Exception as e:
        logger.error(f"Get products with buffer zones error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des produits avec ZNT"
        )

@router.get("/holder/{titulaire}", response_model=List[ProductResponse])
async def get_products_by_holder(
    titulaire: str,
    limit: int = Query(50, ge=1, le=1000),
    current_user: User = Depends(auth_service.get_current_user),
    db: AsyncSession = Depends(get_async_db)
):
    """
    Obtenir les produits par titulaire (entreprise)
    
    Args:
        titulaire: Nom du titulaire
        limit: Nombre maximum de résultats
        current_user: Utilisateur authentifié
        db: Session de base de données
        
    Returns:
        List[ProductResponse]: Liste des produits du titulaire
    """
    try:
        products = await product_service.get_products_by_holder(
            db=db,
            titulaire=titulaire,
            limit=limit
        )
        
        return products
        
    except Exception as e:
        logger.error(f"Get products by holder error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erreur lors de la récupération des produits par titulaire"
        )
