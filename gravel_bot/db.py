"""
gravel_bot.db - Gestión de Base de Datos SQLite, Persistencia y Deduplicación de Alertas
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional
from gravel_bot.config import DB_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    c = conn.cursor()

    # Tabla tiendas
    c.execute("""
    CREATE TABLE IF NOT EXISTS tiendas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        nombre TEXT NOT NULL,
        tipo TEXT NOT NULL, -- fisica / online / ocasion_certificada
        direccion TEXT,
        distancia_km REAL,
        telefono TEXT,
        whatsapp TEXT,
        marcas TEXT,
        servicios TEXT,
        url TEXT
    );
    """)

    # Tabla bicicletas
    c.execute("""
    CREATE TABLE IF NOT EXISTS bicicletas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        slug TEXT UNIQUE NOT NULL,
        marca TEXT NOT NULL,
        modelo TEXT NOT NULL,
        ano INTEGER,
        disciplina TEXT NOT NULL, -- gravel / carretera / fitness / mtb
        transmision TEXT NOT NULL,
        tipo_transmision TEXT NOT NULL, -- 2x10, 2x11, 2x12, 1x10, 1x11, 1x12, etc.
        frenos TEXT NOT NULL,
        tipo_frenos TEXT NOT NULL, -- hidraulico / semihidraulico / mecanico_doble / mecanico_mono
        cuadro TEXT NOT NULL,
        horquilla TEXT NOT NULL,
        ejes TEXT NOT NULL,
        patilla_udh INTEGER DEFAULT 0,
        talla_recomendada_169 TEXT NOT NULL,
        precio_pvp REAL,
        precio_oferta REAL,
        tienda_id INTEGER REFERENCES tiendas(id),
        url_oferta TEXT,
        en_stock INTEGER DEFAULT 1,
        c1_frenos REAL,
        c2_transmision REAL,
        c3_cuadro REAL,
        c4_precio REAL,
        c5_talla REAL,
        puntuacion_total REAL,
        nota REAL,
        tier TEXT NOT NULL,
        notas_veredicto TEXT
    );
    """)

    # Tabla historial_precios
    c.execute("""
    CREATE TABLE IF NOT EXISTS historial_precios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bicicleta_id INTEGER REFERENCES bicicletas(id),
        tienda_id INTEGER REFERENCES tiendas(id),
        precio REAL NOT NULL,
        talla TEXT,
        en_stock INTEGER DEFAULT 1,
        url TEXT,
        fecha_registro TEXT NOT NULL,
        nota_adicional TEXT
    );
    """)

    # Tabla alertas_notificadas (para evitar SPAM en Telegram)
    c.execute("""
    CREATE TABLE IF NOT EXISTS alertas_notificadas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        bicicleta_id INTEGER REFERENCES bicicletas(id),
        precio_notificado REAL NOT NULL,
        tier TEXT NOT NULL,
        nota REAL NOT NULL,
        canal TEXT NOT NULL DEFAULT 'telegram',
        fecha_notificacion TEXT NOT NULL
    );
    """)

    conn.commit()
    conn.close()

def get_store_by_slug(slug: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM tiendas WHERE slug = ?", (slug,))
    row = c.fetchone()
    conn.close()
    return row

def get_or_create_store(slug: str, nombre: str, tipo: str = "online", url: str = "", direccion: str = "") -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM tiendas WHERE slug = ?", (slug,))
    row = c.fetchone()
    if row:
        store_id = row["id"]
    else:
        c.execute("""
        INSERT INTO tiendas (slug, nombre, tipo, url, direccion)
        VALUES (?, ?, ?, ?, ?)
        """, (slug, nombre, tipo, url, direccion))
        store_id = c.lastrowid
        conn.commit()
    conn.close()
    return store_id

def get_bike_by_slug(slug: str) -> Optional[sqlite3.Row]:
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM bicicletas WHERE slug = ?", (slug,))
    row = c.fetchone()
    conn.close()
    return row

def upsert_bike(b: Dict[str, Any]) -> int:
    """Inserta o actualiza una bicicleta en la base de datos."""
    conn = get_connection()
    c = conn.cursor()

    c.execute("SELECT id, precio_oferta FROM bicicletas WHERE slug = ?", (b["slug"],))
    existing = c.fetchone()

    if existing:
        bike_id = existing["id"]
        c.execute("""
        UPDATE bicicletas SET
            marca = ?, modelo = ?, ano = ?, disciplina = ?,
            transmision = ?, tipo_transmision = ?, frenos = ?, tipo_frenos = ?,
            cuadro = ?, horquilla = ?, ejes = ?, patilla_udh = ?,
            talla_recomendada_169 = ?, precio_pvp = ?, precio_oferta = ?,
            tienda_id = ?, url_oferta = ?, en_stock = ?,
            c1_frenos = ?, c2_transmision = ?, c3_cuadro = ?, c4_precio = ?, c5_talla = ?,
            puntuacion_total = ?, nota = ?, tier = ?, notas_veredicto = ?
        WHERE id = ?
        """, (
            b["marca"], b["modelo"], b.get("ano", 2025), b.get("disciplina", "gravel"),
            b["transmision"], b["tipo_transmision"], b["frenos"], b["tipo_frenos"],
            b["cuadro"], b["horquilla"], b.get("ejes", "Pasantes 12 mm"), b.get("patilla_udh", 0),
            b["talla_recomendada_169"], b.get("precio_pvp", b["precio_oferta"]), b["precio_oferta"],
            b.get("tienda_id"), b.get("url_oferta", ""), b.get("en_stock", 1),
            b["c1_frenos"], b["c2_transmision"], b["c3_cuadro"], b["c4_precio"], b["c5_talla"],
            b["puntuacion_total"], b["nota"], b["tier"], b.get("notas_veredicto", ""),
            bike_id
        ))
    else:
        c.execute("""
        INSERT INTO bicicletas (
            slug, marca, modelo, ano, disciplina,
            transmision, tipo_transmision, frenos, tipo_frenos,
            cuadro, horquilla, ejes, patilla_udh,
            talla_recomendada_169, precio_pvp, precio_oferta,
            tienda_id, url_oferta, en_stock,
            c1_frenos, c2_transmision, c3_cuadro, c4_precio, c5_talla,
            puntuacion_total, nota, tier, notas_veredicto
        ) VALUES (
            ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?
        )
        """, (
            b["slug"], b["marca"], b["modelo"], b.get("ano", 2025), b.get("disciplina", "gravel"),
            b["transmision"], b["tipo_transmision"], b["frenos"], b["tipo_frenos"],
            b["cuadro"], b["horquilla"], b.get("ejes", "Pasantes 12 mm"), b.get("patilla_udh", 0),
            b["talla_recomendada_169"], b.get("precio_pvp", b["precio_oferta"]), b["precio_oferta"],
            b.get("tienda_id"), b.get("url_oferta", ""), b.get("en_stock", 1),
            b["c1_frenos"], b["c2_transmision"], b["c3_cuadro"], b["c4_precio"], b["c5_talla"],
            b["puntuacion_total"], b["nota"], b["tier"], b.get("notas_veredicto", "")
        ))
        bike_id = c.lastrowid

    conn.commit()
    conn.close()
    return bike_id

def record_price(bike_id: int, store_id: Optional[int], price: float, size: str, in_stock: int, url: str, note: str = ""):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO historial_precios (bicicleta_id, tienda_id, precio, talla, en_stock, url, fecha_registro, nota_adicional)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (bike_id, store_id, price, size, in_stock, url, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), note))
    conn.commit()
    conn.close()

def was_alert_sent(bike_id: int, current_price: float) -> bool:
    """Verifica si ya se envió una alerta para esta bici a este precio o menor."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT precio_notificado FROM alertas_notificadas
    WHERE bicicleta_id = ? AND precio_notificado <= ?
    """, (bike_id, current_price))
    row = c.fetchone()
    conn.close()
    return row is not None

def mark_alert_sent(bike_id: int, price: float, tier: str, nota: float, canal: str = "telegram"):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO alertas_notificadas (bicicleta_id, precio_notificado, tier, nota, canal, fecha_notificacion)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (bike_id, price, tier, nota, canal, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def get_all_bikes(tier_filter: Optional[str] = None) -> List[sqlite3.Row]:
    conn = get_connection()
    c = conn.cursor()
    query = """
    SELECT b.*, t.nombre as tienda_nombre, t.tipo as tienda_tipo, t.distancia_km as tienda_distancia
    FROM bicicletas b
    LEFT JOIN tiendas t ON b.tienda_id = t.id
    """
    params = []
    if tier_filter:
        query += " WHERE b.tier LIKE ?"
        params.append(f"%{tier_filter}%")
    query += " ORDER BY b.puntuacion_total DESC, b.precio_oferta ASC"

    c.execute(query, params)
    rows = c.fetchall()
    conn.close()
    return rows

def get_deals(min_discount_pct: float = 15.0) -> List[sqlite3.Row]:
    conn = get_connection()
    c = conn.cursor()
    query = """
    SELECT b.*, t.nombre as tienda_nombre,
           ((b.precio_pvp - b.precio_oferta) / b.precio_pvp * 100) as descuento_pct,
           (b.precio_pvp - b.precio_oferta) as ahorro_eur
    FROM bicicletas b
    LEFT JOIN tiendas t ON b.tienda_id = t.id
    WHERE b.precio_pvp > b.precio_oferta
      AND ((b.precio_pvp - b.precio_oferta) / b.precio_pvp * 100) >= ?
    ORDER BY b.puntuacion_total DESC, descuento_pct DESC
    """
    c.execute(query, (min_discount_pct,))
    rows = c.fetchall()
    conn.close()
    return rows
