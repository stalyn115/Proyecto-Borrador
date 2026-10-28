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

from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
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


class AsistenciaQR(BaseModel):
    codigo_qr: str          # Formato: AGUARICO|cedula|codigo_puesto  ó solo cédula


class AsistenciaTipear(BaseModel):
    cedula: str


class ReporteFiltros(BaseModel):
    fecha_desde: Optional[str] = ""   # dd/mm/yyyy
    fecha_hasta: Optional[str] = ""
    socio_id:    Optional[int] = None


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
def login(form: OAuth2PasswordRequestForm = Depends()):
    """
    Autenticación con usuario y contraseña.
    Devuelve JWT Bearer token.
    Compatible con el hash SHA-256 del sistema de escritorio.
    """
    conn = get_conn(); c = conn.cursor()
    c.execute("""SELECT id, username, rol, nombre, password
                 FROM usuarios WHERE username=?""", (form.username,))
    row = c.fetchone(); conn.close()

    if not row:
        raise HTTPException(status_code=401, detail="Usuario no encontrado")

    # Verificar con werkzeug (pbkdf2) o SHA-256 legacy
    if not verificar_pwd(form.password, row["password"]):
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
