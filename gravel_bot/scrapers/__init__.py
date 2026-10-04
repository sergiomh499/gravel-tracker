"""
gravel_bot.scrapers - Registro de Scrapers de Tiendas
"""

from typing import List, Type
from gravel_bot.scrapers.base import BaseScraper
from gravel_bot.scrapers.fabregues import FabreguesScraper
from gravel_bot.scrapers.mammoth import MammothScraper
from gravel_bot.scrapers.sanferbike import SanferbikeScraper
from gravel_bot.scrapers.wallapop import WallapopMadridScraper

ACTIVE_SCRAPERS: List[BaseScraper] = [
    SanferbikeScraper(),
    FabreguesScraper(),
    MammothScraper(),
    WallapopMadridScraper(),
]

def get_all_scrapers() -> List[BaseScraper]:
    return ACTIVE_SCRAPERS
