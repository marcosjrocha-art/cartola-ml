from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.services.team_generator import gerar_time
from app.services.backtest_service import run_backtest
from app.core.simple_cache import get as cache_get, set as cache_set

router = APIRouter(prefix="/api")

class GerarTimeRequest(BaseModel):
    cartoletas: float = Field(..., ge=0, le=500)
    formacao: str = Field(..., min_length=3, max_length=5)

@router.get("/health")
def health():
    return {"status": "ok"}

@router.post("/gerar-time")
def gerar_time_endpoint(body: GerarTimeRequest):
    return gerar_time(body)

@router.get("/backtest/resumo")
def backtest_resumo(
    cartoletas: float = Query(200.0, ge=0, le=500),
    formacao: str = Query("4-3-3"),
    top_k: int = Query(20, ge=5, le=100),
    min_train_rounds: int = Query(5, ge=1, le=30),
):
    cache_key = f"bt:TOTAL:{cartoletas}:{formacao}:{top_k}:{min_train_rounds}"
    cached = cache_get(cache_key)
    if cached is not None:
        return cached

    result = run_backtest(
        cartoletas=float(cartoletas),
        formacao=formacao,
        top_k=int(top_k),
        min_train_rounds=int(min_train_rounds),
    )

    cache_set(cache_key, result, ttl_seconds=15 * 60)  # 15 minutos
    return result
