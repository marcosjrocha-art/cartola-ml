from pydantic import BaseModel, Field

class TeamRequest(BaseModel):
    cartoletas: float = Field(gt=0)
    formacao: str
