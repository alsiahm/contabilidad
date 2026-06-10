import psycopg2
from psycopg2.extras import RealDictCursor
from datetime import datetime
import os
from dotenv import load_dotenv
from supabase import create_client

def conectar_db():
    """Establece la conexión usando el Pooler de Supabase optimizado para IPv4."""
    return psycopg2.connect(
        host="aws-1-eu-central-1.pooler.supabase.com",
        port="5432",                                  # <- Pon aquí el puerto exacto que te pida tu panel (5432 o 6543)
        database="postgres",
        user="postgres.jiodhkgaycfvjoienkvx",         # Tu usuario compuesto de Supabase
        password="holamegustanlaspapas",                  # Tu contraseña limpia, SIN corchetes []
        sslmode="require"
    )
# ─────────────────────────────────────────
# CREACION DE TABLAS
# ─────────────────────────────────────────
def crear_tablas():
    conn = conectar_db()
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id SERIAL PRIMARY KEY,
        nombre_fiscal TEXT NOT NULL,
        cif_nif TEXT UNIQUE NOT NULL,
        direccion TEXT,
        email TEXT
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facturas (
        id SERIAL PRIMARY KEY,
        numero_factura TEXT UNIQUE NOT NULL,
        fecha TEXT NOT NULL,
        cliente_id INTEGER REFERENCES clientes(id),
        concepto TEXT NOT NULL,
        base_imponible REAL NOT NULL,
        porcentaje_igic REAL DEFAULT 7.0,
        importe_igic REAL NOT NULL,
        total REAL NOT NULL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gastos (
        id SERIAL PRIMARY KEY,
        numero_gasto TEXT UNIQUE NOT NULL,
        fecha TEXT NOT NULL,
        "proveedor_CIF" TEXT NOT NULL,
        concepto TEXT NOT NULL,
        importe REAL NOT NULL
    )""")

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS provisiones (
        id SERIAL PRIMARY KEY,
        numero_provision TEXT UNIQUE NOT NULL,
        fecha TEXT NOT NULL,
        cliente_id INTEGER REFERENCES clientes(id),
        concepto TEXT NOT NULL,
        importe REAL NOT NULL,
        factura_asociada TEXT DEFAULT NULL,
        aplicada INTEGER DEFAULT 0
    )""")

    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# CLIENTES
# ─────────────────────────────────────────

def agregar_cliente(nombre_fiscal, cif_nif, direccion="", email=""):
    conn = conectar_db()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO clientes (nombre_fiscal, cif_nif, direccion, email)
            VALUES (%s, %s, %s, %s)
        """, (nombre_fiscal, cif_nif, direccion, email))
        conn.commit()
        return True
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return False
    finally:
        conn.close()

def obtener_clientes():
    conn = conectar_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("SELECT id, nombre_fiscal, cif_nif, direccion, email FROM clientes ORDER BY nombre_fiscal")
    rows = cursor.fetchall()
    conn.close()
    return rows

def borrar_cliente(cliente_id):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE id = %s", (cliente_id,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# FACTURAS
# ─────────────────────────────────────────

def calcular_siguiente_factura():
    conn = conectar_db()
    cursor = conn.cursor()
    año_actual = datetime.now().strftime("%Y")
    cursor.execute("""
        SELECT numero_factura FROM facturas
        WHERE numero_factura LIKE %s
        ORDER BY id DESC LIMIT 1
    """, (f"FAC-{año_actual}-%",))
    ultimo = cursor.fetchone()
    conn.close()
    nuevo_num = int(ultimo[0].split("-")[-1]) + 1 if ultimo else 1
    return f"FAC-{año_actual}-{nuevo_num:04d}"

def agregar_factura(numero_factura, fecha, cliente_id, concepto, base_imponible, porcentaje_igic_=7.0):
    conn = conectar_db()
    cursor = conn.cursor()
    porcentaje_igic = porcentaje_igic_
    importe_igic = base_imponible * (porcentaje_igic / 100)
    total = base_imponible + importe_igic
    cursor.execute("""
        INSERT INTO facturas (numero_factura, fecha, cliente_id, concepto, base_imponible, porcentaje_igic, importe_igic, total)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (numero_factura, fecha, cliente_id, concepto, base_imponible, porcentaje_igic, importe_igic, total))
    conn.commit()
    conn.close()

def obtener_facturas_periodo(año=None, trimestre=None):
    conn = conectar_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    condiciones = []
    params = []
    if año:
        # fecha guardada como DD/MM/YYYY — extraemos año con substring
        condiciones.append("SUBSTRING(f.fecha, 7, 4) = %s")
        params.append(str(año))
    if trimestre:
        meses = {1: ('01','02','03'), 2: ('04','05','06'), 3: ('07','08','09'), 4: ('10','11','12')}
        condiciones.append("SUBSTRING(f.fecha, 4, 2) = ANY(%s)")
        params.append(list(meses[trimestre]))
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    cursor.execute(f"""
        SELECT f.numero_factura, f.fecha, c.nombre_fiscal AS cliente,
               f.base_imponible, f.porcentaje_igic, f.importe_igic, f.total
        FROM facturas f
        LEFT JOIN clientes c ON f.cliente_id = c.id
        {where}
        ORDER BY f.id DESC
    """, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def borrar_factura(numero_factura):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM facturas WHERE numero_factura = %s", (numero_factura,))
    conn.commit()
    conn.close()

def guardar_factura_bd(numero, fecha, cliente_id, concepto, base, igic_p, importe_igic, total):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO facturas (numero_factura, fecha, cliente_id, concepto, base_imponible, porcentaje_igic, importe_igic, total)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
    """, (numero, fecha, cliente_id, concepto, base, igic_p, importe_igic, total))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# GASTOS
# ─────────────────────────────────────────

def calcular_siguiente_gasto():
    conn = conectar_db()
    cursor = conn.cursor()
    año_actual = datetime.now().strftime("%Y")
    cursor.execute("""
        SELECT numero_gasto FROM gastos
        WHERE numero_gasto LIKE %s
        ORDER BY id DESC LIMIT 1
    """, (f"GAS-{año_actual}-%",))
    ultimo = cursor.fetchone()
    conn.close()
    nuevo_num = int(ultimo[0].split("-")[-1]) + 1 if ultimo else 1
    return f"GAS-{año_actual}-{nuevo_num:04d}"

def registrar_gasto(fecha, proveedor_cif, concepto, importe):
    conn = conectar_db()
    cursor = conn.cursor()
    n_gasto_id = calcular_siguiente_gasto()
    cursor.execute("""
        INSERT INTO gastos (numero_gasto, fecha, "proveedor_CIF", concepto, importe)
        VALUES (%s, %s, %s, %s, %s)
    """, (n_gasto_id, fecha, proveedor_cif, concepto, importe))
    conn.commit()
    conn.close()

def obtener_gastos():
    conn = conectar_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT numero_gasto, fecha, "proveedor_CIF" AS proveedor, concepto, importe
        FROM gastos
        ORDER BY id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def obtener_gastos_periodo(año=None, trimestre=None):
    conn = conectar_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    condiciones = []
    params = []
    if año:
        condiciones.append("SUBSTRING(fecha, 7, 4) = %s")
        params.append(str(año))
    if trimestre:
        meses = {1: ('01','02','03'), 2: ('04','05','06'), 3: ('07','08','09'), 4: ('10','11','12')}
        condiciones.append("SUBSTRING(fecha, 4, 2) = ANY(%s)")
        params.append(list(meses[trimestre]))
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    cursor.execute(f"""
        SELECT numero_gasto, fecha, "proveedor_CIF" AS proveedor, concepto, importe
        FROM gastos
        {where}
        ORDER BY id DESC
    """, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def borrar_gasto(numero_gasto):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM gastos WHERE numero_gasto = %s", (numero_gasto,))
    conn.commit()
    conn.close()


# ─────────────────────────────────────────
# PROVISIONES
# ─────────────────────────────────────────

def calcular_siguiente_provision():
    conn = conectar_db()
    cursor = conn.cursor()
    año_actual = datetime.now().strftime("%Y")
    cursor.execute("""
        SELECT numero_provision FROM provisiones
        WHERE numero_provision LIKE %s
        ORDER BY id DESC LIMIT 1
    """, (f"PRO-{año_actual}-%",))
    ultimo = cursor.fetchone()
    conn.close()
    nuevo_num = int(ultimo[0].split("-")[-1]) + 1 if ultimo else 1
    return f"PRO-{año_actual}-{nuevo_num:04d}"

def registrar_provision(fecha, cliente_id, concepto, importe, factura_asociada=None):
    conn = conectar_db()
    cursor = conn.cursor()
    numero = calcular_siguiente_provision()
    cursor.execute("""
        INSERT INTO provisiones (numero_provision, fecha, cliente_id, concepto, importe, factura_asociada)
        VALUES (%s, %s, %s, %s, %s, %s)
    """, (numero, fecha, cliente_id, concepto, importe, factura_asociada))
    conn.commit()
    conn.close()

def obtener_provisiones():
    conn = conectar_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT p.numero_provision, p.fecha, c.nombre_fiscal AS cliente,
               p.concepto, p.importe, p.factura_asociada, p.aplicada
        FROM provisiones p
        LEFT JOIN clientes c ON p.cliente_id = c.id
        ORDER BY p.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def obtener_provisiones_pendientes(cliente_id):
    conn = conectar_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cursor.execute("""
        SELECT id, numero_provision, concepto, importe
        FROM provisiones
        WHERE cliente_id = %s AND aplicada = 0
        ORDER BY id ASC
    """, (cliente_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def marcar_provisiones_aplicadas(ids_provisiones, numero_factura):
    conn = conectar_db()
    cursor = conn.cursor()
    for pid in ids_provisiones:
        cursor.execute("""
            UPDATE provisiones
            SET aplicada = 1, factura_asociada = %s
            WHERE id = %s
        """, (numero_factura, pid))
    conn.commit()
    conn.close()

def obtener_provisiones_periodo(año=None, trimestre=None):
    conn = conectar_db()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    condiciones = []
    params = []
    if año:
        condiciones.append("SUBSTRING(p.fecha, 7, 4) = %s")
        params.append(str(año))
    if trimestre:
        meses = {1: ('01','02','03'), 2: ('04','05','06'), 3: ('07','08','09'), 4: ('10','11','12')}
        condiciones.append("SUBSTRING(p.fecha, 4, 2) = ANY(%s)")
        params.append(list(meses[trimestre]))
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    cursor.execute(f"""
        SELECT p.numero_provision, p.fecha, c.nombre_fiscal AS cliente,
               p.concepto, p.importe, p.factura_asociada, p.aplicada
        FROM provisiones p
        LEFT JOIN clientes c ON p.cliente_id = c.id
        {where}
        ORDER BY p.id DESC
    """, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def borrar_provision(numero_provision):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM provisiones WHERE numero_provision = %s", (numero_provision,))
    conn.commit()
    conn.close()