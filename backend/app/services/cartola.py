import requests
from cachetools import TTLCache

cache = TTLCache(maxsize=10, ttl=900)

def get_rodada_atual():
    if "rodada" in cache:
        return cache["rodada"]

    r = requests.get("https://api.cartola.globo.com/mercado/status")
    r.raise_for_status()
    data = r.json()
    cache["rodada"] = data
    return data
