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
from gravel_bot.scrapers.multi_store import MultiStoreAggregatorScraper
from gravel_bot.scrapers.cicloscorredor import CiclosCorredorScraper
from gravel_bot.scrapers.bikestocks import BikestocksScraper
from gravel_bot.scrapers.buhobike import BuhobikeScraper
from gravel_bot.scrapers.alltricks import AlltricksScraper
from gravel_bot.scrapers.buycycle import BuycycleScraper
from gravel_bot.scrapers.canyon import CanyonOutletScraper
from gravel_bot.scrapers.bicispasaje import BicispasajeScraper
from gravel_bot.scrapers.bicimarket import BicimarketScraper
from gravel_bot.scrapers.bikediscount import BikeDiscountScraper
from gravel_bot.scrapers.decathlon import DecathlonScraper

ACTIVE_SCRAPERS: List[BaseScraper] = [
    MammothScraper(),
    SanferbikeScraper(),
    BuhobikeScraper(),
    CiclosCorredorScraper(),
    BikestocksScraper(),
    AlltricksScraper(),
    FabreguesScraper(),
    WallapopMadridScraper(),
    OutletAggregatorScraper(),
    ChollometroScraper(),
    MultiStoreAggregatorScraper(),
    BuycycleScraper(),
    CanyonOutletScraper(),
    BicispasajeScraper(),
    BicimarketScraper(),
    BikeDiscountScraper(),
    DecathlonScraper(),
]
def get_all_scrapers() -> List[BaseScraper]:
    return ACTIVE_SCRAPERS
