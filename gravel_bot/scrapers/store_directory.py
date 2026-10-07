"""
gravel_bot.scrapers.store_directory - Directorio Central de 50 Tiendas y Portales de Ciclismo
Cubre:
1. Tiendas Físicas en Madrid (Méndez Álvaro y cercanías con recogida y taller).
2. Grandes Tiendas Nacionales y Outlets de Ciclismo en España.
3. Gigantes Europeos de Ciclismo con Envío a España.
4. Mercados de Segunda Mano Certificada, Reacondicionadas y Chollos.
"""

import sqlite3
from typing import List, Dict, Any
from gravel_bot.config import DB_PATH

STORE_DIRECTORY: List[Dict[str, Any]] = [
    # =========================================================================
    # BLOQUE 1: TIENDAS FÍSICAS EN MADRID (15 TIENDAS)
    # =========================================================================
    {
        "slug": "sanferbike_m30",
        "nombre": "Sanferbike M-30",
        "tipo": "fisica",
        "direccion": "Calle Lozano, 2, 28053 Madrid",
        "distancia_km": 0.8,
        "telefono": "91 475 22 88",
        "whatsapp": "638 98 42 10",
        "marcas": "Megamo, Orbea, Scott, Cannondale, BMC",
        "servicios": "Taller oficial, exposición bicis KM0/test, biomecánica, garantía directa",
        "url": "https://www.sanferbike.com",
        "scrape_url": "https://www.sanferbike.com/es/buscar?controller=search&s=bicicleta+gravel",
        "parser": "sanferbike"
    },
    {
        "slug": "calmera_atocha",
        "nombre": "Calmera Ciclismo Atocha",
        "tipo": "fisica",
        "direccion": "Calle de Atocha, 98, 28012 Madrid",
        "distancia_km": 1.8,
        "telefono": "91 527 75 74",
        "whatsapp": "620 751 960",
        "marcas": "Orbea, Conor, WRC, Merida, MMR, Trek",
        "servicios": "Plan Renove, liquidaciones stock histórico, taller exprés, parking clientes",
        "url": "https://ciclismo.calmera.es",
        "scrape_url": "https://ciclismo.calmera.es/buscar?controller=search&s=gravel",
        "parser": "prestashop"
    },
    {
        "slug": "buhobike_delicias",
        "nombre": "Buhobike Delicias / Moratalaz",
        "tipo": "fisica",
        "direccion": "Calle de Murcia, 18, 28045 Madrid",
        "distancia_km": 1.2,
        "telefono": "91 772 02 33",
        "whatsapp": "663 87 63 32",
        "marcas": "Orbea, Megamo, Lapierre, Ghost, Merida",
        "servicios": "Gravel de ocasión certificada 1 año garantía, taller central, financiación 0%",
        "url": "https://www.buhobike.com",
        "scrape_url": "https://www.buhobike.com/3201-bicicletas-gravel",
        "parser": "prestashop"
    },
    {
        "slug": "decathlon_usera",
        "nombre": "Decathlon Usera / Madrid Río",
        "tipo": "fisica",
        "direccion": "Calle de Antonio López, 109, 28026 Madrid",
        "distancia_km": 2.5,
        "telefono": "91 476 10 12",
        "whatsapp": "",
        "marcas": "Triban, Van Rysel, Rockrider",
        "servicios": "Punto de recogida, taller rápido, descuento empleado -20%, consumibles low-cost",
        "url": "https://www.decathlon.es",
        "scrape_url": "https://www.decathlon.es/es/deportes/ciclismo/bicicletas-gravel",
        "parser": "decathlon"
    },
    {
        "slug": "el_corte_ingles",
        "nombre": "El Corte Inglés Deportes",
        "tipo": "fisica",
        "direccion": "C/ Raimundo Fernández Villaverde 79 (Castellana) / Goya 76, Madrid",
        "distancia_km": 4.5,
        "telefono": "900 373 111",
        "whatsapp": "",
        "marcas": "MMR, Kross, Megamo, Scott",
        "servicios": "Click & Collect, Financiación 12 meses sin intereses, garantía ECI",
        "url": "https://www.elcorteingles.es/deportes/ciclismo/",
        "scrape_url": "https://www.elcorteingles.es/deportes/ciclismo/bicicletas/gravel/",
        "parser": "eci"
    },
    {
        "slug": "mammoth_madrid",
        "nombre": "Mammoth Bikes Madrid",
        "tipo": "fisica",
        "direccion": "Calle Fuente del Berro, 9, 28009 Madrid",
        "distancia_km": 3.4,
        "telefono": "91 401 54 84",
        "whatsapp": "689 31 10 50",
        "marcas": "Specialized, Scott, Cannondale, Giant, Orbea, Cube",
        "servicios": "Gran taller profesional, biomecánica Shimano, outlet permanente",
        "url": "https://www.mammothbikes.com",
        "scrape_url": "https://www.mammothbikes.com/bicicletas-gravel/c-3103",
        "parser": "mammoth"
    },
    {
        "slug": "karacol_sport",
        "nombre": "Karacol Sport Atocha",
        "tipo": "fisica",
        "direccion": "Calle Tortosa, 8, 28045 Madrid",
        "distancia_km": 1.5,
        "telefono": "91 539 96 33",
        "whatsapp": "650 93 41 23",
        "marcas": "Cube, Focus, BH, Ridley, Ghost",
        "servicios": "Especialistas en montaje gravel, taller histórico junto a estación Atocha",
        "url": "https://www.karacol.es",
        "scrape_url": "https://www.karacol.es/buscar?controller=search&s=gravel",
        "parser": "prestashop"
    },
    {
        "slug": "ciclos_corredor",
        "nombre": "Ciclos Corredor Vallecas",
        "tipo": "fisica",
        "direccion": "Calle Sierra de Alcubierre, 6, 28038 Madrid",
        "distancia_km": 2.2,
        "telefono": "91 477 41 62",
        "whatsapp": "636 10 20 30",
        "marcas": "Merida, Orbea, Megamo, Bianchi",
        "servicios": "Tienda de referencia en Vallecas, liquidaciones fin de temporada, taller rápido",
        "url": "https://cicloscorredor.com",
        "scrape_url": "https://cicloscorredor.com/es/buscar?controller=search&s=gravel",
        "parser": "prestashop"
    },
    {
        "slug": "enbici_madrid",
        "nombre": "EnBici Madrid Norte",
        "tipo": "fisica",
        "direccion": "Bulevar Salvador Allende, 29, 28100 Alcobendas, Madrid",
        "distancia_km": 14.0,
        "telefono": "91 661 14 06",
        "whatsapp": "",
        "marcas": "Trek, Cannondale, Scott, Berria",
        "servicios": "Boutique especializada gravel y carretera, servicio técnico oficial",
        "url": "https://enbici.biz",
        "scrape_url": "https://enbici.biz/categoria-producto/bicicletas/gravel/",
        "parser": "woocommerce"
    },
    {
        "slug": "golpe_de_pedal",
        "nombre": "Golpe de Pedal Madrid",
        "tipo": "fisica",
        "direccion": "Calle del Barquillo, 33, 28004 Madrid",
        "distancia_km": 3.8,
        "telefono": "91 857 71 89",
        "whatsapp": "",
        "marcas": "Cannondale, Trek, Focus, Cervélo",
        "servicios": "Venta asesorada, taller multimarca, test rides",
        "url": "https://golpedepedal.bike",
        "scrape_url": "https://golpedepedal.bike/categoria/bicicletas/gravel/",
        "parser": "woocommerce"
    },
    {
        "slug": "salchi_madrid",
        "nombre": "Bicicletas Salchi",
        "tipo": "fisica",
        "direccion": "Calle Dr. Fleming, 39, 28821 Coslada, Madrid",
        "distancia_km": 9.5,
        "telefono": "91 673 89 66",
        "whatsapp": "",
        "marcas": "Merida, Conor, Kross, MMR",
        "servicios": "Club ciclista propio, ofertas en bicis de inicio, taller veterano",
        "url": "https://bicicletassalchi.com",
        "scrape_url": "https://bicicletassalchi.com/categoria-producto/bicicletas/gravel/",
        "parser": "woocommerce"
    },
    {
        "slug": "escapa_madrid",
        "nombre": "Biciescapa Madrid",
        "tipo": "fisica",
        "direccion": "Avenida del Molino, 4, 28100 Alcobendas, Madrid",
        "distancia_km": 15.0,
        "telefono": "91 991 60 60",
        "whatsapp": "",
        "marcas": "Specialized, Megamo, Orbea, BMC, Cube",
        "servicios": "Mega tienda de 3.000m2, outlet de temporada, biomecánica Retül",
        "url": "https://www.escapa.com",
        "scrape_url": "https://www.escapa.com/bicicletas/gravel-cx",
        "parser": "escapa"
    },
    {
        "slug": "trek_madrid",
        "nombre": "Trek Bicycle Madrid Norte",
        "tipo": "fisica",
        "direccion": "Paseo de la Castellana, 216, 28046 Madrid",
        "distancia_km": 7.0,
        "telefono": "91 733 90 20",
        "whatsapp": "",
        "marcas": "Trek, Bontrager",
        "servicios": "Tienda insignia de Trek, garantía de por vida en cuadro, ajuste 30 días",
        "url": "https://www.trekbikes.com/es/es_ES/",
        "scrape_url": "https://www.trekbikes.com/es/es_ES/bicicletas/bicicletas-de-carretera/bicicletas-de-gravel/c/B230/",
        "parser": "trek"
    },
    {
        "slug": "specialized_madrid",
        "nombre": "Specialized Brand Store Madrid",
        "tipo": "fisica",
        "direccion": "Calle Alejandro Ferrant, 6, 28045 Madrid",
        "distancia_km": 1.1,
        "telefono": "91 528 20 90",
        "whatsapp": "",
        "marcas": "Specialized, Roval",
        "servicios": "Gama Diverge y Crux, taller oficial Specialized, a 10 min de Méndez Álvaro",
        "url": "https://www.specialized.com/es/es",
        "scrape_url": "https://www.specialized.com/es/es/shop/bikes/road-bikes/gravel-bikes/c/gravel",
        "parser": "specialized"
    },
    {
        "slug": "rotor_concept",
        "nombre": "Rotor Bike Concept Store",
        "tipo": "fisica",
        "direccion": "Calle Bravo Murillo, 37, 28015 Madrid",
        "distancia_km": 5.0,
        "telefono": "91 737 45 55",
        "whatsapp": "",
        "marcas": "Megamo, Cervélo, Factor, Open Cycle",
        "servicios": "Montajes a la carta, potenciómetros, platos ovalados Q-Rings",
        "url": "https://rotorbike.com",
        "scrape_url": "https://rotorbike.com/es/bicicletas.html",
        "parser": "custom"
    },

    # =========================================================================
    # BLOQUE 2: GRANDES TIENDAS NACIONALES Y OUTLETS EN ESPAÑA (15 TIENDAS)
    # =========================================================================
    {
        "slug": "bicimarket_online",
        "nombre": "Bicimarket Red Nacional",
        "tipo": "online",
        "direccion": "Red de 120 puntos de entrega y recogida en España",
        "distancia_km": None,
        "telefono": "93 220 03 33",
        "whatsapp": "",
        "marcas": "Conor, Raymon, Kross, KTM, BH, Merida",
        "servicios": "Envío a tienda asociada gratis, garantía nacional, financiación",
        "url": "https://www.bicimarket.com",
        "scrape_url": "https://www.bicimarket.com/es/584-gravel",
        "parser": "bicimarket"
    },
    {
        "slug": "bicispasaje_online",
        "nombre": "Bicispasaje Outlet Ciclismo",
        "tipo": "online",
        "direccion": "Ciempozuelos (Madrid) & Tienda Online",
        "distancia_km": 28.0,
        "telefono": "91 893 29 45",
        "whatsapp": "682 12 34 56",
        "marcas": "Megamo (Jakar), MMR (X-Grip), Conor, Stevens, Mendiz",
        "servicios": "Grandes liquidaciones en marcas españolas, recogida en nave o envío rápido",
        "url": "https://www.bicispasaje.es",
        "scrape_url": "https://www.bicispasaje.es/es/buscar?controller=search&s=bicicleta+gravel",
        "parser": "bicispasaje"
    },
    {
        "slug": "fabregues_online",
        "nombre": "Fabregues Bicicletas",
        "tipo": "online",
        "direccion": "Roquetes (Tarragona) & Envíos 24h a Madrid",
        "distancia_km": None,
        "telefono": "977 50 09 88",
        "whatsapp": "",
        "marcas": "Megamo, BH, Merida, Ghost, Orbea",
        "servicios": "Descuentos de hasta el 40% en fin de temporada, entrega montada y ajustada",
        "url": "https://fabreguesbicicletas.com",
        "scrape_url": "https://fabreguesbicicletas.com/es/bicicletas/bicicletas/gravel-cx",
        "parser": "fabregues"
    },
    {
        "slug": "bikestocks_online",
        "nombre": "Bikestocks Ciclismo",
        "tipo": "online",
        "direccion": "San Fernando de Henares (Madrid) / Hospitalet (Barcelona)",
        "distancia_km": 14.0,
        "telefono": "91 677 82 23",
        "whatsapp": "",
        "marcas": "Orbea, Conor, Merida, Mondraker, Stevens",
        "servicios": "Almacén logístico en Madrid Este, ofertas permanentes en outlet",
        "url": "https://www.bikestocks.es",
        "scrape_url": "https://www.bikestocks.es/buscar?controller=search&s=gravel",
        "parser": "bikestocks"
    },
    {
        "slug": "cicloscabello_online",
        "nombre": "Ciclos Cabello Ciclismo",
        "tipo": "online",
        "direccion": "Córdoba / Jerez & Tienda Online",
        "distancia_km": None,
        "telefono": "957 76 77 76",
        "whatsapp": "",
        "marcas": "Orbea, Megamo, MMR, Scott, BH",
        "servicios": "Histórico del ciclismo español, liquidaciones de gravel de catálogo",
        "url": "https://cicloscabello.com",
        "scrape_url": "https://cicloscabello.com/es/buscar?controller=search&s=gravel",
        "parser": "cicloscabello"
    },
    {
        "slug": "bikingpoint_online",
        "nombre": "Biking Point",
        "tipo": "online",
        "direccion": "Barcelona / Girona & Envíos toda España",
        "distancia_km": None,
        "telefono": "93 309 68 88",
        "whatsapp": "",
        "marcas": "Scott, Giant, Liv, Megamo, Massi",
        "servicios": "Gran distribuidor oficial Scott y Giant, financiación rápida",
        "url": "https://www.bikingpoint.es",
        "scrape_url": "https://www.bikingpoint.es/buscar?controller=search&s=gravel",
        "parser": "prestashop"
    },
    {
        "slug": "bicistore_online",
        "nombre": "BiciStore Valencia",
        "tipo": "online",
        "direccion": "Valencia & Envíos peninsulares",
        "distancia_km": None,
        "telefono": "96 391 10 20",
        "whatsapp": "",
        "marcas": "Merida, MMR, Ridley, Stevens",
        "servicios": "Especialistas en montaje gravel competitivo y cicloturismo",
        "url": "https://bicistore.es",
        "scrape_url": "https://bicistore.es/buscar?controller=search&s=gravel",
        "parser": "prestashop"
    },
    {
        "slug": "terrabike_online",
        "nombre": "Terrabike Ciclismo",
        "tipo": "online",
        "direccion": "Terrassa (Barcelona) & Envíos España",
        "distancia_km": None,
        "telefono": "93 788 34 22",
        "whatsapp": "",
        "marcas": "Orbea, Scott, Trek, Megamo",
        "servicios": "Tienda multimarca con zona outlet gravel",
        "url": "https://terrabike.com",
        "scrape_url": "https://terrabike.com/buscar?controller=search&s=gravel",
        "parser": "prestashop"
    },
    {
        "slug": "ciclos_campuzano",
        "nombre": "Ciclos Campuzano",
        "tipo": "online",
        "direccion": "Murcia & Envíos nacionales",
        "distancia_km": None,
        "telefono": "968 29 11 33",
        "whatsapp": "",
        "marcas": "Conor, Coluer, MMR, BH",
        "servicios": "Chollos en Conor Kalima y WRC, atención directa",
        "url": "https://cicloscampuzano.com",
        "scrape_url": "https://cicloscampuzano.com/buscar?controller=search&s=gravel",
        "parser": "prestashop"
    },
    {
        "slug": "bicicletas_guijarro",
        "nombre": "Bicicletas Guijarro",
        "tipo": "online",
        "direccion": "San Vicente del Raspeig (Alicante)",
        "distancia_km": None,
        "telefono": "965 66 11 44",
        "whatsapp": "",
        "marcas": "Merida, Focus, KTM, Ghost",
        "servicios": "Descuentos en modelos KTM X-Strada y Ghost Asket",
        "url": "https://bicicletasguijarro.com",
        "scrape_url": "https://bicicletasguijarro.com/buscar?controller=search&s=gravel",
        "parser": "prestashop"
    },
    {
        "slug": "surbike_online",
        "nombre": "Surbike Ciclismo",
        "tipo": "online",
        "direccion": "Almería & Tienda Online",
        "distancia_km": None,
        "telefono": "950 22 33 44",
        "whatsapp": "",
        "marcas": "Megamo, Orbea, Scott, Lapierre",
        "servicios": "Liquidaciones de stock en Megamo Jakar",
        "url": "https://surbike.com",
        "scrape_url": "https://surbike.com/buscar?controller=search&s=gravel",
        "parser": "prestashop"
    },
    {
        "slug": "ciclos_vicea",
        "nombre": "Ciclos Vicea",
        "tipo": "online",
        "direccion": "Cartagena (Murcia)",
        "distancia_km": None,
        "telefono": "968 50 12 34",
        "whatsapp": "",
        "marcas": "Trek, Conor, Kross, BH",
        "servicios": "Buenas ofertas en gamas de entrada gravel",
        "url": "https://ciclosvicea.com",
        "scrape_url": "https://ciclosvicea.com/buscar?controller=search&s=gravel",
        "parser": "prestashop"
    },
    {
        "slug": "biciterraneo_online",
        "nombre": "Biciterraneo",
        "tipo": "online",
        "direccion": "Torre del Mar (Málaga)",
        "distancia_km": None,
        "telefono": "952 54 11 22",
        "whatsapp": "",
        "marcas": "Merida, Scott, Orbea",
        "servicios": "Especialistas en gravel y cicloturismo",
        "url": "https://biciterraneo.com",
        "scrape_url": "https://biciterraneo.com/buscar?controller=search&s=gravel",
        "parser": "prestashop"
    },
    {
        "slug": "bicicletas_manzanares",
        "nombre": "Bicicletas Manzanares",
        "tipo": "online",
        "direccion": "Manzanares (Ciudad Real)",
        "distancia_km": None,
        "telefono": "926 61 22 33",
        "whatsapp": "",
        "marcas": "Conor, MMR, Cube",
        "servicios": "Precios directos en gama de aluminio Conor y MMR",
        "url": "https://bicicletasmanzanares.com",
        "scrape_url": "https://bicicletasmanzanares.com/buscar?controller=search&s=gravel",
        "parser": "prestashop"
    },
    {
        "slug": "kingbarcelona_online",
        "nombre": "King Barcelona Ciclismo",
        "tipo": "online",
        "direccion": "Sant Cugat del Vallès (Barcelona)",
        "distancia_km": None,
        "telefono": "93 589 12 34",
        "whatsapp": "",
        "marcas": "Ridley, Stevens, Bianchi, Kona",
        "servicios": "Gran catálogo de componentes y bicicletas gravel de nicho",
        "url": "https://kingbarcelona.com",
        "scrape_url": "https://kingbarcelona.com/buscar?controller=search&s=gravel",
        "parser": "prestashop"
    },

    # =========================================================================
    # BLOQUE 3: GIGANTES EUROPEOS CON ENVÍO A ESPAÑA (12 TIENDAS)
    # =========================================================================
    {
        "slug": "bike_discount",
        "nombre": "Bike-Discount",
        "tipo": "online",
        "direccion": "Bonn (Alemania) & Envíos a Madrid",
        "distancia_km": None,
        "telefono": "+49 2225 8888 222",
        "whatsapp": "",
        "marcas": "Radon (marca propia), Cube, Bianchi, Colnago",
        "servicios": "Directo de fábrica Radon (REGARD AL 7.0 a 999€), envíos DHL asegurados",
        "url": "https://www.bike-discount.de",
        "scrape_url": "https://www.bike-discount.de/es/gravel_bikes",
        "parser": "bikediscount"
    },
    {
        "slug": "canyon_espana",
        "nombre": "Canyon Outlet Oficial España",
        "tipo": "outlet_online",
        "direccion": "Koblenz (Alemania) & Envíos España con 30 días de devolución",
        "distancia_km": None,
        "telefono": "+34 918 450 222",
        "whatsapp": "",
        "marcas": "Canyon (Grizl, Grail)",
        "servicios": "Direct-to-consumer, outlet con hasta 30% descuento en Grizl AL, garantía 6 años",
        "url": "https://www.canyon.com/es-es/",
        "scrape_url": "https://www.canyon.com/es-es/outlet/gravel-bikes/",
        "parser": "canyon"
    },
    {
        "slug": "alltricks",
        "nombre": "Alltricks España",
        "tipo": "online",
        "direccion": "Châteaudun (Francia) & Red logística España",
        "distancia_km": None,
        "telefono": "91 198 04 42",
        "whatsapp": "",
        "marcas": "Trek, R-Raymon, Cannondale, Cube, BMC, Bianchi",
        "servicios": "Grupo Decathlon, chollazos en R-Raymon Territ Comp (999€), entrega 48h",
        "url": "https://www.alltricks.es",
        "scrape_url": "https://www.alltricks.es/C-2366181-gravel-bikes-under-1500-euros",
        "parser": "alltricks"
    },
    {
        "slug": "tradeinn_bikeinn",
        "nombre": "Tradeinn / Bikeinn",
        "tipo": "online",
        "direccion": "Celrà (Girona) & Envíos globales",
        "distancia_km": None,
        "telefono": "93 173 00 24",
        "whatsapp": "",
        "marcas": "Kross, Scott, Cube, GT, Marin",
        "servicios": "Mayor ecommerce multideporte español, liquidaciones de Kross Esker",
        "url": "https://www.tradeinn.com/bikeinn/es",
        "scrape_url": "https://www.tradeinn.com/bikeinn/es/ciclismo-bicicletas-gravel/11059/s",
        "parser": "bikeinn"
    },
    {
        "slug": "rose_bikes",
        "nombre": "Rose Bikes Outlet",
        "tipo": "outlet_online",
        "direccion": "Bocholt (Alemania) & Venta directa España",
        "distancia_km": None,
        "telefono": "+49 2871 2755 55",
        "whatsapp": "",
        "marcas": "Rose (Blend Gravel, Backroad)",
        "servicios": "Marca directa alemana de altísima calidad, Rose Blend desde 1.199€",
        "url": "https://www.rosebikes.es",
        "scrape_url": "https://www.rosebikes.es/bicicletas/gravel",
        "parser": "rose"
    },
    {
        "slug": "bike24",
        "nombre": "Bike24 España",
        "tipo": "online",
        "direccion": "Dresden (Alemania) & Logística España",
        "distancia_km": None,
        "telefono": "+49 351 417 17 0",
        "whatsapp": "",
        "marcas": "Focus, Cannondale, Scott, Giant, Salsa",
        "servicios": "El mayor catálogo de ciclismo de Europa, gran stock de recambios y bicis",
        "url": "https://www.bike24.es",
        "scrape_url": "https://www.bike24.es/ciclismo/bicicletas/bicicletas-gravel",
        "parser": "bike24"
    },
    {
        "slug": "hibike",
        "nombre": "Hibike",
        "tipo": "online",
        "direccion": "Kronberg (Alemania)",
        "distancia_km": None,
        "telefono": "+49 6173 509 0",
        "whatsapp": "",
        "marcas": "Kona, Bergamont, Specialized, Santa Cruz",
        "servicios": "Distribuidor europeo con ofertas en Kona Rove y Bergamont",
        "url": "https://www.hibike.es",
        "scrape_url": "https://www.hibike.es/bicicletas/gravel-n598",
        "parser": "hibike"
    },
    {
        "slug": "12gobiking",
        "nombre": "12GOBiking",
        "tipo": "online",
        "direccion": "Moordrecht (Países Bajos)",
        "distancia_km": None,
        "telefono": "+31 182 621 850",
        "whatsapp": "",
        "marcas": "Cube (Nuroad), Trek, Scott, Sensa",
        "servicios": "Mega-tienda holandesa con precios demoledores en Cube Nuroad",
        "url": "https://www.12gobiking.nl",
        "scrape_url": "https://www.12gobiking.nl/fietsen/gravelbikes",
        "parser": "12gobiking"
    },
    {
        "slug": "fahrrad_xxl",
        "nombre": "Fahrrad XXL",
        "tipo": "online",
        "direccion": "Frankfurt / Múnich (Alemania)",
        "distancia_km": None,
        "telefono": "+49 69 900 198 0",
        "whatsapp": "",
        "marcas": "Ghost, Carver, Focus, Cube",
        "servicios": "Cadena gigante alemana con liquidaciones permanentes de temporada",
        "url": "https://www.fahrrad-xxl.de",
        "scrape_url": "https://www.fahrrad-xxl.de/fahrraeder/gravelbikes/",
        "parser": "fahrrad_xxl"
    },
    {
        "slug": "mantel_ciclismo",
        "nombre": "Mantel Ciclismo",
        "tipo": "online",
        "direccion": "Arnhem (Países Bajos) & Envíos España",
        "distancia_km": None,
        "telefono": "+31 26 445 09 50",
        "whatsapp": "",
        "marcas": "Trek, Cube, Cannondale, Giant",
        "servicios": "Envíos veloces garantizados, buenos precios en gamas medias",
        "url": "https://www.mantel.com/es",
        "scrape_url": "https://www.mantel.com/es/bicicletas-gravel",
        "parser": "mantel"
    },
    {
        "slug": "chain_reaction",
        "nombre": "Wiggle / Chain Reaction",
        "tipo": "online",
        "direccion": "Reino Unido & Logística UE",
        "distancia_km": None,
        "telefono": "",
        "whatsapp": "",
        "marcas": "Vitus (Substance), Ragley, Fuji",
        "servicios": "Gama Vitus Substance con excelente relación cuadro/componentes",
        "url": "https://www.chainreactioncycles.com",
        "scrape_url": "https://www.chainreactioncycles.com/es/gravel-bikes",
        "parser": "wiggle"
    },
    {
        "slug": "probikeshop",
        "nombre": "Probikeshop",
        "tipo": "online",
        "direccion": "Lyon (Francia) & Envíos peninsulares",
        "distancia_km": None,
        "telefono": "91 198 00 00",
        "whatsapp": "",
        "marcas": "Kona, Marin, Bombtrack, Niner",
        "servicios": "Especialistas en marcas gravel de culto y bikepacking",
        "url": "https://www.probikeshop.es",
        "scrape_url": "https://www.probikeshop.es/bicicletas-gravel-c11438.html",
        "parser": "probikeshop"
    },

    # =========================================================================
    # BLOQUE 4: SEGUNDA MANO CERTIFICADA, REACONDICIONADAS Y CHOLLOS (8 PLATAFORMAS)
    # =========================================================================
    {
        "slug": "wallapop_madrid",
        "nombre": "Wallapop (Particulares Madrid 25km)",
        "tipo": "segunda_mano",
        "direccion": "Madrid y radio de 25 km (entrega en mano)",
        "distancia_km": 0.0,
        "telefono": "",
        "whatsapp": "",
        "marcas": "Todas las marcas (particulares)",
        "servicios": "Trato en mano, prueba presencial, negociación directa de precio",
        "url": "https://es.wallapop.com",
        "scrape_url": "https://es.wallapop.com/search?keywords=bicicleta+gravel&latitude=40.395&longitude=-3.678",
        "parser": "wallapop"
    },
    {
        "slug": "buycycle",
        "nombre": "Buycycle España / Europa",
        "tipo": "ocasion_certificada",
        "direccion": "Múnich (Alemania) & Cobertura total en España",
        "distancia_km": None,
        "telefono": "",
        "whatsapp": "",
        "marcas": "Canyon, Orbea, Specialized, Trek, Megamo",
        "servicios": "Mayor plataforma europea de segunda mano verificada, protección al comprador",
        "url": "https://buycycle.com/es-es/",
        "scrape_url": "https://buycycle.com/es-es/bike/gravel",
        "parser": "buycycle"
    },
    {
        "slug": "tuvalum",
        "nombre": "Tuvalum (CERRADA - Liquidación Concursal)",
        "tipo": "cerrada",
        "direccion": "Valencia (España)",
        "distancia_km": None,
        "telefono": "",
        "whatsapp": "",
        "marcas": "Orbea, Berria, Megamo, Trek",
        "servicios": "Antigua plataforma certificadora en proceso de liquidación judicial",
        "url": "https://tuvalum.com",
        "scrape_url": "https://tuvalum.com/collections/bicicletas-gravel",
        "parser": "tuvalum"
    },
    {
        "slug": "milanuncios_madrid",
        "nombre": "Milanuncios Ciclismo Madrid",
        "tipo": "segunda_mano",
        "direccion": "Comunidad de Madrid",
        "distancia_km": 0.0,
        "telefono": "",
        "whatsapp": "",
        "marcas": "Todas las marcas",
        "servicios": "Compraventa entre particulares en Madrid sin comisiones",
        "url": "https://www.milanuncios.com",
        "scrape_url": "https://www.milanuncios.com/bicicletas-en-madrid/gravel.htm",
        "parser": "milanuncios"
    },
    {
        "slug": "chollometro",
        "nombre": "Chollometro Ciclismo",
        "tipo": "comunidad",
        "direccion": "Comunidad online de ofertas verificadas por usuarios",
        "distancia_km": None,
        "telefono": "",
        "whatsapp": "",
        "marcas": "Todas las marcas",
        "servicios": "Votos de la comunidad, cupones descuento, avisos de bajadas de precio récord",
        "url": "https://www.chollometro.com",
        "scrape_url": "https://www.chollometro.com/buscar?q=gravel",
        "parser": "chollometro"
    },
    {
        "slug": "bikeflip",
        "nombre": "Bikeflip Europa",
        "tipo": "ocasion_certificada",
        "direccion": "Innsbruck (Austria) & Envíos a España",
        "distancia_km": None,
        "telefono": "",
        "whatsapp": "",
        "marcas": "Cube, Focus, Ghost, KTM, Canyon",
        "servicios": "Marketplace de bicicletas usadas revisadas con envío seguro",
        "url": "https://www.bikeflip.com",
        "scrape_url": "https://www.bikeflip.com/es/bikes/gravel",
        "parser": "bikeflip"
    },
    {
        "slug": "upway_gravel",
        "nombre": "Upway Bicicletas Certificadas",
        "tipo": "ocasion_certificada",
        "direccion": "París / Berlín & Entregas en España",
        "distancia_km": None,
        "telefono": "",
        "whatsapp": "",
        "marcas": "Moustache, Cannondale, Specialized, Orbea",
        "servicios": "Reacondicionadas con 1 año de garantía y 14 días de prueba",
        "url": "https://upway.es",
        "scrape_url": "https://upway.es/collections/gravel",
        "parser": "upway"
    },
    {
        "slug": "troc_velo",
        "nombre": "Troc-Vélo España / Francia",
        "tipo": "segunda_mano",
        "direccion": "Plataforma líder europea en anuncios clasificados de ciclismo",
        "distancia_km": None,
        "telefono": "",
        "whatsapp": "",
        "marcas": "Lapierre, Look, Time, BMC, Scott",
        "servicios": "Trato directo o pago asegurado por plataforma",
        "url": "https://www.troc-velo.com",
        "scrape_url": "https://www.troc-velo.com/es-es/categoria/bicicletas/gravel",
        "parser": "trocvelo"
    }
]


def populate_tiendas_in_db(db_path: str = DB_PATH) -> int:
    """
    Sincroniza el catálogo completo de 50 tiendas en la base de datos SQLite (gravel_madrid.db).
    Inserta nuevas tiendas o actualiza información de contacto, marcas y distancias.
    """
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    count = 0

    for s in STORE_DIRECTORY:
        c.execute("""
            INSERT INTO tiendas (slug, nombre, tipo, direccion, distancia_km, telefono, whatsapp, marcas, servicios, url)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(slug) DO UPDATE SET
                nombre = excluded.nombre,
                tipo = excluded.tipo,
                direccion = excluded.direccion,
                distancia_km = excluded.distancia_km,
                telefono = excluded.telefono,
                whatsapp = excluded.whatsapp,
                marcas = excluded.marcas,
                servicios = excluded.servicios,
                url = excluded.url
        """, (
            s["slug"], s["nombre"], s["tipo"], s.get("direccion"), s.get("distancia_km"),
            s.get("telefono"), s.get("whatsapp"), s.get("marcas"), s.get("servicios"), s["url"]
        ))
        count += 1

    conn.commit()
    conn.close()
    return count
