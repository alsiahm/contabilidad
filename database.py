import sqlite3
from datetime import datetime

def conectar_db():
    conexion = sqlite3.connect("contabilidad.db")
    return conexion

def crear_tablas():
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    # 1. TABLA DE CLIENTES
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS clientes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre_fiscal TEXT NOT NULL,
        cif_nif TEXT UNIQUE NOT NULL,
        direccion TEXT,
        email TEXT

    )""")
    
    # 2. TABLA Ingresos
    # Aquí se registra lo que le cobras al cliente por el servicio.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS facturas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_factura TEXT UNIQUE NOT NULL, -- Ej: FAC-2026-0001
        fecha TEXT NOT NULL,
        cliente_id INTEGER,
        concepto TEXT NOT NULL,              -- El servicio prestado
        base_imponible REAL NOT NULL,
        porcentaje_igic REAL DEFAULT 7.0,    -- IGIC cobrado al cliente
        importe_igic REAL NOT NULL,
        total REAL NOT NULL,
        FOREIGN KEY(cliente_id) REFERENCES clientes(id)
    )""")
    
    # 3. TABLA DE GASTOS DE LA EMPRESA
    # Totalmente independiente.
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS gastos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        numero_gasto TEXT UNIQUE NOT NULL, -- Ej: GAS-2026-0001
        fecha TEXT NOT NULL,
        proveedor_CIF TEXT NOT NULL,             -- A quién le compras
        concepto TEXT NOT NULL,              -- Qué compras (Ej: "Suscripción Adobe")
        importe REAL NOT NULL
    )""")
    
    conexion.commit()
    conexion.close()
    crear_tabla_provisiones()  # Creamos la tabla de provisiones al iniciar la app

def agregar_cliente(nombre_fiscal, cif_nif, direccion="", email=""):
    conexion = conectar_db()
    cursor = conexion.cursor()
    try:
        cursor.execute("""
        INSERT INTO clientes (nombre_fiscal, cif_nif, direccion, email)
        VALUES (?, ?, ?, ?)
        """, (nombre_fiscal, cif_nif, direccion, email))
        conexion.commit()
        return True
    except sqlite3.IntegrityError:
        print(f"Error: El CIF/NIF '{cif_nif}' ya existe en la base de datos.")
        return False
    finally:
        conexion.close()

def agregar_factura(numero_factura, fecha, cliente_id, concepto, base_imponible, porcentaje_igic_=7.0):
    conexion = conectar_db()
    cursor = conexion.cursor()
    
    porcentaje_igic = porcentaje_igic_
    importe_igic = base_imponible * (porcentaje_igic / 100)
    total = base_imponible + importe_igic
    
    cursor.execute("""
    INSERT INTO facturas (numero_factura, fecha, cliente_id, concepto, base_imponible, porcentaje_igic, importe_igic, total)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (numero_factura, fecha, cliente_id, concepto, base_imponible, porcentaje_igic, importe_igic, total))
    
    conexion.commit()
    conexion.close()

def obtener_clientes():
    conn = conectar_db()
    # ESTA LÍNEA ES LA MAGIA: Activa el modo diccionario para las filas
    conn.row_factory = sqlite3.Row 
    cursor = conn.cursor()
    
    # Traemos explícitamente todos los campos necesarios
    cursor.execute("SELECT id, nombre_fiscal, cif_nif, direccion, email FROM clientes")
    clientes = cursor.fetchall()
    conn.close()
    return clientes

def calcular_facturacion_total():
    conexion = conectar_db()
    cursor = conexion.cursor()
    cursor.execute("SELECT SUM(total) FROM facturas")
    total_facturado = cursor.fetchone()[0] or 0.0
    conexion.close()
    return total_facturado

# ... (las funciones anteriores quedan igual) ...

def calcular_siguiente_factura():
    # Toda esta lógica debe llevar 4 espacios de sangrado respecto al margen izquierdo
    conn = conectar_db()
    cursor = conn.cursor()
    año_actual = datetime.now().strftime("%Y")
    
    cursor.execute("""
        SELECT numero_factura FROM facturas 
        WHERE numero_factura LIKE ? 
        ORDER BY id DESC LIMIT 1
    """, (f"FAC-{año_actual}-%",))
    
    ultimo_registro = cursor.fetchone()
    conn.close()
    
    if ultimo_registro:
        ultimo_num = int(ultimo_registro[0].split("-")[-1])
        nuevo_num = ultimo_num + 1
    else:
        nuevo_num = 1
        
    return f"FAC-{año_actual}-{nuevo_num:04d}"


def guardar_factura_bd(numero, fecha, cliente_id, concepto, base, igic_p, importe_igic, total):
    # Al igual que arriba, todo el cuerpo de la función lleva 4 espacios
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO facturas (numero_factura, fecha, cliente_id, concepto, base_imponible, porcentaje_igic, importe_igic, total)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (numero, fecha, cliente_id, concepto, base, igic_p, importe_igic, total))
    conn.commit()
    conn.close()

def registrar_gasto(fecha, proveedor_cif, concepto, importe):
    conn = conectar_db()
    cursor = conn.cursor()
    n_gasto_id = calcular_siguiente_gasto()  # Generamos el número de gasto automático
    cursor.execute("""
        INSERT INTO gastos (numero_gasto, fecha, proveedor_CIF, concepto, importe)
        VALUES (?, ?, ?, ?, ?)
    """, (n_gasto_id, fecha, proveedor_cif, concepto, importe))
    conn.commit()
    conn.close()

def calcular_siguiente_gasto():
    conn = conectar_db()
    cursor = conn.cursor()
    año_actual = datetime.now().strftime("%Y")
    
    cursor.execute("""
        SELECT numero_gasto FROM gastos 
        WHERE numero_gasto LIKE ? 
        ORDER BY id DESC LIMIT 1
    """, (f"GAS-{año_actual}-%",)) 
    
    ultimo_registro = cursor.fetchone()
    conn.close()
    
    if ultimo_registro:
        ultimo_num = int(ultimo_registro[0].split("-")[-1])
        nuevo_num = ultimo_num + 1
    else:
        nuevo_num = 1
        
    return f"GAS-{año_actual}-{nuevo_num:04d}"

def obtener_gastos():
    conn = conectar_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            id,
            numero_gasto,
            fecha,
            proveedor_CIF AS proveedor,
            concepto,
            importe
        FROM gastos 
        ORDER BY id DESC
    """)
    gastos = cursor.fetchall()
    conn.close()
    return gastos

def obtener_facturas_periodo(año=None, trimestre=None):
    conn = conectar_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    condiciones = []
    params = []

    if año:
        condiciones.append("strftime('%Y', substr(fecha, 7, 4) || '-' || substr(fecha, 4, 2) || '-' || substr(fecha, 1, 2)) = ?")
        params.append(str(año))
    if trimestre:
        meses = {1: ('01','02','03'), 2: ('04','05','06'), 3: ('07','08','09'), 4: ('10','11','12')}
        m = meses[trimestre]
        condiciones.append("substr(fecha, 4, 2) IN (?, ?, ?)")
        params.extend(m)

    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    cursor.execute(f"""
        SELECT f.numero_factura, f.fecha, c.nombre_fiscal AS cliente,
               f.base_imponible, f.porcentaje_igic, f.importe_igic, f.total
        FROM facturas f
        LEFT JOIN clientes c ON f.cliente_id = c.id
        {where}
        ORDER BY f.id DESC
    """, params)
    facturas = cursor.fetchall()
    conn.close()
    return facturas

def obtener_gastos_periodo(año=None, trimestre=None):
    conn = conectar_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    condiciones = []
    params = []

    if año:
        condiciones.append("strftime('%Y', substr(fecha, 7, 4) || '-' || substr(fecha, 4, 2) || '-' || substr(fecha, 1, 2)) = ?")
        params.append(str(año))
    if trimestre:
        meses = {1: ('01','02','03'), 2: ('04','05','06'), 3: ('07','08','09'), 4: ('10','11','12')}
        m = meses[trimestre]
        condiciones.append("substr(fecha, 4, 2) IN (?, ?, ?)")
        params.extend(m)

    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    cursor.execute(f"""
        SELECT numero_gasto, fecha, proveedor_CIF AS proveedor, concepto, importe
        FROM gastos
        {where}
        ORDER BY id DESC
    """, params)
    gastos = cursor.fetchall()
    conn.close()
    return gastos

def borrar_factura(numero_factura):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM facturas WHERE numero_factura = ?", (numero_factura,))
    conn.commit()
    conn.close()

def borrar_gasto(numero_gasto):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM gastos WHERE numero_gasto = ?", (numero_gasto,))
    conn.commit()
    conn.close()

def borrar_cliente(cif_nif):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM clientes WHERE cif_nif = ?", (cif_nif,))
    conn.commit()
    conn.close()

def crear_tabla_provisiones():
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("""
      CREATE TABLE IF NOT EXISTS provisiones (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          numero_provision TEXT UNIQUE NOT NULL,
          fecha TEXT NOT NULL,
          cliente_id INTEGER,
          concepto TEXT NOT NULL,
          importe REAL NOT NULL,
          factura_asociada TEXT DEFAULT NULL,
          aplicada INTEGER DEFAULT 0,
          FOREIGN KEY(cliente_id) REFERENCES clientes(id)
      )
    """)
    conn.commit()
    conn.close()

def calcular_siguiente_provision():
    conn = conectar_db()
    cursor = conn.cursor()
    año_actual = datetime.now().strftime("%Y")
    cursor.execute("""
        SELECT numero_provision FROM provisiones
        WHERE numero_provision LIKE ?
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
        VALUES (?, ?, ?, ?, ?, ?)
    """, (numero, fecha, cliente_id, concepto, importe, factura_asociada))
    conn.commit()
    conn.close()

def obtener_provisiones():
    conn = conectar_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT p.numero_provision, p.fecha, c.nombre_fiscal AS cliente,
               p.concepto, p.importe, p.factura_asociada
        FROM provisiones p
        LEFT JOIN clientes c ON p.cliente_id = c.id
        ORDER BY p.id DESC
    """)
    rows = cursor.fetchall()
    conn.close()
    return rows

def borrar_provision(numero_provision):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM provisiones WHERE numero_provision = ?", (numero_provision,))
    conn.commit()
    conn.close()

def obtener_provisiones_periodo(año=None, trimestre=None):
    conn = conectar_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    condiciones = []
    params = []
    if año:
        condiciones.append("strftime('%Y', substr(p.fecha,7,4)||'-'||substr(p.fecha,4,2)||'-'||substr(p.fecha,1,2)) = ?")
        params.append(str(año))
    if trimestre:
        meses = {1:('01','02','03'), 2:('04','05','06'), 3:('07','08','09'), 4:('10','11','12')}
        condiciones.append("substr(p.fecha,4,2) IN (?,?,?)")
        params.extend(meses[trimestre])
    where = ("WHERE " + " AND ".join(condiciones)) if condiciones else ""
    cursor.execute(f"""
        SELECT p.numero_provision, p.fecha, c.nombre_fiscal AS cliente,
               p.concepto, p.importe, p.factura_asociada
        FROM provisiones p
        LEFT JOIN clientes c ON p.cliente_id = c.id
        {where}
        ORDER BY p.id DESC
    """, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def obtener_provisiones_pendientes(cliente_id):
    """Provisiones no aplicadas aún de un cliente concreto."""
    conn = conectar_db()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, numero_provision, concepto, importe
        FROM provisiones
        WHERE cliente_id = ? AND aplicada = 0
        ORDER BY id ASC
    """, (cliente_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def marcar_provisiones_aplicadas(ids_provisiones, numero_factura):
    """Marca las provisiones seleccionadas como aplicadas y les asocia la factura."""
    conn = conectar_db()
    cursor = conn.cursor()
    for pid in ids_provisiones:
        cursor.execute("""
            UPDATE provisiones
            SET aplicada = 1, factura_asociada = ?
            WHERE id = ?
        """, (numero_factura, pid))
    conn.commit()
    conn.close()