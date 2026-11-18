"""
╔══════════════════════════════════════════════════════════════════════════╗
║    BACKEND API  —  AGRUPACION AGUARICO v6                               ║
║    FastAPI · SQLite · JWT · ReportLab                                   ║
║    Inicia con:                                                           ║
║      uvicorn backend_api:app --host 0.0.0.0 --port 8000 --reload       ║
╚══════════════════════════════════════════════════════════════════════════╝
"""

import os
import sqlite3
import hashlib
from datetime import datetime, timedelta
from typing import Optional

from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from jose import JWTError, jwt
from passlib.context import CryptContext
from werkzeug.security import generate_password_hash, check_password_hash

# ── ReportLab ──────────────────────────────────────────────────────────────
try:
    from reportlab.lib.pagesizes import A4, landscape
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.platypus import (SimpleDocTemplate, Table, TableStyle,
                                    Paragraph, Spacer, HRFlowable)
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

# ════════════════════════════════════════════════════════════════════════════
# CONFIGURACIÓN
# ════════════════════════════════════════════════════════════════════════════
# Ruta absoluta a la BD — misma carpeta que este script
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
DB_PATH    = os.path.join(BASE_DIR, "aguarico_v6.db")
DIR_REP    = os.path.join(BASE_DIR, "reportes")
os.makedirs(DIR_REP, exist_ok=True)

SECRET_KEY = "AGUARICO_SECRET_2024_@#xZ9q"  # Cambia en producción
ALGORITHM  = "HS256"
TOKEN_EXPIRE_HOURS = 8

pwd_ctx    = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2     = OAuth2PasswordBearer(tokenUrl="/login")

# ════════════════════════════════════════════════════════════════════════════
# APP
# ════════════════════════════════════════════════════════════════════════════
app = FastAPI(
    title="API Agrupación Aguarico",
    version="1.0.0",
    description="Backend para sistema de gestión Aguarico v6"
)

# Permitir peticiones desde cualquier origen (app móvil Flutter)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ════════════════════════════════════════════════════════════════════════════
# DB HELPERS
# ════════════════════════════════════════════════════════════════════════════
def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row      # acceso por nombre de columna
    return conn


def hash_pwd_sha(pwd: str) -> str:
    """Hash SHA-256 igual que el sistema de escritorio (compatibilidad)."""
    return hashlib.sha256(pwd.encode()).hexdigest()

def hash_pwd(pwd: str) -> str:
    """Hash werkzeug (pbkdf2) para nuevos usuarios."""
    return generate_password_hash(pwd)

def verificar_pwd(pwd: str, hashed: str) -> bool:
    """Verifica la contraseña soportando werkzeug y SHA-256 legacy."""
    # Hash werkzeug empieza con 'pbkdf2:' o 'scrypt:'
    if hashed.startswith('pbkdf2:') or hashed.startswith('scrypt:'):
        return check_password_hash(hashed, pwd)
    # Fallback: SHA-256 puro (usuarios existentes)
    return hashed == hash_pwd_sha(pwd)


# ════════════════════════════════════════════════════════════════════════════
# MODELOS PYDANTIC
# ════════════════════════════════════════════════════════════════════════════
class TokenResponse(BaseModel):
    access_token: str
    token_type: str
    usuario: dict


class LoginRequest(BaseModel):
    """Login vía JSON — usado por la app móvil."""
    username: Optional[str] = None
    password: Optional[str] = None
    usuario:  Optional[str] = None
    clave:    Optional[str] = None


class AsistenciaQR(BaseModel):
    codigo_qr: str          # Formato: AGUARICO|cedula|codigo_puesto  ó solo cédula


class AsistenciaTipear(BaseModel):
    cedula: str


class ReporteFiltros(BaseModel):
    fecha_desde: Optional[str] = ""   # dd/mm/yyyy
    fecha_hasta: Optional[str] = ""
    socio_id:    Optional[int] = None


class TaxiConectar(BaseModel):
    unidad: str
    socio_nombre: Optional[str] = ""
    telefono: Optional[str] = ""
    latitud: Optional[float] = 0.0
    longitud: Optional[float] = 0.0


class TaxiGPS(BaseModel):
    unidad: str
    latitud: float
    longitud: float


class TaxiUnidad(BaseModel):
    unidad: str


class TaxiAlerta(BaseModel):
    unidad: str
    socio_nombre: Optional[str] = ""
    latitud: Optional[float] = 0.0
    longitud: Optional[float] = 0.0


# ════════════════════════════════════════════════════════════════════════════
# JWT HELPERS
# ════════════════════════════════════════════════════════════════════════════
def crear_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.utcnow() + timedelta(hours=TOKEN_EXPIRE_HOURS)
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)


def verificar_token(token: str = Depends(oauth2)):
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido o expirado",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        uid = payload.get("sub")
        if uid is None:
            raise exc
        return payload
    except JWTError:
        raise exc


# ════════════════════════════════════════════════════════════════════════════
# PARSEAR QR
# ════════════════════════════════════════════════════════════════════════════
def parsear_qr(contenido: str) -> dict | None:
    partes = contenido.strip().split("|")
    if len(partes) == 3 and partes[0] == "AGUARICO":
        return {"cedula": partes[1], "codigo_puesto": partes[2]}
    # Solo cédula
    c = contenido.strip()
    if c.isdigit() and len(c) >= 8:
        return {"cedula": c, "codigo_puesto": ""}
    return None


def buscar_socio_activo(cedula: str = "", codigo: str = ""):
    conn = get_conn(); c = conn.cursor()
    if cedula:
        c.execute("""SELECT id, codigo_puesto, nombre, apellido, cedula
                     FROM socios WHERE cedula=? AND estado='ACTIVO'""", (cedula,))
    elif codigo:
        c.execute("""SELECT id, codigo_puesto, nombre, apellido, cedula
                     FROM socios WHERE codigo_puesto=? AND estado='ACTIVO'""", (codigo,))
    else:
        conn.close(); return None
    row = c.fetchone(); conn.close()
    if not row:
        return None
    return {
        "id": row["id"], "codigo": row["codigo_puesto"],
        "nombre": f"{row['nombre']} {row['apellido']}",
        "cedula": row["cedula"]
    }


def registrar_asistencia(socio: dict, registrado_por: str, obs: str = "") -> dict:
    hoy  = datetime.now().strftime("%d/%m/%Y")
    hora = datetime.now().strftime("%H:%M:%S")
    conn = get_conn(); c = conn.cursor()

    c.execute("""SELECT id, hora_salida FROM asistencias
                 WHERE socio_id=? AND fecha=?""", (socio["id"], hoy))
    row = c.fetchone()

    if not row:
        c.execute("""INSERT INTO asistencias
                     (socio_id, codigo_puesto, nombre_socio, fecha,
                      hora_entrada, estado, registrado_por, observacion)
                     VALUES (?,?,?,?,?,?,?,?)""",
                  (socio["id"], socio["codigo"], socio["nombre"], hoy,
                   hora, "Entrada", registrado_por,
                   obs or "Registro por app movil"))
        conn.commit(); conn.close()
        return {
            "accion": "ENTRADA",
            "socio": socio["nombre"],
            "codigo": socio["codigo"],
            "hora": hora, "fecha": hoy,
            "mensaje": f"Entrada registrada: {socio['nombre']} a las {hora}"
        }
    elif not row["hora_salida"]:
        c.execute("""UPDATE asistencias SET hora_salida=?, estado='Completo'
                     WHERE id=?""", (hora, row["id"]))
        conn.commit(); conn.close()
        return {
            "accion": "SALIDA",
            "socio": socio["nombre"],
            "codigo": socio["codigo"],
            "hora": hora, "fecha": hoy,
            "mensaje": f"Salida registrada: {socio['nombre']} a las {hora}"
        }
    else:
        conn.close()
        return {
            "accion": "YA_COMPLETO",
            "socio": socio["nombre"],
            "codigo": socio["codigo"],
            "hora": hora, "fecha": hoy,
            "mensaje": f"{socio['nombre']} ya tiene entrada y salida registradas hoy."
        }


# ════════════════════════════════════════════════════════════════════════════
# ENDPOINTS
# ════════════════════════════════════════════════════════════════════════════

# ── GET /  ───────────────────────────────────────────────────────────────────
@app.get("/", tags=["Estado"])
def raiz():
    return {
        "sistema": "API Agrupación Aguarico v6",
        "estado": "activo",
        "hora": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "endpoints": ["/login", "/socios", "/asistencia/qr",
                      "/asistencia/tipear", "/asistencia/hoy",
                      "/asistencia/historial", "/reporte/pdf"]
    }


# ── POST /login ──────────────────────────────────────────────────────────────
@app.post("/login", response_model=TokenResponse, tags=["Auth"])
async def login(
    # JSON body (app móvil)
    data: LoginRequest | None = None,
    # Form urlencoded (swagger / sistema escritorio)
    username: str | None = Form(default=None),
    password: str | None = Form(default=None),
):
    """
    Autenticación con usuario y contraseña.
    Acepta JSON  → { "username": "...", "password": "..." }
    Acepta Form  → username=...&password=...
    Devuelve JWT Bearer token.
    """
    # Resolver credenciales según el formato recibido
    user = (data.username or data.usuario if data else username) or ""
    pwd  = (data.password or data.clave   if data else password) or ""

    if not user or not pwd:
        raise HTTPException(status_code=422, detail="username y password son requeridos")

    conn = get_conn(); c = conn.cursor()
    c.execute("""SELECT id, username, rol, nombre, password
                 FROM usuarios WHERE LOWER(username)=LOWER(?)""", (user,))
    row = c.fetchone(); conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    if not verificar_pwd(pwd, row["password"]):
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")

    token = crear_token({
        "sub": str(row["id"]),
        "username": row["username"],
        "rol": row["rol"],
        "nombre": row["nombre"]
    })
    return {
        "access_token": token,
        "token_type": "bearer",
        "usuario": {
            "id": row["id"],
            "username": row["username"],
            "rol": row["rol"],
            "nombre": row["nombre"]
        }
    }


# ── GET /socios ──────────────────────────────────────────────────────────────
@app.get("/socios", tags=["Socios"])
def listar_socios(
    buscar: str = "",
    estado: str = "",
    payload: dict = Depends(verificar_token)
):
    """Lista todos los socios. Filtra por nombre/cédula/código y estado."""
    conn = get_conn(); c = conn.cursor()
    sql = """SELECT id, codigo_puesto, nombre, apellido, cedula,
                    rango, estado, unidad, whatsapp, fecha_ingreso
             FROM socios WHERE 1=1"""
    params = []
    if buscar:
        sql += """ AND (nombre LIKE ? OR apellido LIKE ?
                        OR cedula LIKE ? OR codigo_puesto LIKE ?)"""
        params.extend([f"%{buscar}%"] * 4)
    if estado:
        sql += " AND estado=?"
        params.append(estado.upper())
    sql += " ORDER BY apellido, nombre"
    c.execute(sql, params)
    rows = c.fetchall(); conn.close()
    return {
        "total": len(rows),
        "socios": [dict(r) for r in rows]
    }


# ── GET /socios/{id} ─────────────────────────────────────────────────────────
@app.get("/socios/{socio_id}", tags=["Socios"])
def detalle_socio(socio_id: int, payload: dict = Depends(verificar_token)):
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT * FROM socios WHERE id=?", (socio_id,))
    row = c.fetchone()
    conn.close()
    if not row:
        raise HTTPException(status_code=404, detail="Socio no encontrado")
    return dict(row)


# ── POST /asistencia/qr ──────────────────────────────────────────────────────
@app.post("/asistencia/qr", tags=["Asistencia"])
def asistencia_por_qr(
    data: AsistenciaQR,
    payload: dict = Depends(verificar_token)
):
    """
    Registra entrada o salida escaneando el QR del socio.
    El QR puede tener formato: AGUARICO|cedula|codigo_puesto  o solo cédula.
    - Si el socio no tiene registro hoy → registra ENTRADA
    - Si tiene entrada sin salida → registra SALIDA
    - Si ya tiene ambas → devuelve YA_COMPLETO
    """
    datos_qr = parsear_qr(data.codigo_qr)
    if not datos_qr:
        raise HTTPException(
            status_code=400,
            detail=f"Código QR no reconocido: '{data.codigo_qr}'. "
                   f"Formato esperado: AGUARICO|cedula|codigo  o solo cédula."
        )

    socio = buscar_socio_activo(
        cedula=datos_qr.get("cedula", ""),
        codigo=datos_qr.get("codigo_puesto", "")
    )
    if not socio:
        raise HTTPException(
            status_code=404,
            detail=f"Socio activo no encontrado con cédula '{datos_qr.get('cedula')}'"
        )

    return registrar_asistencia(
        socio,
        registrado_por=payload.get("nombre", payload.get("username", "App Móvil")),
        obs="QR - App Móvil"
    )


# ── POST /asistencia/tipear ──────────────────────────────────────────────────
@app.post("/asistencia/tipear", tags=["Asistencia"])
def asistencia_por_cedula(
    data: AsistenciaTipear,
    payload: dict = Depends(verificar_token)
):
    """
    Registra entrada o salida tipeando la cédula manualmente.
    Misma lógica que /asistencia/qr.
    """
    cedula = data.cedula.strip()
    if not cedula:
        raise HTTPException(status_code=400, detail="La cédula no puede estar vacía")

    socio = buscar_socio_activo(cedula=cedula)
    if not socio:
        raise HTTPException(
            status_code=404,
            detail=f"Socio activo no encontrado con cédula '{cedula}'"
        )

    return registrar_asistencia(
        socio,
        registrado_por=payload.get("nombre", payload.get("username", "App Móvil")),
        obs="Manual - App Móvil"
    )


# ── GET /asistencia/hoy ──────────────────────────────────────────────────────
@app.get("/asistencia/hoy", tags=["Asistencia"])
def asistencia_hoy(payload: dict = Depends(verificar_token)):
    """Devuelve los registros de asistencia del día actual."""
    hoy = datetime.now().strftime("%d/%m/%Y")
    conn = get_conn(); c = conn.cursor()
    c.execute("""SELECT id, codigo_puesto, nombre_socio, fecha,
                        hora_entrada, hora_salida, estado, registrado_por
                 FROM asistencias WHERE fecha=?
                 ORDER BY hora_entrada ASC""", (hoy,))
    rows = c.fetchall(); conn.close()
    return {
        "fecha": hoy,
        "total": len(rows),
        "registros": [dict(r) for r in rows]
    }


# ── GET /asistencia/historial ────────────────────────────────────────────────
@app.get("/asistencia/historial", tags=["Asistencia"])
def historial_asistencia(
    socio_id: Optional[int] = None,
    fecha_desde: str = "",
    fecha_hasta: str = "",
    limite: int = 100,
    payload: dict = Depends(verificar_token)
):
    """Historial de asistencias con filtros opcionales."""
    conn = get_conn(); c = conn.cursor()
    sql = """SELECT id, codigo_puesto, nombre_socio, fecha,
                    hora_entrada, hora_salida, estado, registrado_por
             FROM asistencias WHERE 1=1"""
    params = []
    if socio_id:
        sql += " AND socio_id=?"
        params.append(socio_id)
    if fecha_desde:
        sql += " AND fecha >= ?"
        params.append(fecha_desde)
    if fecha_hasta:
        sql += " AND fecha <= ?"
        params.append(fecha_hasta)
    sql += f" ORDER BY id DESC LIMIT {min(limite, 500)}"
    c.execute(sql, params)
    rows = c.fetchall(); conn.close()
    return {
        "total": len(rows),
        "registros": [dict(r) for r in rows]
    }


# ── GET /asistencia/mi-historial ─────────────────────────────────────────────
@app.get("/asistencia/mi-historial", tags=["Asistencia"])
def mi_historial(
    cedula: str,
    payload: dict = Depends(verificar_token)
):
    """Historial de asistencia de un socio por su cédula."""
    conn = get_conn(); c = conn.cursor()
    c.execute("SELECT id FROM socios WHERE cedula=?", (cedula,))
    row = c.fetchone()
    if not row:
        conn.close()
        raise HTTPException(status_code=404,
                            detail=f"Socio no encontrado con cédula '{cedula}'")
    sid = row["id"]
    c.execute("""SELECT fecha, hora_entrada, hora_salida, estado, registrado_por
                 FROM asistencias WHERE socio_id=?
                 ORDER BY fecha DESC, hora_entrada DESC LIMIT 60""", (sid,))
    rows = c.fetchall(); conn.close()
    return {
        "cedula": cedula,
        "total": len(rows),
        "registros": [dict(r) for r in rows]
    }


# ── POST /reporte/pdf ─────────────────────────────────────────────────────────
@app.post("/reporte/pdf", tags=["Reportes"])
def generar_reporte_pdf(
    filtros: ReporteFiltros,
    payload: dict = Depends(verificar_token)
):
    """
    Genera PDF de asistencia con filtros opcionales.
    Devuelve el archivo PDF para descarga.
    """
    if not REPORTLAB_OK:
        raise HTTPException(
            status_code=503,
            detail="ReportLab no instalado en el servidor. "
                   "Instala con: pip install reportlab"
        )

    conn = get_conn(); c = conn.cursor()
    sql = """SELECT a.codigo_puesto, a.nombre_socio, a.fecha,
                    a.hora_entrada, a.hora_salida, a.estado,
                    a.registrado_por, a.observacion
             FROM asistencias a WHERE 1=1"""
    params = []
    if filtros.fecha_desde:
        sql += " AND a.fecha >= ?"
        params.append(filtros.fecha_desde)
    if filtros.fecha_hasta:
        sql += " AND a.fecha <= ?"
        params.append(filtros.fecha_hasta)
    if filtros.socio_id:
        sql += " AND a.socio_id = ?"
        params.append(filtros.socio_id)
    sql += " ORDER BY a.fecha ASC, a.hora_entrada ASC"
    c.execute(sql, params)
    rows = c.fetchall(); conn.close()

    if not rows:
        raise HTTPException(status_code=404,
                            detail="No hay registros con los filtros indicados.")

    # ── Generar PDF ───────────────────────────────────────────────────────
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    archivo = os.path.join(DIR_REP, f"API_Asistencia_{ts}.pdf")

    doc = SimpleDocTemplate(
        archivo, pagesize=landscape(A4),
        rightMargin=1.5*cm, leftMargin=1.5*cm,
        topMargin=1.5*cm, bottomMargin=1.5*cm
    )
    estilos = getSampleStyleSheet()
    st_titulo = ParagraphStyle("t", fontSize=18, fontName="Helvetica-Bold",
                                alignment=TA_CENTER,
                                textColor=colors.HexColor("#0f2746"), spaceAfter=4)
    st_sub = ParagraphStyle("s", fontSize=10, fontName="Helvetica",
                             alignment=TA_CENTER,
                             textColor=colors.HexColor("#1a73e8"), spaceAfter=10)
    st_pie = ParagraphStyle("p", fontSize=8, fontName="Helvetica",
                             alignment=TA_CENTER, textColor=colors.grey)

    rango = f"{filtros.fecha_desde or '—'}  al  {filtros.fecha_hasta or '—'}"
    usuario_nombre = payload.get("nombre", payload.get("username", "API"))

    elementos = [
        Paragraph("ASO AGUARICO", st_titulo),
        Paragraph("AGRUPACION AUTOMOVILISTICA AGUARICO", st_sub),
        Paragraph("REPORTE DE ASISTENCIA", st_sub),
        HRFlowable(width="100%", thickness=2,
                   color=colors.HexColor("#1a73e8"), spaceAfter=6),
        Paragraph(
            f"Periodo: <b>{rango}</b>  |  Total: <b>{len(rows)}</b>  |  "
            f"Generado: <b>{datetime.now().strftime('%d/%m/%Y %H:%M')}</b>  |  "
            f"Por: <b>{usuario_nombre}</b>", st_sub),
    ]

    encabezado = ["#", "Codigo", "Nombre", "Fecha",
                  "Entrada", "Salida", "Estado", "Registrado por"]
    datos = [encabezado]
    for i, row in enumerate(rows, 1):
        datos.append([
            str(i),
            row["codigo_puesto"] or "",
            (row["nombre_socio"] or "")[:30],
            row["fecha"] or "",
            row["hora_entrada"] or "",
            row["hora_salida"] or "--",
            row["estado"] or "",
            (row["registrado_por"] or "")[:20],
        ])
    # Fila total
    completos = sum(1 for r in rows if r["estado"] == "Completo")
    datos.append(["", "",
                  f"TOTAL ENTRADAS: {len(rows)}",
                  f"Completos: {completos}",
                  f"Solo entrada: {len(rows)-completos}",
                  "", "", ""])

    col_w = [0.7*cm, 2.2*cm, 5.5*cm, 2.5*cm, 2.2*cm, 2.2*cm, 2.4*cm, 4.5*cm]
    tabla = Table(datos, colWidths=col_w, repeatRows=1)
    tabla.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#0f2746")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0),  8),
        ("ALIGN",         (0, 0), (-1, 0),  "CENTER"),
        ("ROWBACKGROUNDS",(0, 1), (-1, -2),
         [colors.white, colors.HexColor("#eaf0fb")]),
        ("FONTNAME",      (0, 1), (-1, -2), "Helvetica"),
        ("FONTSIZE",      (0, 1), (-1, -2), 7),
        ("ALIGN",         (0, 1), (-1, -2), "CENTER"),
        ("ALIGN",         (2, 1), (2, -1),  "LEFT"),
        ("BACKGROUND",    (0, -1), (-1, -1), colors.HexColor("#1a73e8")),
        ("TEXTCOLOR",     (0, -1), (-1, -1), colors.white),
        ("FONTNAME",      (0, -1), (-1, -1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, -1), (-1, -1), 7),
        ("GRID",          (0, 0), (-1, -1),  0.4, colors.HexColor("#c0c8d8")),
        ("BOX",           (0, 0), (-1, -1),  1,   colors.HexColor("#0f2746")),
        ("TOPPADDING",    (0, 0), (-1, -1),  3),
        ("BOTTOMPADDING", (0, 0), (-1, -1),  3),
    ]))
    elementos.extend([
        tabla, Spacer(1, 0.5*cm),
        HRFlowable(width="100%", thickness=1,
                   color=colors.HexColor("#c0c8d8")),
        Paragraph("AGRUPACION AUTOMOVILISTICA AGUARICO  —  Sistema v6  —  "
                  "Documento generado via API", st_pie)
    ])

    doc.build(elementos)
    return FileResponse(
        path=archivo,
        media_type="application/pdf",
        filename=f"Asistencia_Aguarico_{ts}.pdf"
    )


# ── GET /estadisticas ─────────────────────────────────────────────────────────
@app.get("/estadisticas", tags=["Reportes"])
def estadisticas(payload: dict = Depends(verificar_token)):
    """Resumen rápido para el dashboard de la app móvil."""
    conn = get_conn(); c = conn.cursor()
    hoy = datetime.now().strftime("%d/%m/%Y")

    c.execute("SELECT COUNT(*) AS n FROM socios"); total_s = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) AS n FROM socios WHERE estado='ACTIVO'"); activos = c.fetchone()["n"]
    c.execute("SELECT COUNT(DISTINCT socio_id) AS n FROM asistencias WHERE fecha=?",
              (hoy,)); asist_hoy = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) AS n FROM sanciones WHERE estado='Vigente'"); sanciones = c.fetchone()["n"]
    c.execute("SELECT COUNT(*) AS n FROM vehiculos_historial WHERE estado='Actual'"); vehs = c.fetchone()["n"]
    conn.close()
    return {
        "fecha": hoy,
        "total_socios": total_s,
        "socios_activos": activos,
        "asistencia_hoy": asist_hoy,
        "sanciones_vigentes": sanciones,
        "vehiculos_actuales": vehs
    }


# ════════════════════════════════════════════════════════════════════════════
# MÓDULO TAXIS — RASTREO GPS Y BOTÓN DE PÁNICO (APP MÓVIL)
# ════════════════════════════════════════════════════════════════════════════

@app.post("/taxi/conectar", tags=["Taxi Movil"])
def taxi_conectar(data: TaxiConectar):
    conn = get_conn(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS taxis_en_linea (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unidad TEXT UNIQUE,
        socio_nombre TEXT,
        telefono TEXT,
        estado TEXT DEFAULT 'CONECTADO',
        latitud REAL,
        longitud REAL,
        ultima_actualizacion TEXT,
        solicitud_desconexion INTEGER DEFAULT 0,
        alerta_activa INTEGER DEFAULT 0,
        alerta_fecha TEXT
    )""")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""INSERT INTO taxis_en_linea 
                 (unidad, socio_nombre, telefono, estado, latitud, longitud, ultima_actualizacion, solicitud_desconexion, alerta_activa)
                 VALUES (?, ?, ?, 'CONECTADO', ?, ?, ?, 0, 0)
                 ON CONFLICT(unidad) DO UPDATE SET
                 socio_nombre=excluded.socio_nombre,
                 telefono=excluded.telefono,
                 estado='CONECTADO',
                 latitud=excluded.latitud,
                 longitud=excluded.longitud,
                 ultima_actualizacion=excluded.ultima_actualizacion,
                 solicitud_desconexion=0,
                 alerta_activa=0""",
              (data.unidad, data.socio_nombre, data.telefono, data.latitud, data.longitud, now_str))
    conn.commit(); conn.close()
    return {"status": "ok", "mensaje": f"Unidad {data.unidad} conectada a la matriz"}

@app.post("/taxi/gps", tags=["Taxi Movil"])
def taxi_actualizar_gps(data: TaxiGPS):
    conn = get_conn(); c = conn.cursor()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""UPDATE taxis_en_linea SET latitud=?, longitud=?, ultima_actualizacion=?
                 WHERE unidad=?""", (data.latitud, data.longitud, now_str, data.unidad))
    c.execute("""SELECT estado, solicitud_desconexion, alerta_activa FROM taxis_en_linea WHERE unidad=?""",
              (data.unidad,))
    row = c.fetchone()
    conn.commit(); conn.close()

    desconexion_aprobada = False
    alerta_activa = False
    if row:
        desconexion_aprobada = (row["estado"] == "DESCONECTADO")
        alerta_activa = bool(row["alerta_activa"])

    return {
        "status": "ok",
        "desconexion_aprobada": desconexion_aprobada,
        "alerta_activa": alerta_activa
    }

@app.post("/taxi/solicitar-desconexion", tags=["Taxi Movil"])
def taxi_solicitar_desconexion(data: TaxiUnidad):
    conn = get_conn(); c = conn.cursor()
    c.execute("""UPDATE taxis_en_linea SET solicitud_desconexion=1 WHERE unidad=?""", (data.unidad,))
    conn.commit(); conn.close()
    return {"status": "ok", "mensaje": "Solicitud enviada a la matriz"}

@app.post("/taxi/aprobar-desconexion", tags=["Taxi Movil"])
def taxi_aprobar_desconexion(data: TaxiUnidad):
    conn = get_conn(); c = conn.cursor()
    c.execute("""UPDATE taxis_en_linea SET estado='DESCONECTADO', solicitud_desconexion=0 WHERE unidad=?""", (data.unidad,))
    conn.commit(); conn.close()
    return {"status": "ok", "mensaje": f"Desconexión aprobada para {data.unidad}"}

@app.post("/taxi/alerta", tags=["Taxi Movil"])
def taxi_disparar_alerta(data: TaxiAlerta):
    conn = get_conn(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS alertas_emergencia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        unidad TEXT,
        socio_nombre TEXT,
        latitud REAL,
        longitud REAL,
        fecha_hora TEXT,
        estado TEXT DEFAULT 'ACTIVA'
    )""")
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    c.execute("""UPDATE taxis_en_linea SET alerta_activa=1, alerta_fecha=? WHERE unidad=?""",
              (now_str, data.unidad))
    c.execute("""INSERT INTO alertas_emergencia (unidad, socio_nombre, latitud, longitud, fecha_hora, estado)
                 VALUES (?, ?, ?, ?, ?, 'ACTIVA')""",
              (data.unidad, data.socio_nombre, data.latitud, data.longitud, now_str))
    conn.commit(); conn.close()
    return {"status": "alerta_activa", "unidad": data.unidad, "fecha_hora": now_str}

@app.post("/taxi/cancelar-alerta", tags=["Taxi Movil"])
def taxi_cancelar_alerta(data: TaxiUnidad):
    conn = get_conn(); c = conn.cursor()
    c.execute("""UPDATE taxis_en_linea SET alerta_activa=0 WHERE unidad=?""", (data.unidad,))
    c.execute("""UPDATE alertas_emergencia SET estado='FALSA_ALARMA' WHERE unidad=? AND estado='ACTIVA'""", (data.unidad,))
    conn.commit(); conn.close()
    return {"status": "ok", "mensaje": "Alerta cancelada"}

@app.get("/taxi/monitoreo", tags=["Taxi Movil"])
def taxi_monitoreo():
    conn = get_conn(); c = conn.cursor()
    try:
        taxis = [dict(r) for r in c.execute("SELECT * FROM taxis_en_linea ORDER BY id DESC").fetchall()]
        alertas = [dict(r) for r in c.execute("SELECT * FROM alertas_emergencia WHERE estado='ACTIVA' ORDER BY id DESC").fetchall()]
    except Exception:
        taxis = []
        alertas = []
    conn.close()
    return {"taxis": taxis, "alertas_activas": alertas}

@app.get("/app", response_class=HTMLResponse, tags=["Taxi Movil"])
def web_app_movil():
    """Aplicación Móvil Web Progresiva (PWA) interactiva para teléfonos y radios Android."""
    return """<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
  <title>Taxi Seguro Aguarico</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; }
    body { background: #0f2746; color: #fff; height: 100vh; display: flex; flex-direction: column; overflow: hidden; }
    
    /* Header */
    header { background: #162d50; padding: 14px 18px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid rgba(255,255,255,0.1); }
    .title { font-weight: bold; font-size: 16px; color: #fff; display: flex; align-items: center; gap: 8px; }
    .btn-camuflaje { background: #1e3a5f; border: none; color: #b0bec5; padding: 6px 12px; border-radius: 8px; font-size: 13px; cursor: pointer; }
    
    /* Main Content */
    .container { flex: 1; padding: 18px; display: flex; flex-direction: column; justify-content: space-between; max-width: 480px; margin: 0 auto; width: 100%; overflow-y: auto; }
    
    /* Status Card */
    .card { background: #1e3a5f; border-radius: 16px; padding: 16px; box-shadow: 0 4px 12px rgba(0,0,0,0.3); }
    .status-badge { display: inline-block; padding: 4px 10px; border-radius: 12px; font-size: 11px; font-weight: bold; letter-spacing: 0.5px; margin-bottom: 8px; }
    .badge-on { background: #27ae60; color: #fff; }
    .badge-off { background: #c0392b; color: #fff; }
    .badge-wait { background: #f39c12; color: #fff; }
    
    .driver-name { font-size: 18px; font-weight: bold; }
    .taxi-unit { font-size: 14px; color: #b0bec5; }
    .gps-info { font-size: 12px; color: #64b5f6; margin-top: 8px; }

    /* Action Buttons */
    .btn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-top: 14px; }
    .btn { padding: 14px; border: none; border-radius: 12px; font-weight: bold; font-size: 14px; cursor: pointer; transition: 0.2s; }
    .btn-connect { background: #27ae60; color: #fff; }
    .btn-disconnect { background: #e67e22; color: #fff; }
    .btn:disabled { opacity: 0.4; cursor: not-allowed; }

    /* PANIC BUTTON */
    .panic-container { display: flex; flex-direction: column; align-items: center; justify-content: center; margin: 20px 0; }
    .panic-btn { width: 190px; height: 190px; border-radius: 50%; background: radial-gradient(circle, #ff1744 0%, #b71c1c 100%); border: 6px solid rgba(255,255,255,0.2); box-shadow: 0 0 40px rgba(255, 23, 68, 0.6); display: flex; flex-direction: column; align-items: center; justify-content: center; cursor: pointer; user-select: none; transition: transform 0.1s; }
    .panic-btn:active { transform: scale(0.95); }
    .panic-title { font-size: 26px; font-weight: 900; letter-spacing: 2px; }
    .panic-sub { font-size: 11px; opacity: 0.8; margin-top: 4px; }

    /* Emergency Modal Countdown */
    .modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.92); display: none; flex-direction: column; align-items: center; justify-content: center; padding: 24px; z-index: 999; }
    .countdown { font-size: 96px; font-weight: 900; color: #ff1744; margin: 20px 0; }
    .cancel-btn { background: #fff; color: #b71c1c; font-size: 18px; font-weight: bold; padding: 16px 32px; border-radius: 30px; border: none; cursor: pointer; }

    /* Calculator Camouflage Mode */
    #calc-screen { position: fixed; inset: 0; background: #000; display: none; flex-direction: column; z-index: 1000; }
    .calc-disp { flex: 1; display: flex; align-items: flex-end; justify-content: flex-end; padding: 30px; font-size: 54px; color: #fff; }
    .calc-pad { display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; padding: 16px; }
    .c-btn { background: #333; color: #fff; border: none; padding: 20px; font-size: 22px; border-radius: 16px; cursor: pointer; }
    .c-btn.op { background: #f39c12; }
  </style>
</head>
<body>

  <!-- App Header -->
  <header>
    <div class="title">🚗 Taxi Seguro</div>
    <button class="btn-camuflaje" onclick="toggleCamuflaje(true)">🧮 Modo Oculto</button>
  </header>

  <!-- App Body -->
  <div class="container">
    <div class="card">
      <span id="badge" class="status-badge badge-off">DESCONECTADO</span>
      <div class="driver-name" id="disp-driver">Jorge Stalyn Enríquez</div>
      <div class="taxi-unit" id="disp-unit">Unidad: <b>Taxi-10</b></div>
      <div class="gps-info" id="disp-gps">🛰️ GPS: Obteniendo ubicación...</div>
      
      <div class="btn-grid">
        <button id="btn-conectar" class="btn btn-connect" onclick="conectarTurno()">CONECTAR</button>
        <button id="btn-desconectar" class="btn btn-disconnect" onclick="solicitarDesconexion()" disabled>DESCONECTAR</button>
      </div>
    </div>

    <!-- BOTÓN DE PÁNICO -->
    <div class="panic-container">
      <div class="panic-btn" onclick="iniciarAlerta()">
        <span class="panic-title">PÁNICO</span>
        <span class="panic-sub">TOCA EN EMERGENCIA</span>
      </div>
    </div>

    <div style="text-align: center; color: rgba(255,255,255,0.5); font-size: 12px; margin-bottom: 8px;">
      Sistema de Seguridad Aguarico · Conexión Matriz
    </div>
  </div>

  <!-- Countdown Modal -->
  <div id="modal-panic" class="modal-overlay">
    <h2 style="color: #ff1744; font-size: 24px; text-align: center;">¡ALERTA DE EMERGENCIA ACTIVADA!</h2>
    <p style="color: #ccc; font-size: 14px; margin-top: 8px; text-align: center;">Transmitiendo a la Matriz y grupos en:</p>
    <div id="timer-val" class="countdown">10</div>
    <button id="cancel-btn" class="cancel-btn" onclick="cancelarDobleToque()">CANCELAR (Toca 2 veces)</button>
    <p id="cancel-hint" style="color: #aaa; font-size: 12px; margin-top: 14px;">Si fue una falsa alarma, toca 2 veces seguidas.</p>
  </div>

  <!-- Camouflage Mode (Calculadora) -->
  <div id="calc-screen">
    <div style="padding: 14px 18px; color: #666; font-size: 13px;">Calculadora</div>
    <div id="c-display" class="calc-disp">0</div>
    <div class="calc-pad">
      <button class="c-btn" onclick="calcPress('C')">C</button>
      <button class="c-btn" onclick="calcPress('+/-')">+/-</button>
      <button class="c-btn" onclick="calcPress('%')">%</button>
      <button class="c-btn op" onclick="calcPress('/')">÷</button>
      <button class="c-btn" onclick="calcPress('7')">7</button>
      <button class="c-btn" onclick="calcPress('8')">8</button>
      <button class="c-btn" onclick="calcPress('9')">9</button>
      <button class="c-btn op" onclick="calcPress('*')">×</button>
      <button class="c-btn" onclick="calcPress('4')">4</button>
      <button class="c-btn" onclick="calcPress('5')">5</button>
      <button class="c-btn" onclick="calcPress('6')">6</button>
      <button class="c-btn op" onclick="calcPress('-')">-</button>
      <button class="c-btn" onclick="calcPress('1')">1</button>
      <button class="c-btn" onclick="calcPress('2')">2</button>
      <button class="c-btn" onclick="calcPress('3')">3</button>
      <button class="c-btn op" onclick="calcPress('+')">+</button>
      <button class="c-btn" style="grid-column: span 2;" onclick="calcPress('0')">0</button>
      <button class="c-btn" onclick="calcPress('.')">.</button>
      <button class="c-btn op" onclick="calcPress('=')">=</button>
    </div>
  </div>

  <script>
    let unidad = "Taxi-10";
    let conductor = "Jorge Stalyn Enríquez";
    let telefono = "0963178853";
    let conectado = false;
    let esperandoDesconexion = false;
    let lat = -0.22985, lng = -78.52495;
    let countdownTimer = null;
    let secondsLeft = 10;
    let cancelTaps = 0;
    let calcInput = "";

    // Iniciar GPS Real
    if (navigator.geolocation) {
      navigator.geolocation.watchPosition((pos) => {
        lat = pos.coords.latitude;
        lng = pos.coords.longitude;
        document.getElementById("disp-gps").innerText = `🛰️ GPS: ${lat.toFixed(5)}, ${lng.toFixed(5)}`;
      }, () => {
        document.getElementById("disp-gps").innerText = `🛰️ GPS: Simulado (${lat}, ${lng})`;
      });
    }

    // Intervalo de transmisión a la Matriz
    setInterval(() => {
      if (conectado) {
        fetch("/taxi/gps", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({ unidad, latitud: lat, longitud: lng })
        })
        .then(r => r.json())
        .then(data => {
          if (data.desconexion_aprobada) {
            conectado = false;
            esperandoDesconexion = false;
            actualizarUI();
            alert("La Matriz ha aprobado tu fin de turno. Desconectado.");
          }
        }).catch(() => {});
      }
    }, 5000);

    function actualizarUI() {
      const badge = document.getElementById("badge");
      const btnConectar = document.getElementById("btn-conectar");
      const btnDesconectar = document.getElementById("btn-desconectar");

      if (conectado) {
        if (esperandoDesconexion) {
          badge.className = "status-badge badge-wait";
          badge.innerText = "ESPERANDO APROBACIÓN MATRIZ";
          btnDesconectar.innerText = "SOLICITADO...";
          btnDesconectar.disabled = true;
        } else {
          badge.className = "status-badge badge-on";
          badge.innerText = "EN SERVICIO / CONECTADO";
          btnDesconectar.innerText = "DESCONECTAR";
          btnDesconectar.disabled = false;
        }
        btnConectar.disabled = true;
      } else {
        badge.className = "status-badge badge-off";
        badge.innerText = "DESCONECTADO";
        btnConectar.disabled = false;
        btnDesconectar.disabled = true;
      }
    }

    function conectarTurno() {
      fetch("/taxi/conectar", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ unidad, socio_nombre: conductor, telefono, latitud: lat, longitud: lng })
      }).then(() => {
        conectado = true;
        esperandoDesconexion = false;
        actualizarUI();
      });
    }

    function solicitarDesconexion() {
      fetch("/taxi/solicitar-desconexion", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ unidad })
      }).then(() => {
        esperandoDesconexion = true;
        actualizarUI();
        alert("Para tu seguridad, la desconexión requiere autorización de la Matriz. Esperando...");
      });
    }

    function iniciarAlerta() {
      if (navigator.vibrate) navigator.vibrate([300, 100, 300]);
      secondsLeft = 10;
      cancelTaps = 0;
      document.getElementById("timer-val").innerText = secondsLeft;
      document.getElementById("cancel-btn").innerText = "CANCELAR (Toca 2 veces)";
      document.getElementById("modal-panic").style.display = "flex";

      clearInterval(countdownTimer);
      countdownTimer = setInterval(() => {
        secondsLeft--;
        document.getElementById("timer-val").innerText = secondsLeft;
        if (secondsLeft <= 0) {
          clearInterval(countdownTimer);
          confirmarAlerta();
        }
      }, 1000);
    }

    function cancelarDobleToque() {
      cancelTaps++;
      if (cancelTaps >= 2) {
        clearInterval(countdownTimer);
        document.getElementById("modal-panic").style.display = "none";
        fetch("/taxi/cancelar-alerta", {
          method: "POST",
          headers: {"Content-Type": "application/json"},
          body: JSON.stringify({ unidad })
        });
        alert("Alerta cancelada (Falsa alarma registrada).");
      } else {
        document.getElementById("cancel-btn").innerText = "¡TOCA OTRA VEZ!";
      }
    }

    function confirmarAlerta() {
      document.getElementById("modal-panic").style.display = "none";
      fetch("/taxi/alerta", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({ unidad, socio_nombre: conductor, latitud: lat, longitud: lng })
      }).then(() => {
        alert("¡ALERTA TRANSMITIDA A LA MATRIZ Y GRUPOS DE AUXILIO!");
      });
    }

    // Modo Camuflaje (Calculadora)
    function toggleCamuflaje(show) {
      document.getElementById("calc-screen").style.display = show ? "flex" : "none";
    }

    function calcPress(val) {
      const disp = document.getElementById("c-display");
      if (val === 'C') {
        calcInput = "";
        disp.innerText = "0";
      } else if (val === '=') {
        if (calcInput === "1234") {
          toggleCamuflaje(false);
          calcInput = "";
          return;
        }
        if (calcInput === "911" || calcInput === "9999") {
          confirmarAlerta();
          disp.innerText = "Error";
          calcInput = "";
          return;
        }
        disp.innerText = "0";
        calcInput = "";
      } else {
        calcInput += val;
        disp.innerText = calcInput;
      }
    }
  </script>
</body>
</html>"""


# ════════════════════════════════════════════════════════════════════════════
# MAIN — ejecución directa
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    import uvicorn
    import socket

    # Mostrar IP local
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
    except Exception:
        ip = "0.0.0.0"

    print("=" * 60)
    print("  API AGRUPACION AGUARICO v6")
    print("=" * 60)
    print(f"  Local:   http://127.0.0.1:8000")
    print(f"  Red:     http://{ip}:8000")
    print(f"  Docs:    http://{ip}:8000/docs")
    print(f"  DB:      {DB_PATH}")
    print("=" * 60)
    print("  Pon esta IP en tu app Flutter:")
    print(f"  const String BASE_URL = 'http://{ip}:8000';")
    print("=" * 60)

    uvicorn.run("backend_api:app", host="0.0.0.0", port=8000, reload=True)
