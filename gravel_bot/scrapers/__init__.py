"""
gravel_bot.scrapers - Registro de Scrapers de Tiendas
"""

from typing import List
from gravel_bot.scrapers.base import BaseScraper
from gravel_bot.scrapers.fabregues import FabreguesScraper
from gravel_bot.scrapers.mammoth import MammothScraper
from gravel_bot.scrapers.sanferbike import SanferbikeScraper
from gravel_bot.scrapers.wallapop import WallapopMadridScraper
from gravel_bot.scrapers.outlets import OutletAggregatorScraper
from gravel_bot.scrapers.chollometro import ChollometroScraper
from gravel_bot.scrapers.bikediscount import BikeDiscountScraper
from gravel_bot.scrapers.decathlon import DecathlonScraper
from gravel_bot.scrapers.bicimarket import BicimarketScraper
from gravel_bot.scrapers.canyon import CanyonOutletScraper
from gravel_bot.scrapers.bicispasaje import BicispasajeScraper

ACTIVE_SCRAPERS: List[BaseScraper] = [
    DecathlonScraper(),
    BikeDiscountScraper(),
    BicimarketScraper(),
    CanyonOutletScraper(),
    BicispasajeScraper(),
    SanferbikeScraper(),
    FabreguesScraper(),
    MammothScraper(),
    WallapopMadridScraper(),
    OutletAggregatorScraper(),
    ChollometroScraper(),
]

def get_all_scrapers() -> List[BaseScraper]:
    return ACTIVE_SCRAPERS
