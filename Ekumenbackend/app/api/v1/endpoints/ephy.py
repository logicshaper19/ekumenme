"""
EPHY data endpoints.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.models.ephy import Produit, SubstanceActive, UsageProduit
from app.schemas.ephy import ProduitResponse, SubstanceActiveResponse, UsageProduitResponse
import structlog

logger = structlog.get_logger()
router = APIRouter()


@router.get("/produits", response_model=List[ProduitResponse])
async def get_produits(
    type_produit: Optional[str] = Query(None, description="Product type (PPP or MFSC)"),
    etat_autorisation: Optional[str] = Query(None, description="Authorization status"),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get EPHY products with optional filtering."""
    query = db.query(Produit)
    
    if type_produit:
        query = query.filter(Produit.type_produit == type_produit)
    
    if etat_autorisation:
        query = query.filter(Produit.etat_autorisation == etat_autorisation)
    
    produits = query.offset(skip).limit(limit).all()
    return produits


@router.get("/produits/{numero_amm}", response_model=ProduitResponse)
async def get_produit(numero_amm: str, db: Session = Depends(get_db)):
    """Get a specific EPHY product by AMM number."""
    produit = db.query(Produit).filter(Produit.numero_amm == numero_amm).first()
    if not produit:
        raise HTTPException(status_code=404, detail="Product not found")
    return produit


@router.get("/substances-actives", response_model=List[SubstanceActiveResponse])
async def get_substances_actives(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db)
):
    """Get active substances."""
    substances = db.query(SubstanceActive).offset(skip).limit(limit).all()
    return substances


@router.get("/usages/{numero_amm}", response_model=List[UsageProduitResponse])
async def get_produit_usages(
    numero_amm: str,
    db: Session = Depends(get_db)
):
    """Get usages for a specific product."""
    usages = db.query(UsageProduit).filter(
        UsageProduit.numero_amm == numero_amm
    ).all()
    
    if not usages:
        raise HTTPException(status_code=404, detail="No usages found for this product")
    
    return usages


@router.get("/search")
async def search_produits(
    q: str = Query(..., description="Search query"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Search products by name or AMM number."""
    query = db.query(Produit).filter(
        (Produit.nom_produit.ilike(f"%{q}%")) |
        (Produit.numero_amm.ilike(f"%{q}%"))
    )
    
    produits = query.offset(skip).limit(limit).all()
    
    return {
        "query": q,
        "results": produits,
        "total": query.count()
    }
