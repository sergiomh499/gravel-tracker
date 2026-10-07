"""
gravel_bot.db - Gestión de Base de Datos SQLite, Persistencia y Deduplicación de Alertas
"""

import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from contextlib import contextmanager
from gravel_bot.config import DB_PATH

def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

@contextmanager
def db_session():
    """Context manager para transacciones SQLite seguras con auto-commit y cierre garantizado."""
    conn = get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
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

    # Tabla usuarios (multiusuario para Telegram Bot)
    c.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_chat_id INTEGER UNIQUE NOT NULL,
        telegram_username TEXT,
        fecha_registro TEXT NOT NULL,
        activo INTEGER DEFAULT 1
    );
    """)

    # Tabla perfiles_ciclista (personalización individual)
    c.execute("""
    CREATE TABLE IF NOT EXISTS perfiles_ciclista (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER UNIQUE REFERENCES usuarios(id),
        estatura_cm INTEGER NOT NULL DEFAULT 169,
        talla_calculada TEXT NOT NULL DEFAULT 'S',
        presupuesto_max REAL NOT NULL DEFAULT 1000.0,
        holgura_max_pct REAL NOT NULL DEFAULT 15.0, -- % margen extra para chollos excepcionales
        preferencia_transmision TEXT DEFAULT '2x', -- '2x', '1x', 'indiferente'
        terreno_asfalto_pct INTEGER DEFAULT 50,    -- 50% asfalto / 50% tierra
        zona TEXT DEFAULT 'Madrid',
        alertas_activas INTEGER DEFAULT 1,
        nota_minima_alerta REAL DEFAULT 8.5
    );
    """)
    # Migración en caliente de columna holgura si la base ya existe
    try:
        c.execute("ALTER TABLE perfiles_ciclista ADD COLUMN holgura_max_pct REAL DEFAULT 15.0")
    except Exception:
        pass

    # Tabla alertas_por_usuario (para evitar enviar duplicados al mismo usuario)
    c.execute("""
    CREATE TABLE IF NOT EXISTS alertas_por_usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER REFERENCES usuarios(id),
        bicicleta_id INTEGER REFERENCES bicicletas(id),
        precio_notificado REAL NOT NULL,
        fecha_notificacion TEXT NOT NULL
    );
    """)
    # Tabla alertas_talla_usuario (notificaciones de reposición de talla específica)
    c.execute("""
    CREATE TABLE IF NOT EXISTS alertas_talla_usuario (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario_id INTEGER REFERENCES usuarios(id),
        termino_modelo TEXT NOT NULL,
        talla_deseada TEXT NOT NULL,
        activa INTEGER DEFAULT 1,
        fecha_creacion TEXT NOT NULL
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

def clean_model_name(marca: str, modelo: str) -> str:
    """Limpia 'Bicicleta', repeticiones de marca y espacios redundantes del nombre de modelo."""
    import re
    m = modelo.strip()
    m = re.sub(r'^(bicicleta\s+el[eé]ctrica|bicicleta\s+de\s+gravel|bicicleta)\s+', '', m, flags=re.IGNORECASE)
    marca_pattern = r'^' + re.escape(marca.strip()) + r'\s+'
    m = re.sub(marca_pattern, '', m, flags=re.IGNORECASE)
    m = re.sub(marca_pattern, '', m, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', m).strip()

def upsert_bike(b: Dict[str, Any]) -> int:
    """Inserta o actualiza una bicicleta en la base de datos garantizando deduplicación estricta."""
    conn = get_connection()
    c = conn.cursor()

    clean_mod = clean_model_name(b["marca"], b["modelo"])
    b["modelo"] = clean_mod

    # Buscar coincidencia exacta por slug O por combinación (marca, modelo limpio)
    c.execute("""
        SELECT id, precio_oferta FROM bicicletas 
        WHERE slug = ? OR (LOWER(marca) = LOWER(?) AND LOWER(modelo) = LOWER(?))
    """, (b["slug"], b["marca"], clean_mod))
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

def record_price_if_changed(bike_id: int, store_id: Optional[int], price: float, size: str = "", in_stock: int = 1, url: str = "", note: str = "") -> bool:
    """
    Registra una entrada en el historial de precios sólo si el precio ha variado o es el primer registro.
    Evita duplicados redundantes del mismo precio en cada ciclo de rastreo.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT precio, en_stock FROM historial_precios
    WHERE bicicleta_id = ?
    ORDER BY id DESC LIMIT 1
    """, (bike_id,))
    last = c.fetchone()
    
    should_record = False
    if not last or abs(last["precio"] - price) >= 0.5 or last["en_stock"] != in_stock:
        should_record = True
        c.execute("""
        INSERT INTO historial_precios (bicicleta_id, tienda_id, precio, talla, en_stock, url, fecha_registro, nota_adicional)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (bike_id, store_id, price, size, in_stock, url, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), note))
        conn.commit()
    conn.close()
    return should_record

def get_bike_price_history(identifier: Any) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Recupera una bicicleta (por id o por slug/nombre) y toda su secuencia cronológica de precios.
    """
    conn = get_connection()
    c = conn.cursor()
    
    if isinstance(identifier, int) or (isinstance(identifier, str) and identifier.isdigit()):
        c.execute("SELECT * FROM bicicletas WHERE id = ?", (int(identifier),))
    else:
        c.execute("""
        SELECT * FROM bicicletas 
        WHERE slug = ? OR LOWER(modelo) LIKE ? OR LOWER(marca || ' ' || modelo) LIKE ?
        ORDER BY id ASC LIMIT 1
        """, (str(identifier), f"%{str(identifier).lower()}%", f"%{str(identifier).lower()}%"))
        
    bike_row = c.fetchone()
    if not bike_row:
        conn.close()
        return None, []
        
    bike_data = dict(bike_row)
    c.execute("""
    SELECT h.*, t.nombre as tienda_nombre, t.url as tienda_url
    FROM historial_precios h
    LEFT JOIN tiendas t ON h.tienda_id = t.id
    WHERE h.bicicleta_id = ?
    ORDER BY h.fecha_registro ASC
    """, (bike_data["id"],))
    history_rows = c.fetchall()
    conn.close()
    return bike_data, [dict(r) for r in history_rows]
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
# -------------------------------------------------------------
# Métodos Multiusuario y Perfiles de Ciclista
# -------------------------------------------------------------

def get_or_create_user(chat_id: int, username: Optional[str] = None) -> int:
    """Registra o recupera el ID interno de un usuario de Telegram."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM usuarios WHERE telegram_chat_id = ?", (chat_id,))
    row = c.fetchone()
    if row:
        user_id = row["id"]
        if username:
            c.execute("UPDATE usuarios SET telegram_username = ? WHERE id = ?", (username, user_id))
            conn.commit()
    else:
        c.execute("""
        INSERT INTO usuarios (telegram_chat_id, telegram_username, fecha_registro, activo)
        VALUES (?, ?, ?, 1)
        """, (chat_id, username or "", datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
        user_id = c.lastrowid

        # Crear perfil por defecto (Sergio - Méndez Álvaro, 1,69 m, S, 1350 €, 2x, 50/50)
        c.execute("""
        INSERT INTO perfiles_ciclista (
            usuario_id, estatura_cm, talla_calculada, presupuesto_max,
            preferencia_transmision, terreno_asfalto_pct, zona, alertas_activas, nota_minima_alerta
        ) VALUES (?, 169, 'S', 1350.0, '2x', 50, 'Madrid', 1, 8.5)
        """, (user_id,))
        conn.commit()

    conn.close()
    return user_id

def get_user_profile(chat_id_or_user_id: int) -> Optional[sqlite3.Row]:
    """Obtiene el perfil de ciclista por telegram_chat_id o por usuario_id interno."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT p.*, u.telegram_chat_id, u.telegram_username
    FROM perfiles_ciclista p
    JOIN usuarios u ON p.usuario_id = u.id
    WHERE u.telegram_chat_id = ?
    LIMIT 1
    """, (chat_id_or_user_id,))
    row = c.fetchone()
    if not row:
        c.execute("""
        SELECT p.*, u.telegram_chat_id, u.telegram_username
        FROM perfiles_ciclista p
        JOIN usuarios u ON p.usuario_id = u.id
        WHERE u.id = ?
        LIMIT 1
        """, (chat_id_or_user_id,))
        row = c.fetchone()
    conn.close()
    return row
def update_user_profile(chat_id_or_user_id: int, **kwargs) -> Optional[sqlite3.Row]:
    """Actualiza campos específicos del perfil ciclista por telegram_chat_id o usuario_id."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT id FROM usuarios WHERE telegram_chat_id = ? LIMIT 1", (chat_id_or_user_id,))
    u_row = c.fetchone()
    if not u_row:
        c.execute("SELECT id FROM usuarios WHERE id = ? LIMIT 1", (chat_id_or_user_id,))
        u_row = c.fetchone()
    conn.close()
    if u_row:
        user_id = u_row[0]
    else:
        user_id = get_or_create_user(chat_id_or_user_id)
    if "estatura_cm" in kwargs and "talla_calculada" not in kwargs:
        from gravel_bot.evaluator import calcular_talla_desde_estatura
        kwargs["talla_calculada"] = calcular_talla_desde_estatura(kwargs["estatura_cm"])
    allowed_fields = [
        "estatura_cm", "talla_calculada", "presupuesto_max", "holgura_max_pct",
        "preferencia_transmision", "terreno_asfalto_pct", "zona",
        "alertas_activas", "nota_minima_alerta"
    ]
    updates = []
    params = []
    for k, v in kwargs.items():
            updates.append(f"{k} = ?")
            params.append(v)

    if not updates:
        return get_user_profile(chat_id_or_user_id)
    params.append(user_id)
    conn = get_connection()
    c = conn.cursor()
    query = f"UPDATE perfiles_ciclista SET {', '.join(updates)} WHERE usuario_id = ?"
    c.execute(query, params)
    conn.commit()
    conn.close()
    return get_user_profile(chat_id_or_user_id)
def get_all_active_profiles() -> List[sqlite3.Row]:
    """Devuelve todos los perfiles de usuarios con alertas activas para el pipeline de escaneo."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT p.*, u.telegram_chat_id, u.telegram_username
    FROM perfiles_ciclista p
    JOIN usuarios u ON p.usuario_id = u.id
    WHERE u.activo = 1 AND p.alertas_activas = 1
    """)
    rows = c.fetchall()
    conn.close()
    return rows

def was_alert_sent_to_user(usuario_id: int, bike_id: int, current_price: float) -> bool:
    """Comprueba si un usuario concreto ya fue notificado de una oferta a este precio o menor."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT precio_notificado FROM alertas_por_usuario
    WHERE usuario_id = ? AND bicicleta_id = ? AND precio_notificado <= ?
    """, (usuario_id, bike_id, current_price))
    row = c.fetchone()
    conn.close()
    return row is not None

def mark_alert_sent_to_user(usuario_id: int, bike_id: int, price: float):
    """Registra que una alerta ya ha sido entregada a un usuario específico."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO alertas_por_usuario (usuario_id, bicicleta_id, precio_notificado, fecha_notificacion)
    VALUES (?, ?, ?, ?)
    """, (usuario_id, bike_id, price, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

def add_size_alert(user_id: int, model_term: str, size: str) -> int:
    """Crea una alerta de reposición de talla para un modelo concreto."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    INSERT INTO alertas_talla_usuario (usuario_id, termino_modelo, talla_deseada, activa, fecha_creacion)
    VALUES (?, ?, ?, 1, ?)
    """, (user_id, model_term.strip().lower(), size.strip().upper(), datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    alert_id = c.lastrowid
    conn.commit()
    conn.close()
    return alert_id

def get_user_size_alerts(user_id: int) -> List[sqlite3.Row]:
    """Obtiene las alertas activas de talla para un usuario."""
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
    SELECT * FROM alertas_talla_usuario
    WHERE usuario_id = ? AND activa = 1
    ORDER BY id DESC
    """, (user_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_size_alert(alert_id: int, user_id: int) -> bool:
    """Desactiva una alerta de reposición de talla."""
    with db_session() as conn:
        c = conn.cursor()
        c.execute("""
        UPDATE alertas_talla_usuario SET activa = 0
        WHERE id = ? AND usuario_id = ?
        """, (alert_id, user_id))
        return c.rowcount > 0

def purge_obsolete_and_junior_models() -> Dict[str, int]:
    """
    Purga automáticamente registros no deseados en la base de datos:
    - Bicicletas junior / infantiles / niños
    - Modelos de disciplinas incompatibles o artefactos de test
    - Slugs huérfanos con marca 'Desconocida'
    """
    with db_session() as conn:
        c = conn.cursor()
        c.execute("""
            SELECT id FROM bicicletas
            WHERE disciplina IN ('junior', 'infantil', 'test_artifact')
               OR LOWER(modelo) LIKE '%junior%'
               OR LOWER(modelo) LIKE '%niño%'
               OR LOWER(modelo) LIKE '%infantil%'
               OR marca = 'Desconocida'
        """)
        rows = c.fetchall()
        bad_ids = [r[0] for r in rows]
        if not bad_ids:
            return {"purged_bikes": 0, "purged_prices": 0}

        placeholders = ','.join('?' for _ in bad_ids)
        c.execute(f"DELETE FROM historial_precios WHERE bicicleta_id IN ({placeholders})", bad_ids)
        purged_prices = c.rowcount
        c.execute(f"DELETE FROM alertas_notificadas WHERE bicicleta_id IN ({placeholders})", bad_ids)
        c.execute(f"DELETE FROM alertas_por_usuario WHERE bicicleta_id IN ({placeholders})", bad_ids)
        c.execute(f"DELETE FROM bicicletas WHERE id IN ({placeholders})", bad_ids)
        purged_bikes = c.rowcount
        return {"purged_bikes": purged_bikes, "purged_prices": purged_prices}
