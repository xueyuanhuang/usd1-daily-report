"""Protocol adapters for fetching USD1 market data."""

from typing import Callable
from src.schema import Row

# Import adapters
from src.adapters.wlfi import fetch_row as wlfi_fetch
from src.adapters.echelon import fetch_row as echelon_fetch
from src.adapters.justlend import fetch_row as justlend_fetch
from src.adapters.kamino import fetch_row as kamino_fetch
from src.adapters.lista import fetch_row as lista_fetch


# Registry of protocol adapters
# Maps display name -> fetch function
ADAPTERS: dict[str, Callable[[float, bool], Row]] = {
    "WLFI Markets": wlfi_fetch,
    "Echelon": echelon_fetch,
    "JustLend": justlend_fetch,
    "Kamino": kamino_fetch,
    "Lista": lista_fetch,
}


def get_adapter_names() -> list[str]:
    """Get list of available adapter names."""
    return list(ADAPTERS.keys())
