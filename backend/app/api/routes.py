from fastapi import APIRouter
from app.services.cartola import get_rodada_atual
from app.services.team_generator import gerar_time
from app.schemas.team import TeamRequest

router = APIRouter()

@router.get("/api/rodada-atual")
def rodada():
    return get_rodada_atual()

@router.post("/api/gerar-time")
def gerar(req: TeamRequest):
    return gerar_time(req)
