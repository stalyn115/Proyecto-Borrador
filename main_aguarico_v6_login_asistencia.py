"""
╔══════════════════════════════════════════════════════════════════════╗
║      SISTEMA AGRUPACION AGUARICO  v6  —  LOGIN + ASISTENCIA         ║
║      Tkinter · SQLite3 · Pillow(opcional) · pywhatkit(opcional)      ║
╚══════════════════════════════════════════════════════════════════════╝
"""

import os
import sqlite3
import shutil
import webbrowser
import urllib.parse
import hashlib
from datetime import datetime, timedelta
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Pillow opcional ──────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ── Carpetas ─────────────────────────────────────────────────────────────────
DB         = "aguarico_v6.db"
DIR_FOTOS  = "fotos"
DIR_VEH    = "vehiculos_fotos"
DIR_DOCS   = "documentos_sanciones"
DIR_VENTAS = "documentos_ventas"
DIR_REP    = "reportes"

for _d in (DIR_FOTOS, DIR_VEH, DIR_DOCS, DIR_VENTAS, DIR_REP):
    os.makedirs(_d, exist_ok=True)

# ── Paleta ───────────────────────────────────────────────────────────────────
BG       = "#0f2746"
PANEL    = "#162d50"
CARD     = "#1e3a5f"
ACCENT   = "#1a73e8"
SUCCESS  = "#27ae60"
DANGER   = "#c0392b"
WARN     = "#f39c12"
TEXT     = "#ffffff"
SUBTEXT  = "#b0bec5"
ENTRY_BG = "#1c3358"
SIDEBAR  = "#0d1f3c"

FT       = ("Segoe UI", 14, "bold")
FB       = ("Segoe UI", 10, "bold")
FN       = ("Segoe UI", 9)
FS       = ("Segoe UI", 8)

# ════════════════════════════════════════════════════════════════════════════
# SEGURIDAD
# ════════════════════════════════════════════════════════════════════════════
def hash_pwd(pwd: str) -> str:
    return hashlib.sha256(pwd.encode()).hexdigest()


# ════════════════════════════════════════════════════════════════════════════
# BASE DE DATOS
# ════════════════════════════════════════════════════════════════════════════
def get_conn():
    return sqlite3.connect(DB)


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (
        id       INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE,
        password TEXT,
        rol      TEXT,
        nombre   TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS socios (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre        TEXT,
        apellido      TEXT,
        cedula        TEXT UNIQUE,
        codigo_puesto TEXT,
        rango         TEXT,
        estado        TEXT DEFAULT 'ACTIVO',
        unidad        TEXT,
        fecha_ingreso TEXT,
        foto          TEXT,
        whatsapp      TEXT,
        observacion   TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS vehiculos_historial (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        socio_id      INTEGER,
        puesto_codigo TEXT,
        tipo          TEXT,
        marca         TEXT,
        modelo        TEXT,
        placa         TEXT,
        color         TEXT,
        estado        TEXT DEFAULT 'Actual',
        km            TEXT,
        foto          TEXT,
        fecha_asig    TEXT,
        fecha_baja    TEXT,
        motivo_baja   TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS sanciones (
        id               INTEGER PRIMARY KEY AUTOINCREMENT,
        socio_id         INTEGER,
        tipo             TEXT,
        fecha            TEXT,
        descripcion      TEXT,
        sancion_aplicada TEXT,
        estado           TEXT DEFAULT 'Vigente',
        documento        TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS arrendatarios (
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        socio_id      INTEGER,
        puesto_codigo TEXT,
        nombre        TEXT,
        cedula        TEXT,
        telefono      TEXT,
        fecha_inicio  TEXT,
        fecha_fin     TEXT,
        estado        TEXT DEFAULT 'ACTIVO'
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS historial_puestos (
        id                    INTEGER PRIMARY KEY AUTOINCREMENT,
        puesto_codigo         TEXT,
        socio_anterior_id     INTEGER,
        socio_nuevo_id        INTEGER,
        socio_anterior_nombre TEXT,
        socio_nuevo_nombre    TEXT,
        fecha_venta           TEXT,
        valor                 TEXT,
        motivo                TEXT,
        documento             TEXT
    )""")

    c.execute("""CREATE TABLE IF NOT EXISTS asistencias (
        id             INTEGER PRIMARY KEY AUTOINCREMENT,
        socio_id       INTEGER,
        codigo_puesto  TEXT,
        nombre_socio   TEXT,
        fecha          TEXT,
        hora_entrada   TEXT,
        hora_salida    TEXT,
        estado         TEXT DEFAULT 'Entrada',
        registrado_por TEXT,
        observacion    TEXT
    )""")

    # Usuarios iniciales
    if not c.execute("SELECT id FROM usuarios LIMIT 1").fetchone():
        c.execute("INSERT INTO usuarios(username,password,rol,nombre) VALUES(?,?,?,?)",
                  ("admin",    hash_pwd("admin123"),      "Administrador", "Adm. Tnte. J. Paredes"))
        c.execute("INSERT INTO usuarios(username,password,rol,nombre) VALUES(?,?,?,?)",
                  ("staly",    hash_pwd("staly123"),      "Administrador", "Staly Aguarico"))
        c.execute("INSERT INTO usuarios(username,password,rol,nombre) VALUES(?,?,?,?)",
                  ("aguarico", hash_pwd("aguarico2024"),  "Operador",      "Operador Aguarico"))

    conn.commit()
    conn.close()


init_db()

# ════════════════════════════════════════════════════════════════════════════
# HELPERS
# ════════════════════════════════════════════════════════════════════════════
def copiar_archivo(origen, carpeta):
    if not origen or not os.path.isfile(origen):
        return ""
    nombre  = os.path.basename(origen)
    destino = os.path.join(carpeta, nombre)
    try:
        shutil.copy2(origen, destino)
    except Exception:
        pass
    return destino


def load_img(path, size):
    if not PIL_OK or not path or not os.path.isfile(path):
        return None
    try:
        img = Image.open(path)
        img.thumbnail(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def wa_open(numero, mensaje=""):
    tel = str(numero).strip().replace(" ", "")
    if not tel.startswith("+"):
        tel = "+593" + tel.lstrip("0")
    url = ("https://wa.me/" + tel.lstrip("+") +
           ("?text=" + urllib.parse.quote(mensaje) if mensaje else ""))
    webbrowser.open(url)


def btn(parent, text, cmd, bg=ACCENT, fg=TEXT, width=None,
        font=FN, pady=4, padx=6):
    kw = dict(text=text, command=cmd, bg=bg, fg=fg, font=font,
              relief="flat", cursor="hand2",
              activebackground=bg, activeforeground=fg,
              pady=pady, padx=padx)
    if width:
        kw["width"] = width
    return tk.Button(parent, **kw)


def label(parent, text, fg=TEXT, bg=BG, font=FN, **kw):
    return tk.Label(parent, text=text, fg=fg, bg=bg, font=font, **kw)


def entry(parent, width=28, textvariable=None, show=None):
    kw = dict(width=width, bg=ENTRY_BG, fg=TEXT,
              insertbackground="white", relief="flat", font=FN)
    if textvariable:
        kw["textvariable"] = textvariable
    if show:
        kw["show"] = show
    return tk.Entry(parent, **kw)


def lframe(parent, text, fg=TEXT, bg=PANEL):
    return tk.LabelFrame(parent, text=text, fg=fg, bg=bg,
                         font=FB, bd=1, relief="groove")


# ════════════════════════════════════════════════════════════════════════════
# DIÁLOGO SIMPLE (sin simpledialog)
# ════════════════════════════════════════════════════════════════════════════
class AskDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=BG)
        self.grab_set()
        self.resizable(False, False)
        self.result = None
        label(self, prompt, bg=BG).pack(padx=20, pady=10)
        self._e = entry(self, width=36)
        self._e.pack(padx=20, pady=4, ipady=4)
        f = tk.Frame(self, bg=BG); f.pack(pady=10)
        btn(f, "OK",       self._ok,      bg=SUCCESS, width=10).pack(side="left", padx=6)
        btn(f, "Cancelar", self.destroy,  bg=DANGER,  width=10).pack(side="left", padx=6)
        self._e.focus_set()
        self.bind("<Return>", lambda e: self._ok())

    def _ok(self):
        self.result = self._e.get()
        self.destroy()


def ask_string(parent, title, prompt):
    d = AskDialog(parent, title, prompt)
    parent.wait_window(d)
    return d.result


# ════════════════════════════════════════════════════════════════════════════
# LOGIN
# ════════════════════════════════════════════════════════════════════════════
class LoginWindow(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("AGRUPACION AGUARICO — Login")
        self.geometry("420x340")
        self.resizable(False, False)
        self.configure(bg=BG)
        self.usuario_logueado = None
        self._build()

    def _build(self):
        tk.Frame(self, bg=ACCENT, height=6).pack(fill="x")

        label(self, "AGRUPACION AGUARICO", bg=BG, fg=TEXT,
              font=("Segoe UI", 16, "bold")).pack(pady=(22, 2))
        label(self, "Sistema de Gestión v6", bg=BG, fg=SUBTEXT,
              font=FN).pack(pady=(0, 20))

        frm = tk.Frame(self, bg=BG)
        frm.pack()

        label(frm, "Usuario:", bg=BG).grid(row=0, column=0, sticky="w", pady=8)
        self._user = entry(frm, width=24)
        self._user.grid(row=0, column=1, padx=10, ipady=4)

        label(frm, "Contraseña:", bg=BG).grid(row=1, column=0, sticky="w", pady=8)
        self._pwd = entry(frm, width=24, show="●")
        self._pwd.grid(row=1, column=1, padx=10, ipady=4)

        self._msg = label(self, "", bg=BG, fg=DANGER, font=FS)
        self._msg.pack(pady=4)

        btn(self, "  INGRESAR  ", self._login,
            bg=ACCENT, font=FB, pady=8).pack(pady=6)

        self._user.focus_set()
        self.bind("<Return>", lambda e: self._login())

    def _login(self):
        user = self._user.get().strip()
        pwd  = self._pwd.get().strip()
        if not user or not pwd:
            self._msg.config(text="Complete usuario y contraseña.")
            return
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT id,username,rol,nombre FROM usuarios WHERE username=? AND password=?",
                  (user, hash_pwd(pwd)))
        row = c.fetchone(); conn.close()
        if row:
            self.usuario_logueado = {"id": row[0], "username": row[1],
                                     "rol": row[2], "nombre": row[3]}
            self.destroy()
        else:
            self._msg.config(text="Usuario o contraseña incorrectos.")
            self._pwd.delete(0, "end")


# ════════════════════════════════════════════════════════════════════════════
# APP PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════
class MainApp(tk.Tk):
    def __init__(self, usuario):
        super().__init__()
        self.usuario  = usuario
        self._refs    = []
        self.title("SISTEMA AGRUPACION AGUARICO v6")
        self.geometry("1340x760")
        self.configure(bg=BG)
        self._apply_styles()
        self._build()

    def _apply_styles(self):
        s = ttk.Style()
        s.theme_use("clam")
        s.configure("Treeview", background=PANEL, fieldbackground=PANEL,
                    foreground=TEXT, rowheight=26, font=FN)
        s.configure("Treeview.Heading", background=BG, foreground=TEXT, font=FB)
        s.map("Treeview", background=[("selected", ACCENT)])
        s.configure("TCombobox", fieldbackground=ENTRY_BG, background=ENTRY_BG,
                    foreground=TEXT, selectbackground=ACCENT)
        s.map("TCombobox", fieldbackground=[("readonly", ENTRY_BG)],
              foreground=[("readonly", TEXT)])
        s.configure("TScrollbar", background=PANEL, troughcolor=BG,
                    arrowcolor=TEXT)

    # ── Layout base ──────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=SIDEBAR, height=48)
        hdr.pack(fill="x")
        hdr.pack_propagate(False)
        label(hdr, "  🚗  AGRUPACION AGUARICO", bg=SIDEBAR, fg=TEXT,
              font=("Segoe UI", 13, "bold")).pack(side="left")
        label(hdr, f"  {self.usuario['nombre']}  |  {self.usuario['rol']}  ",
              bg=SIDEBAR, fg=SUBTEXT, font=FN).pack(side="right")

        body = tk.Frame(self, bg=BG)
        body.pack(fill="both", expand=True)

        # Sidebar
        self._sidebar = tk.Frame(body, bg=SIDEBAR, width=170)
        self._sidebar.pack(side="left", fill="y")
        self._sidebar.pack_propagate(False)

        self._content = tk.Frame(body, bg=BG)
        self._content.pack(side="left", fill="both", expand=True)

        menus = [
            ("🏠  Inicio",        self.show_inicio),
            ("📂  Expedientes",   self.show_expedientes),
            ("📋  Asistencia",    self.show_asistencia),
            ("🚗  Vehículos",     self.show_vehiculos),
            ("⚠️  Sanciones",     self.show_sanciones),
            ("📊  Reportes",      self.show_reportes),
            ("👥  Usuarios",      self.show_usuarios),
        ]
        for texto, cmd in menus:
            tk.Button(
                self._sidebar, text=texto, command=cmd,
                bg=SIDEBAR, fg=TEXT, font=FN, relief="flat",
                cursor="hand2", anchor="w", padx=14, pady=10,
                activebackground=ACCENT, activeforeground=TEXT,
                bd=0
            ).pack(fill="x")

        btn(self._sidebar, "🔒  Cerrar Sesión", self._logout,
            bg=DANGER, pady=8).pack(fill="x", side="bottom", padx=6, pady=6)

        self.show_inicio()

    def _clear(self):
        for w in self._content.winfo_children():
            w.destroy()
        self._refs.clear()

    def _logout(self):
        if messagebox.askyesno("Cerrar Sesión", "¿Cerrar sesión?"):
            self.destroy()
            _run_login()

    # ════════════════════════════════════════════════════════════════════════
    # INICIO
    # ════════════════════════════════════════════════════════════════════════
    def show_inicio(self):
        self._clear()
        f = tk.Frame(self._content, bg=BG)
        f.pack(fill="both", expand=True)

        # Banner imagen o texto
        # Ruta absoluta primero, luego relativa como fallback
        _script_dir = os.path.dirname(os.path.abspath(__file__))
        banner_path = os.path.join(_script_dir, "auto_deportivo_azul.jpg")
        if not os.path.isfile(banner_path):
            banner_path = "auto_deportivo_azul.jpg"  # fallback relativo

        if PIL_OK and os.path.isfile(banner_path):
            try:
                _img = Image.open(banner_path)
                _img = _img.resize((900, 320), Image.LANCZOS)
                ph   = ImageTk.PhotoImage(_img)
                self._refs.append(ph)
                tk.Label(f, image=ph, bg=BG).pack(pady=(0, 10))
            except Exception:
                ph = None
        else:
            ph = None

        if not ph:
            tk.Frame(f, bg="#0a1a3a", height=140).pack(fill="x")
            label(f, "AGRUPACION AGUARICO", bg=BG, fg=ACCENT,
                  font=("Segoe UI", 22, "bold")).pack(pady=(8, 0))
            label(f, "Sistema de Gestión v6", bg=BG, fg=SUBTEXT,
                  font=FN).pack(pady=(0, 10))

        label(f, f"Bienvenido, {self.usuario['nombre']}",
              bg=BG, fg=TEXT, font=FB).pack(pady=(0, 10))

        # Tarjetas
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM socios")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM socios WHERE estado='ACTIVO'")
        activos = c.fetchone()[0]
        hoy = datetime.now().strftime("%d/%m/%Y")
        c.execute("SELECT COUNT(DISTINCT socio_id) FROM asistencias WHERE fecha=?", (hoy,))
        asist_hoy = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM vehiculos_historial WHERE estado='Actual'")
        veh_act = c.fetchone()[0]
        conn.close()

        cards_f = tk.Frame(f, bg=BG)
        cards_f.pack()
        for titulo, valor, color in [
            ("Total Socios",      total,     ACCENT),
            ("Socios Activos",    activos,   SUCCESS),
            ("Asistencia Hoy",    asist_hoy, WARN),
            ("Vehículos Actuales",veh_act,   "#8e44ad"),
        ]:
            card = tk.Frame(cards_f, bg=color, padx=32, pady=20)
            card.pack(side="left", padx=12, pady=8)
            label(card, str(valor), bg=color, fg=TEXT,
                  font=("Segoe UI", 28, "bold")).pack()
            label(card, titulo, bg=color, fg=TEXT, font=FN).pack()

    # ════════════════════════════════════════════════════════════════════════
    # EXPEDIENTES
    # ════════════════════════════════════════════════════════════════════════
    def show_expedientes(self):
        self._clear()
        f = tk.Frame(self._content, bg=BG)
        f.pack(fill="both", expand=True, padx=10, pady=8)

        label(f, "EXPEDIENTES", bg=BG, fg=ACCENT, font=FT).pack(anchor="w")

        bar = tk.Frame(f, bg=BG); bar.pack(fill="x", pady=5)
        label(bar, "Buscar:", bg=BG).pack(side="left")
        self._exp_buscar = tk.StringVar()
        entry(bar, width=32, textvariable=self._exp_buscar).pack(
            side="left", padx=6, ipady=3)
        btn(bar, "🔍 Buscar",
            lambda: self._cargar_socios(self._exp_buscar.get())
            ).pack(side="left")
        btn(bar, "➕ Nuevo Socio", self._form_socio, bg=SUCCESS
            ).pack(side="right", padx=4)

        cols = ("ID","Código","Nombre","Apellido","Cédula","Rango","Unidad","Estado")
        self._tree_s = ttk.Treeview(f, columns=cols, show="headings", height=24)
        widths = [40,100,140,140,110,110,120,80]
        for col, w in zip(cols, widths):
            self._tree_s.heading(col, text=col)
            self._tree_s.column(col, width=w, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=self._tree_s.yview)
        self._tree_s.configure(yscrollcommand=sb.set)
        self._tree_s.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

        ctx = tk.Menu(self, tearoff=0)
        ctx.add_command(label="📂 Abrir Expediente", command=self._abrir_exp)
        ctx.add_command(label="✏️ Editar",           command=self._form_socio_editar)
        ctx.add_command(label="🗑️ Eliminar",         command=self._del_socio)
        self._tree_s.bind("<Button-3>", lambda e: ctx.post(e.x_root, e.y_root))
        self._tree_s.bind("<Double-1>", lambda e: self._abrir_exp())

        self._cargar_socios()

    def _cargar_socios(self, filtro=""):
        for r in self._tree_s.get_children():
            self._tree_s.delete(r)
        conn = get_conn(); c = conn.cursor()
        sql = ("SELECT id,codigo_puesto,nombre,apellido,cedula,"
               "rango,unidad,estado FROM socios")
        if filtro:
            sql += (" WHERE nombre LIKE ? OR apellido LIKE ?"
                    " OR cedula LIKE ? OR codigo_puesto LIKE ?")
            c.execute(sql, (f"%{filtro}%",)*4)
        else:
            c.execute(sql + " ORDER BY apellido")
        for row in c.fetchall():
            self._tree_s.insert("", "end", values=row)
        conn.close()

    def _abrir_exp(self):
        sel = self._tree_s.selection()
        if not sel: return
        sid = self._tree_s.item(sel[0])["values"][0]
        ExpedienteWindow(self, sid, self.usuario)

    def _form_socio_editar(self):
        sel = self._tree_s.selection()
        if not sel: return
        sid = self._tree_s.item(sel[0])["values"][0]
        self._form_socio(sid)

    def _del_socio(self):
        sel = self._tree_s.selection()
        if not sel: return
        sid = self._tree_s.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar", "¿Eliminar este socio?"):
            conn = get_conn(); c = conn.cursor()
            c.execute("DELETE FROM socios WHERE id=?", (sid,))
            conn.commit(); conn.close()
            self._cargar_socios()

    def _form_socio(self, socio_id=None):
        FormSocio(self, socio_id, callback=self._cargar_socios)

    # ════════════════════════════════════════════════════════════════════════
    # ASISTENCIA
    # ════════════════════════════════════════════════════════════════════════
    def show_asistencia(self):
        self._clear()
        f = tk.Frame(self._content, bg=BG)
        f.pack(fill="both", expand=True, padx=10, pady=8)

        label(f, "CONTROL DE ASISTENCIA", bg=BG, fg=ACCENT, font=FT).pack(anchor="w")

        # Panel de registro
        reg_lf = lframe(f, "Registrar Asistencia", bg=PANEL)
        reg_lf.pack(fill="x", pady=6)

        row1 = tk.Frame(reg_lf, bg=PANEL); row1.pack(fill="x", padx=8, pady=6)

        label(row1, "Socio:", bg=PANEL).pack(side="left")
        self._asist_socio_var = tk.StringVar()
        self._asist_cb = ttk.Combobox(reg_lf, textvariable=self._asist_socio_var,
                                       width=42, state="readonly", font=FN)
        self._asist_cb.pack(in_=row1, side="left", padx=6)
        self._asist_socio_ids = []
        self._cargar_socios_combo()

        row2 = tk.Frame(reg_lf, bg=PANEL); row2.pack(fill="x", padx=8, pady=4)
        label(row2, "Cédula:", bg=PANEL).pack(side="left")
        self._asist_ced = entry(row2, width=16)
        self._asist_ced.pack(side="left", padx=6, ipady=3)

        label(row2, "Obs.:", bg=PANEL).pack(side="left", padx=(10,0))
        self._asist_obs = entry(row2, width=26)
        self._asist_obs.pack(side="left", padx=6, ipady=3)

        btn_row = tk.Frame(reg_lf, bg=PANEL); btn_row.pack(fill="x", padx=8, pady=6)
        btn(btn_row, "✅ REGISTRAR ENTRADA",
            self._reg_entrada, bg=SUCCESS, font=FB, pady=6).pack(side="left", padx=4)
        btn(btn_row, "🚪 REGISTRAR SALIDA",
            self._reg_salida, bg=WARN, font=FB, pady=6).pack(side="left", padx=4)
        btn(btn_row, "🔄 Actualizar",
            self._cargar_asistencias, bg=PANEL).pack(side="left", padx=4)
        btn(btn_row, "🖨️ Historial Socio",
            self._imprimir_historial, bg=ACCENT).pack(side="left", padx=4)
        btn(btn_row, "📤 Exportar Hoy",
            self._exportar_hoy, bg="#8e44ad").pack(side="left", padx=4)

        # Estado del día
        self._asist_estado = label(f, "", bg=BG, fg=SUCCESS, font=FB)
        self._asist_estado.pack(anchor="w", pady=2)

        # Tabla
        cols = ("ID","Código","Nombre","Fecha","Entrada","Salida","Estado","Registrado por")
        self._tree_as = ttk.Treeview(f, columns=cols, show="headings", height=20)
        widths = [40,90,160,90,80,80,80,140]
        for col, w in zip(cols, widths):
            self._tree_as.heading(col, text=col)
            self._tree_as.column(col, width=w, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=self._tree_as.yview)
        self._tree_as.configure(yscrollcommand=sb.set)
        self._tree_as.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

        self._cargar_asistencias()

    def _cargar_socios_combo(self):
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT id,codigo_puesto,nombre,apellido FROM socios "
                  "WHERE estado='ACTIVO' ORDER BY apellido")
        rows = c.fetchall(); conn.close()
        self._asist_socio_ids = [r[0] for r in rows]
        nombres = [f"{r[1]} — {r[2]} {r[3]}" for r in rows]
        self._asist_cb["values"] = nombres
        if nombres:
            self._asist_cb.current(0)
            self._sync_cedula()
        self._asist_cb.bind("<<ComboboxSelected>>",
                             lambda e: self._sync_cedula())

    def _sync_cedula(self):
        idx = self._asist_cb.current()
        if idx < 0 or idx >= len(self._asist_socio_ids): return
        sid = self._asist_socio_ids[idx]
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT cedula FROM socios WHERE id=?", (sid,))
        row = c.fetchone(); conn.close()
        if row:
            self._asist_ced.delete(0, "end")
            self._asist_ced.insert(0, row[0])

    def _get_socio_sel(self):
        idx = self._asist_cb.current()
        if idx < 0 or idx >= len(self._asist_socio_ids):
            messagebox.showwarning("Aviso", "Seleccione un socio.")
            return None
        sid = self._asist_socio_ids[idx]
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT id,codigo_puesto,nombre,apellido,cedula FROM socios WHERE id=?",
                  (sid,))
        row = c.fetchone(); conn.close()
        if not row:
            return None
        return {"id": row[0], "codigo": row[1],
                "nombre": f"{row[2]} {row[3]}", "cedula": row[4]}

    def _reg_entrada(self):
        s = self._get_socio_sel()
        if not s: return
        hoy   = datetime.now().strftime("%d/%m/%Y")
        hora  = datetime.now().strftime("%H:%M:%S")
        # Verificar si ya tiene entrada hoy
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT id FROM asistencias WHERE socio_id=? AND fecha=?",
                  (s["id"], hoy))
        if c.fetchone():
            messagebox.showinfo("Info",
                f"{s['nombre']} ya tiene asistencia registrada hoy.")
            conn.close(); return
        c.execute("""INSERT INTO asistencias
                     (socio_id,codigo_puesto,nombre_socio,fecha,
                      hora_entrada,estado,registrado_por,observacion)
                     VALUES (?,?,?,?,?,?,?,?)""",
                  (s["id"], s["codigo"], s["nombre"], hoy, hora,
                   "Entrada", self.usuario["nombre"],
                   self._asist_obs.get()))
        conn.commit(); conn.close()
        self._asist_estado.config(
            text=f"✅ Entrada registrada: {s['nombre']}  {hora}")
        self._cargar_asistencias()

    def _reg_salida(self):
        s = self._get_socio_sel()
        if not s: return
        hoy  = datetime.now().strftime("%d/%m/%Y")
        hora = datetime.now().strftime("%H:%M:%S")
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT id FROM asistencias
                     WHERE socio_id=? AND fecha=? AND (hora_salida IS NULL OR hora_salida='')""",
                  (s["id"], hoy))
        row = c.fetchone()
        if not row:
            messagebox.showwarning("Aviso",
                "No se encontró entrada de hoy sin salida para este socio.")
            conn.close(); return
        c.execute("UPDATE asistencias SET hora_salida=?, estado='Completo' WHERE id=?",
                  (hora, row[0]))
        conn.commit(); conn.close()
        self._asist_estado.config(
            text=f"🚪 Salida registrada: {s['nombre']}  {hora}")
        self._cargar_asistencias()

    def _cargar_asistencias(self):
        for r in self._tree_as.get_children():
            self._tree_as.delete(r)
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT id,codigo_puesto,nombre_socio,fecha,
                            hora_entrada,hora_salida,estado,registrado_por
                     FROM asistencias
                     ORDER BY id DESC LIMIT 300""")
        for row in c.fetchall():
            self._tree_as.insert("", "end", values=row)
        conn.close()

    def _imprimir_historial(self):
        s = self._get_socio_sel()
        if not s: return
        sid  = s["id"]
        conn = get_conn(); c = conn.cursor()

        c.execute("SELECT * FROM socios WHERE id=?", (sid,))
        socio_row = c.fetchone()
        s_keys = ["id","nombre","apellido","cedula","codigo_puesto","rango",
                  "estado","unidad","fecha_ingreso","foto","whatsapp","observacion"]
        sd = dict(zip(s_keys, socio_row)) if socio_row else {}

        c.execute("""SELECT fecha,hora_entrada,hora_salida,estado,registrado_por,observacion
                     FROM asistencias WHERE socio_id=? ORDER BY fecha DESC""", (sid,))
        asist = c.fetchall()

        c.execute("""SELECT tipo,placa,marca,modelo,estado,km,fecha_asig
                     FROM vehiculos_historial WHERE socio_id=?""", (sid,))
        vehs = c.fetchall()

        c.execute("""SELECT tipo,fecha,descripcion,sancion_aplicada,estado
                     FROM sanciones WHERE socio_id=? ORDER BY fecha DESC""", (sid,))
        sans = c.fetchall()
        conn.close()

        fecha_arch = datetime.now().strftime("%Y%m%d_%H%M%S")
        codigo_limpio = str(sd.get("codigo_puesto","SIN")).replace("/","_")
        nombre_limpio = (f"{sd.get('nombre','')}_{sd.get('apellido','')}").replace(" ","_")
        archivo = os.path.join(DIR_REP,
            f"Historial_{codigo_limpio}_{nombre_limpio}_{fecha_arch}.txt")

        lines = [
            "="*60,
            "  AGRUPACION AGUARICO — HISTORIAL DE SOCIO",
            "="*60,
            f"  Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}",
            f"  Generado por: {self.usuario['nombre']}",
            "="*60,
            "",
            "DATOS PERSONALES",
            "-"*40,
            f"  Nombre:        {sd.get('nombre','')} {sd.get('apellido','')}",
            f"  Cédula:        {sd.get('cedula','')}",
            f"  Código Puesto: {sd.get('codigo_puesto','')}",
            f"  Rango:         {sd.get('rango','')}",
            f"  Estado:        {sd.get('estado','')}",
            f"  Unidad:        {sd.get('unidad','')}",
            f"  F. Ingreso:    {sd.get('fecha_ingreso','')}",
            f"  WhatsApp:      {sd.get('whatsapp','')}",
            f"  Observación:   {sd.get('observacion','')}",
            "",
            "ASISTENCIA",
            "-"*40,
        ]
        if asist:
            for a in asist:
                lines.append(
                    f"  {a[0]}  Entrada:{a[1]}  Salida:{a[2] or '---'}  "
                    f"Estado:{a[3]}  Por:{a[4]}  Obs:{a[5] or ''}")
        else:
            lines.append("  Sin registros de asistencia.")

        lines += ["", "VEHÍCULOS", "-"*40]
        if vehs:
            for v in vehs:
                lines.append(
                    f"  {v[0]}  Placa:{v[1]}  {v[2]} {v[3]}  "
                    f"Estado:{v[4]}  KM:{v[5]}  F.Asig:{v[6]}")
        else:
            lines.append("  Sin vehículos registrados.")

        lines += ["", "SANCIONES", "-"*40]
        if sans:
            for sn in sans:
                lines.append(
                    f"  {sn[0]}  Fecha:{sn[1]}  {sn[2]}  "
                    f"Sanción:{sn[3]}  Estado:{sn[4]}")
        else:
            lines.append("  Sin sanciones.")

        lines += ["", "="*60, "  FIN DEL HISTORIAL", "="*60]

        try:
            with open(archivo, "w", encoding="utf-8") as fp:
                fp.write("\n".join(lines))
            messagebox.showinfo("Historial Generado",
                f"Archivo guardado en:\n{archivo}")
            try:
                os.startfile(archivo)
            except Exception:
                webbrowser.open(archivo)
        except Exception as ex:
            messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{ex}")

    def _exportar_hoy(self):
        hoy      = datetime.now().strftime("%d/%m/%Y")
        hoy_file = datetime.now().strftime("%Y%m%d")
        archivo  = os.path.join(DIR_REP, f"Asistencia_{hoy_file}.txt")
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT codigo_puesto,nombre_socio,fecha,
                            hora_entrada,hora_salida,estado,registrado_por
                     FROM asistencias WHERE fecha=? ORDER BY hora_entrada""", (hoy,))
        rows = c.fetchall(); conn.close()

        lines = [
            "="*60,
            f"  ASISTENCIA DEL DÍA  {hoy}",
            "="*60,
        ]
        for r in rows:
            lines.append(
                f"  {r[0]}  {r[1]}  Ent:{r[3]}  Sal:{r[4] or '---'}  {r[5]}")
        lines += ["", f"  Total: {len(rows)} registros", "="*60]

        try:
            with open(archivo, "w", encoding="utf-8") as fp:
                fp.write("\n".join(lines))
            messagebox.showinfo("Exportado", f"Asistencia guardada en:\n{archivo}")
            try:
                os.startfile(archivo)
            except Exception:
                webbrowser.open(archivo)
        except Exception as ex:
            messagebox.showerror("Error", str(ex))

    # ════════════════════════════════════════════════════════════════════════
    # VEHÍCULOS GLOBAL
    # ════════════════════════════════════════════════════════════════════════
    def show_vehiculos(self):
        self._clear()
        f = tk.Frame(self._content, bg=BG)
        f.pack(fill="both", expand=True, padx=10, pady=8)

        label(f, "VEHÍCULOS REGISTRADOS", bg=BG, fg=ACCENT, font=FT).pack(anchor="w")
        btn(f, "🔄 Actualizar", lambda: self._reload_veh(tree),
            bg=PANEL).pack(anchor="e", pady=4)

        cols = ("ID","Socio","Puesto","Tipo","Placa","Marca","Modelo","Estado","KM","F.Asig")
        tree = ttk.Treeview(f, columns=cols, show="headings", height=26)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=95, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self._reload_veh(tree)

    def _reload_veh(self, tree):
        for r in tree.get_children(): tree.delete(r)
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT v.id, s.nombre||' '||s.apellido, v.puesto_codigo,
                            v.tipo, v.placa, v.marca, v.modelo,
                            v.estado, v.km, v.fecha_asig
                     FROM vehiculos_historial v
                     LEFT JOIN socios s ON s.id=v.socio_id
                     ORDER BY v.estado, v.fecha_asig DESC""")
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    # ════════════════════════════════════════════════════════════════════════
    # SANCIONES GLOBAL
    # ════════════════════════════════════════════════════════════════════════
    def show_sanciones(self):
        self._clear()
        f = tk.Frame(self._content, bg=BG)
        f.pack(fill="both", expand=True, padx=10, pady=8)

        label(f, "SANCIONES", bg=BG, fg=ACCENT, font=FT).pack(anchor="w")
        btn(f, "🔄 Actualizar", lambda: self._reload_san(tree),
            bg=PANEL).pack(anchor="e", pady=4)

        cols = ("ID","Socio","Tipo","Fecha","Descripción","Sanción Aplicada","Estado")
        tree = ttk.Treeview(f, columns=cols, show="headings", height=26)
        widths = [40,160,100,90,200,160,80]
        for col, w in zip(cols, widths):
            tree.heading(col, text=col)
            tree.column(col, width=w, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self._reload_san(tree)

    def _reload_san(self, tree):
        for r in tree.get_children(): tree.delete(r)
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT sa.id, s.nombre||' '||s.apellido,
                            sa.tipo, sa.fecha, sa.descripcion,
                            sa.sancion_aplicada, sa.estado
                     FROM sanciones sa
                     LEFT JOIN socios s ON s.id=sa.socio_id
                     ORDER BY sa.fecha DESC""")
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    # ════════════════════════════════════════════════════════════════════════
    # REPORTES + NOTIFICACIONES WHATSAPP GRUPO
    # ════════════════════════════════════════════════════════════════════════
    def show_reportes(self):
        self._clear()
        f = tk.Frame(self._content, bg=BG)
        f.pack(fill="both", expand=True, padx=10, pady=8)

        label(f, "REPORTES Y NOTIFICACIONES", bg=BG, fg=ACCENT, font=FT).pack(anchor="w")

        # Estadísticas
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM socios")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM socios WHERE estado='ACTIVO'")
        act = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM sanciones WHERE estado='Vigente'")
        san = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM historial_puestos")
        ventas = c.fetchone()[0]
        hoy = datetime.now().strftime("%d/%m/%Y")
        c.execute("SELECT COUNT(*) FROM asistencias WHERE fecha=?", (hoy,))
        asist = c.fetchone()[0]
        conn.close()

        cards_f = tk.Frame(f, bg=BG); cards_f.pack(pady=8)
        for titulo, val, color in [
            ("Total Socios",     total,  ACCENT),
            ("Activos",          act,    SUCCESS),
            ("Sanciones Vigentes",san,   WARN),
            ("Ventas Registradas",ventas,DANGER),
            ("Asistencia Hoy",   asist,  "#8e44ad"),
        ]:
            card = tk.Frame(cards_f, bg=color, padx=22, pady=16)
            card.pack(side="left", padx=8)
            label(card, str(val), bg=color, fg=TEXT,
                  font=("Segoe UI", 22, "bold")).pack()
            label(card, titulo, bg=color, fg=TEXT, font=FS).pack()

        # ── Notificaciones WhatsApp Grupo ─────────────────────────────────
        wa_lf = lframe(f, "📢  Notificaciones WhatsApp — Grupo Aguarico",
                       fg=SUCCESS, bg=PANEL)
        wa_lf.pack(fill="x", pady=12)

        row1 = tk.Frame(wa_lf, bg=PANEL); row1.pack(fill="x", padx=10, pady=6)
        label(row1, "Link/ID del grupo:", bg=PANEL).pack(side="left")
        self._wa_link_var = tk.StringVar(
            value="https://chat.whatsapp.com/It1cuVVJvL5K4B7pLtSsWf")
        e_link = entry(row1, width=50, textvariable=self._wa_link_var)
        e_link.pack(side="left", padx=8, ipady=3)
        label(row1,
              "  (Ej: https://chat.whatsapp.com/XXXX  ó  120363XXXX@g.us)",
              bg=PANEL, fg=SUBTEXT, font=FS).pack(side="left")

        row2 = tk.Frame(wa_lf, bg=PANEL); row2.pack(fill="x", padx=10, pady=4)
        label(row2, "Mensaje:", bg=PANEL).pack(side="left", anchor="n", pady=4)
        self._wa_msg_t = tk.Text(wa_lf, width=70, height=4,
                                  bg=ENTRY_BG, fg=TEXT,
                                  insertbackground="white", relief="flat",
                                  font=FN)
        self._wa_msg_t.pack(padx=10, pady=4)
        self._wa_msg_t.insert("1.0",
            "Estimados miembros de la Agrupación Aguarico, "
            "les informamos que...")

        btn_row = tk.Frame(wa_lf, bg=PANEL); btn_row.pack(fill="x", padx=10, pady=8)
        btn(btn_row, "📋 Copiar y Abrir Grupo",
            self._wa_copiar_abrir, bg=SUCCESS, font=FB, pady=6
            ).pack(side="left", padx=4)
        btn(btn_row, "📢 ENVIAR AUTOMÁTICO AL GRUPO (pywhatkit)",
            self._wa_enviar_auto, bg="#128C7E", font=FB, pady=6
            ).pack(side="left", padx=4)
        btn(btn_row, "📱 Enviar a número individual",
            self._wa_individual, bg=ACCENT, pady=6
            ).pack(side="left", padx=4)

        # Botón grande grupo Aguarico
        btn(wa_lf, "📢  ENVIAR NOTIFICACION AL GRUPO AGUARICO",
            self._wa_enviar_grupo_aguarico,
            bg="#25D366", fg=TEXT, font=("Segoe UI", 11, "bold"), pady=10
            ).pack(fill="x", padx=10, pady=(4, 10))

        # Historial ventas
        label(f, "Historial de Ventas de Puestos",
              bg=BG, fg=TEXT, font=FB).pack(anchor="w", pady=(14, 4))
        cols = ("Puesto","Anterior","Nuevo","Fecha","Valor","Motivo")
        tree_v = ttk.Treeview(f, columns=cols, show="headings", height=8)
        for col in cols:
            tree_v.heading(col, text=col)
            tree_v.column(col, width=150, anchor="center")
        sb_v = ttk.Scrollbar(f, orient="vertical", command=tree_v.yview)
        tree_v.configure(yscrollcommand=sb_v.set)
        tree_v.pack(side="left", fill="x", expand=True, pady=4)
        sb_v.pack(side="left", fill="y")

        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT puesto_codigo,socio_anterior_nombre,
                            socio_nuevo_nombre,fecha_venta,valor,motivo
                     FROM historial_puestos ORDER BY fecha_venta DESC""")
        for row in c.fetchall():
            tree_v.insert("", "end", values=row)
        conn.close()

    def _wa_get_mensaje(self):
        return self._wa_msg_t.get("1.0", "end-1c").strip()

    def _wa_get_link(self):
        return self._wa_link_var.get().strip()

    def _wa_copiar_abrir(self):
        msg  = self._wa_get_mensaje()
        link = self._wa_get_link()
        if not msg:
            messagebox.showwarning("Aviso", "Escribe un mensaje primero."); return
        if not link:
            messagebox.showwarning("Aviso", "Ingresa el link o ID del grupo."); return
        try:
            self.clipboard_clear()
            self.clipboard_append(msg)
            self.update()
        except Exception:
            pass
        # Si es link de invitación lo abrimos directamente
        if link.startswith("http"):
            webbrowser.open(link)
        else:
            # Intentar abrir wa.me con el ID (no siempre funciona para grupos)
            webbrowser.open(f"https://web.whatsapp.com/")
        messagebox.showinfo("✅ Mensaje Copiado",
            "El mensaje fue copiado al portapapeles.\n\n"
            "1. WhatsApp Web se abrirá en el navegador.\n"
            "2. Entra al grupo Aguarico.\n"
            "3. Pega el mensaje con  Ctrl+V  y envía.")

    def _wa_enviar_auto(self):
        msg  = self._wa_get_mensaje()
        link = self._wa_get_link()
        if not msg:
            messagebox.showwarning("Aviso", "Escribe un mensaje primero."); return

        # Extraer ID de grupo si es @g.us, si no tratar de extraer del link
        grupo_id = link
        if link.startswith("http"):
            # No podemos extraer el ID interno desde el link de invitación
            messagebox.showwarning("ID de Grupo Necesario",
                "Para el envío automático necesitas el ID interno del grupo "
                "(formato: 120363XXXXXXXX@g.us).\n\n"
                "Cómo obtenerlo:\n"
                "1. Exporta el chat del grupo desde WhatsApp.\n"
                "2. En el archivo verás el número de grupo.\n"
                "3. Pégalo en el campo Link/ID con el formato: "
                "120363XXXXXXXX@g.us\n\n"
                "Por ahora usa el botón 'Copiar y Abrir Grupo'.")
            return

        try:
            import pywhatkit as kit  # noqa
            ahora   = datetime.now() + timedelta(minutes=2)
            hora    = ahora.hour
            minuto  = ahora.minute
            messagebox.showinfo("Enviando...",
                f"Se programará el mensaje para las {hora:02d}:{minuto:02d}.\n"
                "NO cierres el navegador mientras se envía.")
            kit.sendwhatmsg_to_group(grupo_id, msg, hora, minuto,
                                      wait_time=15, tab_close=False)
            messagebox.showinfo("OK",
                "Mensaje programado correctamente.\n"
                "Verifica que WhatsApp Web esté iniciado sesión.")
        except ImportError:
            messagebox.showerror("pywhatkit no instalado",
                "Instala pywhatkit primero:\n\n"
                "   pip install pywhatkit\n\n"
                "Luego reinicia la aplicación.\n\n"
                "Alternativa: usa el botón 'Copiar y Abrir Grupo'.")
        except Exception as ex:
            messagebox.showerror("Error al enviar",
                f"No se pudo enviar al grupo:\n{ex}\n\n"
                "Verifica:\n"
                "• WhatsApp Web abierto e iniciado sesión\n"
                "• El ID del grupo es correcto (formato: XXXXXXX@g.us)\n"
                "• pywhatkit instalado: pip install pywhatkit")

    def _wa_enviar_grupo_aguarico(self):
        link    = "https://chat.whatsapp.com/It1cuVVJvL5K4B7pLtSsWf"
        mensaje = self._wa_msg_t.get("1.0", "end").strip()
        if not mensaje:
            messagebox.showwarning("Falta", "Escribe el mensaje primero.")
            return
        # 1. Copiar al portapapeles
        try:
            self.clipboard_clear()
            self.clipboard_append(mensaje)
            self.update()
        except Exception:
            pass
        # 2. Abrir el grupo
        webbrowser.open(link)
        messagebox.showinfo(
            "Listo para enviar al grupo AGUARICO",
            f"Se abrió tu grupo de WhatsApp.\n\n"
            f"Mensaje copiado:\n{mensaje[:100]}"
            f"{'...' if len(mensaje) > 100 else ''}\n\n"
            f"1. Espera que abra el grupo\n"
            f"2. Da  Ctrl+V  para pegar\n"
            f"3. Da  Enter  para enviar\n\n"
            f"El mensaje ya está en tu portapapeles.")

    def _wa_individual(self):
        win = tk.Toplevel(self)
        win.title("Enviar a número individual")
        win.configure(bg=BG)
        win.grab_set()
        label(win, "Número (ej: 0991234567 ó +593991234567):",
              bg=BG).pack(padx=16, pady=(12,4))
        e_tel = entry(win, width=30)
        e_tel.pack(padx=16, ipady=4)
        label(win, "Mensaje:", bg=BG).pack(padx=16, pady=(8,2))
        t_msg = tk.Text(win, width=36, height=4, bg=ENTRY_BG, fg=TEXT,
                        insertbackground="white", relief="flat")
        t_msg.insert("1.0", self._wa_get_mensaje())
        t_msg.pack(padx=16)

        def enviar():
            tel = e_tel.get().strip()
            msg = t_msg.get("1.0","end-1c").strip()
            if not tel or not msg:
                messagebox.showwarning("Aviso","Completa número y mensaje.")
                return
            wa_open(tel, msg)
            win.destroy()

        btn(win, "📱 Enviar por WhatsApp", enviar,
            bg=SUCCESS, pady=6).pack(pady=10)

    # ════════════════════════════════════════════════════════════════════════
    # USUARIOS
    # ════════════════════════════════════════════════════════════════════════
    def show_usuarios(self):
        self._clear()
        if self.usuario["rol"] != "Administrador":
            label(self._content, "Acceso restringido a Administradores.",
                  bg=BG, fg=DANGER, font=FB).pack(pady=40)
            return

        f = tk.Frame(self._content, bg=BG)
        f.pack(fill="both", expand=True, padx=10, pady=8)
        label(f, "GESTIÓN DE USUARIOS", bg=BG, fg=ACCENT, font=FT).pack(anchor="w")

        bar = tk.Frame(f, bg=BG); bar.pack(fill="x", pady=6)
        btn(bar, "➕ Nuevo Usuario", self._form_usuario, bg=SUCCESS).pack(side="right")

        cols = ("ID","Username","Rol","Nombre")
        self._tree_usr = ttk.Treeview(f, columns=cols, show="headings", height=20)
        for col in cols:
            self._tree_usr.heading(col, text=col)
            self._tree_usr.column(col, width=200, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=self._tree_usr.yview)
        self._tree_usr.configure(yscrollcommand=sb.set)
        self._tree_usr.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")

        ctx = tk.Menu(self, tearoff=0)
        ctx.add_command(label="✏️ Editar",   command=self._edit_usuario)
        ctx.add_command(label="🗑️ Eliminar", command=self._del_usuario)
        self._tree_usr.bind("<Button-3>", lambda e: ctx.post(e.x_root, e.y_root))

        self._cargar_usuarios()

    def _cargar_usuarios(self):
        for r in self._tree_usr.get_children():
            self._tree_usr.delete(r)
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT id,username,rol,nombre FROM usuarios")
        for row in c.fetchall():
            self._tree_usr.insert("", "end", values=row)
        conn.close()

    def _form_usuario(self, uid=None):
        FormUsuario(self, uid, callback=self._cargar_usuarios)

    def _edit_usuario(self):
        sel = self._tree_usr.selection()
        if not sel: return
        uid = self._tree_usr.item(sel[0])["values"][0]
        self._form_usuario(uid)

    def _del_usuario(self):
        sel = self._tree_usr.selection()
        if not sel: return
        uid = self._tree_usr.item(sel[0])["values"][0]
        if uid == self.usuario["id"]:
            messagebox.showerror("Error","No puedes eliminar tu propio usuario."); return
        if messagebox.askyesno("Confirmar","¿Eliminar usuario?"):
            conn = get_conn(); c = conn.cursor()
            c.execute("DELETE FROM usuarios WHERE id=?", (uid,))
            conn.commit(); conn.close()
            self._cargar_usuarios()


# ════════════════════════════════════════════════════════════════════════════
# FORMULARIO SOCIO
# ════════════════════════════════════════════════════════════════════════════
class FormSocio(tk.Toplevel):
    def __init__(self, parent, socio_id=None, callback=None):
        super().__init__(parent)
        self.title("Datos del Socio")
        self.configure(bg=BG)
        self.grab_set()
        self.resizable(False, False)
        self._sid      = socio_id
        self._callback = callback
        self._refs     = []
        self._foto_var = tk.StringVar()
        self._datos    = {}
        if socio_id:
            conn = get_conn(); c = conn.cursor()
            c.execute("SELECT * FROM socios WHERE id=?", (socio_id,))
            row = c.fetchone(); conn.close()
            if row:
                keys = ["id","nombre","apellido","cedula","codigo_puesto","rango",
                        "estado","unidad","fecha_ingreso","foto","whatsapp","observacion"]
                self._datos = dict(zip(keys, row))
        self._build()

    def _build(self):
        d = self._datos
        campos = [
            ("Nombre",        "nombre"),
            ("Apellido",      "apellido"),
            ("Cédula",        "cedula"),
            ("Código Puesto", "codigo_puesto"),
            ("Rango",         "rango"),
            ("Unidad",        "unidad"),
            ("Fecha Ingreso", "fecha_ingreso"),
            ("WhatsApp",      "whatsapp"),
        ]
        self._entries = {}
        lf_main = tk.Frame(self, bg=BG, padx=18, pady=14)
        lf_main.pack(side="left")

        for i, (lbl, key) in enumerate(campos):
            label(lf_main, lbl, bg=BG, anchor="w").grid(
                row=i, column=0, sticky="w", pady=3)
            e = entry(lf_main, width=30)
            e.insert(0, d.get(key,""))
            e.grid(row=i, column=1, padx=8, pady=3, ipady=3)
            self._entries[key] = e

        row_e = len(campos)
        label(lf_main, "Estado", bg=BG).grid(row=row_e, column=0, sticky="w", pady=3)
        self._estado_var = tk.StringVar(value=d.get("estado","ACTIVO"))
        ttk.Combobox(lf_main, textvariable=self._estado_var,
                     values=["ACTIVO","INACTIVO","SUSPENDIDO","VENDIDO"],
                     state="readonly", width=28).grid(
            row=row_e, column=1, padx=8, pady=3)

        label(lf_main, "Observación", bg=BG).grid(
            row=row_e+1, column=0, sticky="nw", pady=3)
        self._obs = tk.Text(lf_main, width=30, height=3,
                            bg=ENTRY_BG, fg=TEXT, insertbackground="white",
                            relief="flat", font=FN)
        self._obs.insert("1.0", d.get("observacion",""))
        self._obs.grid(row=row_e+1, column=1, padx=8, pady=3)

        btn(lf_main, "💾  Guardar", self._guardar,
            bg=SUCCESS, width=22, pady=6).grid(
            row=row_e+2, column=0, columnspan=2, pady=12)

        # Foto
        right = tk.Frame(self, bg=BG, padx=14, pady=14)
        right.pack(side="left", anchor="n")
        label(right, "Foto", bg=BG, font=FB).pack()
        self._foto_lbl = tk.Label(right, bg=PANEL, width=18, height=10,
                                   text="Sin foto", fg=SUBTEXT)
        self._foto_lbl.pack(pady=5)
        self._foto_var.set(d.get("foto",""))
        self._preview_foto()
        btn(right, "📷 Seleccionar foto", self._sel_foto, bg=ACCENT).pack()

    def _sel_foto(self):
        f = filedialog.askopenfilename(
            filetypes=[("Imágenes","*.jpg *.jpeg *.png *.bmp")])
        if f:
            self._foto_var.set(f)
            self._preview_foto()

    def _preview_foto(self):
        ph = load_img(self._foto_var.get(), (160, 130))
        if ph:
            self._refs.append(ph)
            self._foto_lbl.config(image=ph, text="", width=160, height=130)

    def _guardar(self):
        foto_dest = (copiar_archivo(self._foto_var.get(), DIR_FOTOS)
                     if self._foto_var.get() else self._datos.get("foto",""))
        vals = (
            self._entries["nombre"].get(),
            self._entries["apellido"].get(),
            self._entries["cedula"].get(),
            self._entries["codigo_puesto"].get(),
            self._entries["rango"].get(),
            self._estado_var.get(),
            self._entries["unidad"].get(),
            self._entries["fecha_ingreso"].get() or datetime.now().strftime("%Y-%m-%d"),
            foto_dest,
            self._entries["whatsapp"].get(),
            self._obs.get("1.0","end-1c"),
        )
        conn = get_conn(); c = conn.cursor()
        try:
            if self._sid:
                c.execute("""UPDATE socios SET nombre=?,apellido=?,cedula=?,
                             codigo_puesto=?,rango=?,estado=?,unidad=?,
                             fecha_ingreso=?,foto=?,whatsapp=?,observacion=?
                             WHERE id=?""", vals + (self._sid,))
            else:
                c.execute("""INSERT INTO socios
                             (nombre,apellido,cedula,codigo_puesto,rango,estado,
                              unidad,fecha_ingreso,foto,whatsapp,observacion)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?)""", vals)
            conn.commit()
            messagebox.showinfo("OK","Socio guardado.")
            self.destroy()
            if self._callback: self._callback()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error","Cédula ya registrada.")
        finally:
            conn.close()


# ════════════════════════════════════════════════════════════════════════════
# EXPEDIENTE WINDOW (3 COLUMNAS)
# ════════════════════════════════════════════════════════════════════════════
class ExpedienteWindow(tk.Toplevel):
    def __init__(self, parent, socio_id, usuario):
        super().__init__(parent)
        self._sid     = socio_id
        self._usuario = usuario
        self._refs    = []
        self._cargar_socio()
        nom = f"{self._s.get('nombre','')} {self._s.get('apellido','')}"
        self.title(f"Expediente — {nom}")
        self.geometry("1360x840")
        self.configure(bg=BG)
        self._build()

    def _cargar_socio(self):
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT * FROM socios WHERE id=?", (self._sid,))
        row = c.fetchone(); conn.close()
        keys = ["id","nombre","apellido","cedula","codigo_puesto","rango",
                "estado","unidad","fecha_ingreso","foto","whatsapp","observacion"]
        self._s = dict(zip(keys, row)) if row else {}

    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=BG, pady=8)
        hdr.pack(fill="x")
        label(hdr,
              f"EXPEDIENTE PERSONAL  —  "
              f"{self._s.get('nombre','')} {self._s.get('apellido','')}",
              bg=BG, fg=TEXT, font=FT).pack(side="left", padx=18)
        btn(hdr, "✏️ Editar datos",
            lambda: FormSocio(self, self._sid, callback=self._refresh),
            bg=ACCENT).pack(side="right", padx=10)

        # Contenedor de 3 columnas
        outer = tk.Frame(self, bg=BG)
        outer.pack(fill="both", expand=True, padx=6, pady=6)

        def make_scroll_col(parent, width=None):
            frame = tk.Frame(parent, bg=BG)
            if width:
                frame.config(width=width)
                frame.pack_propagate(False)
            frame.pack(side="left", fill="both",
                       expand=(width is None), padx=3)
            canvas = tk.Canvas(frame, bg=BG, highlightthickness=0)
            sb = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
            inner = tk.Frame(canvas, bg=BG)
            inner.bind("<Configure>", lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")))
            canvas.create_window((0, 0), window=inner, anchor="nw")
            canvas.configure(yscrollcommand=sb.set)
            canvas.pack(side="left", fill="both", expand=True)
            sb.pack(side="right", fill="y")
            return inner

        self._col1 = make_scroll_col(outer, width=330)
        self._col2 = make_scroll_col(outer)
        self._col3 = make_scroll_col(outer, width=350)

        self._build_col1()
        self._build_col2()
        self._build_col3()

    # ── Columna 1 — DATOS DEL PERSONAL ──────────────────────────────────────
    def _build_col1(self):
        p  = self._col1
        s  = self._s

        label(p, "DATOS DEL PERSONAL",
              bg=BG, fg=ACCENT, font=FB).pack(pady=(6, 4))

        # Foto
        foto_f = tk.Frame(p, bg=PANEL, width=320, height=250)
        foto_f.pack(pady=4)
        foto_f.pack_propagate(False)
        self._foto_lbl_exp = tk.Label(foto_f, bg=PANEL,
                                       text="Sin foto", fg=SUBTEXT)
        self._foto_lbl_exp.pack(expand=True)
        ph = load_img(s.get("foto",""), (320, 250))
        if ph:
            self._refs.append(ph)
            self._foto_lbl_exp.config(image=ph, text="")

        # Info
        info_f = lframe(p, "Información Personal")
        info_f.pack(fill="x", padx=4, pady=4)

        def fila(par, etq, val, vc=TEXT):
            r = tk.Frame(par, bg=PANEL); r.pack(fill="x", padx=8, pady=2)
            label(r, etq+":", bg=PANEL, fg=SUBTEXT, font=FS,
                  width=14, anchor="w").pack(side="left")
            label(r, str(val or "—"), bg=PANEL, fg=vc, font=FB,
                  anchor="w").pack(side="left")

        fila(info_f, "Nombre",
             f"{s.get('nombre','')} {s.get('apellido','')}")
        fila(info_f, "Cédula",        s.get("cedula",""))
        fila(info_f, "Código",        s.get("codigo_puesto",""))
        fila(info_f, "Rango",         s.get("rango",""))
        fila(info_f, "Estado",        s.get("estado",""),
             SUCCESS if s.get("estado")=="ACTIVO" else DANGER)
        fila(info_f, "Unidad",        s.get("unidad",""))
        fila(info_f, "F. Ingreso",    s.get("fecha_ingreso",""))

        if s.get("whatsapp"):
            wa_f = tk.Frame(info_f, bg=PANEL); wa_f.pack(fill="x", padx=8, pady=4)
            btn(wa_f, f"📱 WhatsApp {s.get('whatsapp','')}",
                lambda: wa_open(s.get("whatsapp","")),
                bg="#25D366").pack(fill="x")

        # Arrendatario
        arr_lf = lframe(p, "ARRENDATARIO", fg=WARN)
        arr_lf.pack(fill="x", padx=4, pady=6)

        self._arr_var = tk.StringVar(value="— Sin arrendatario activo —")
        self._arr_cb  = ttk.Combobox(arr_lf, textvariable=self._arr_var,
                                      state="readonly", width=36, font=FN)
        self._arr_cb.pack(padx=6, pady=4)
        self._cargar_arr_combo()

        arr_btn = tk.Frame(arr_lf, bg=PANEL); arr_btn.pack(fill="x", padx=6, pady=4)
        btn(arr_btn, "+ Agregar Arrendatario",
            self._form_arr, bg=ACCENT).pack(side="left", padx=(0,4))
        btn(arr_btn, "👁 Ver Arrendatarios",
            self._ver_arr, bg=PANEL).pack(side="left")

        # Venta de Puesto
        btn(p, "🔴  VENTA DE PUESTO",
            self._venta_puesto, bg=DANGER,
            width=36, pady=8, font=FB).pack(pady=8, padx=4, fill="x")

        # Historial del puesto
        self._hist_lf = lframe(p, "Historial de este Puesto")
        self._hist_lf.pack(fill="x", padx=4, pady=4)
        self._cargar_hist_puesto()

    def _cargar_arr_combo(self):
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT id, nombre||' - '||cedula
                     FROM arrendatarios
                     WHERE socio_id=? AND estado='ACTIVO'""", (self._sid,))
        rows = c.fetchall(); conn.close()
        self._arr_ids = [r[0] for r in rows]
        nombres       = [r[1] for r in rows]
        self._arr_cb["values"] = (nombres if nombres
                                  else ["— Sin arrendatario activo —"])
        if nombres: self._arr_cb.current(0)

    def _cargar_hist_puesto(self):
        for w in self._hist_lf.winfo_children():
            w.destroy()
        label(self._hist_lf, "Historial de este Puesto",
              bg=PANEL, fg=TEXT, font=FB).pack()
        codigo = self._s.get("codigo_puesto","")
        conn   = get_conn(); c = conn.cursor()
        c.execute("""SELECT fecha_venta,socio_anterior_nombre,
                            socio_nuevo_nombre,valor,motivo
                     FROM historial_puestos
                     WHERE puesto_codigo=? ORDER BY fecha_venta DESC""",
                  (codigo,))
        rows = c.fetchall(); conn.close()
        if not rows:
            label(self._hist_lf, "Sin historial registrado.",
                  bg=PANEL, fg=SUBTEXT, font=FS).pack(padx=6, pady=4)
        for row in rows:
            f_d, ant, nvo, val, mot = row
            card = tk.Frame(self._hist_lf, bg=CARD, pady=4, padx=6)
            card.pack(fill="x", padx=6, pady=2)
            label(card, f"📅 {f_d}  💰 ${val}",
                  bg=CARD, fg=WARN, font=FS).pack(anchor="w")
            label(card, f"  {ant} → {nvo}",
                  bg=CARD, fg=TEXT, font=FS).pack(anchor="w")
            if mot:
                label(card, f"  Motivo: {mot}",
                      bg=CARD, fg=SUBTEXT, font=FS).pack(anchor="w")

    def _form_arr(self):
        FormArrendatario(self, self._sid,
                         self._s.get("codigo_puesto",""),
                         callback=self._cargar_arr_combo)

    def _ver_arr(self):
        VerArrendatarios(self, self._sid)

    def _venta_puesto(self):
        VentaPuesto(self, self._sid, self._s,
                    self._usuario, callback=self._refresh)

    # ── Columna 2 — VEHÍCULOS ────────────────────────────────────────────────
    def _build_col2(self):
        p = self._col2
        label(p, "VEHÍCULOS ASIGNADOS",
              bg=BG, fg=ACCENT, font=FB).pack(pady=(6, 4))

        bar = tk.Frame(p, bg=BG); bar.pack(fill="x", padx=4, pady=4)
        btn(bar, "+ Agregar Vehículo",
            self._form_veh, bg=SUCCESS).pack(side="left", padx=(0,4))
        btn(bar, "📋 Historial Completo del Puesto",
            self._hist_veh_puesto, bg=PANEL).pack(side="left")

        self._veh_cont = tk.Frame(p, bg=BG)
        self._veh_cont.pack(fill="both", expand=True, padx=4)
        self._cargar_vehs()

    def _cargar_vehs(self):
        for w in self._veh_cont.winfo_children():
            w.destroy()
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT id,tipo,marca,modelo,placa,color,
                            estado,km,foto,fecha_asig,fecha_baja,motivo_baja
                     FROM vehiculos_historial WHERE socio_id=?
                     ORDER BY CASE estado
                         WHEN 'Actual' THEN 0
                         WHEN 'Operativo' THEN 1
                         WHEN 'En Mantenimiento' THEN 2
                         ELSE 3 END, fecha_asig DESC""", (self._sid,))
        rows = c.fetchall(); conn.close()

        if not rows:
            label(self._veh_cont, "No hay vehículos registrados.",
                  bg=BG, fg=SUBTEXT, font=FN).pack(pady=20)
            return

        for row in rows:
            vid, tipo, marca, modelo, placa, color, estado, km, \
                foto, f_asig, f_baja, motivo = row
            e_color = (SUCCESS if estado in ("Actual","Operativo")
                       else WARN   if estado == "En Mantenimiento"
                       else "#7f8c8d")
            card = tk.Frame(self._veh_cont, bg="white",
                            relief="flat", pady=6, padx=8)
            card.pack(fill="x", pady=4)

            foto_lbl = tk.Label(card, bg="white", width=8, height=4)
            foto_lbl.pack(side="left", padx=(0,8))
            ph = load_img(foto, (80, 70))
            if ph:
                self._refs.append(ph)
                foto_lbl.config(image=ph, width=80, height=70)
            else:
                foto_lbl.config(text="🚗", font=("Segoe UI",22), fg="#aaa")

            info = tk.Frame(card, bg="white")
            info.pack(side="left", fill="both", expand=True)
            tk.Label(info, text=f"{tipo}  {marca} {modelo}",
                     bg="white", fg="#1a1a2e", font=FB, anchor="w").pack(anchor="w")
            tk.Label(info, text=f"Placa: {placa}   Color: {color}",
                     bg="white", fg="#555", font=FN, anchor="w").pack(anchor="w")
            tk.Label(info, text=f"Estado: {estado}",
                     bg="white", fg=e_color, font=FB, anchor="w").pack(anchor="w")
            tk.Label(info, text=f"KM: {km}   F.Asig: {f_asig}",
                     bg="white", fg="#555", font=FS, anchor="w").pack(anchor="w")
            if f_baja:
                tk.Label(info, text=f"F.Baja: {f_baja}  Motivo: {motivo}",
                         bg="white", fg="#999", font=FS, anchor="w").pack(anchor="w")

            btn_f = tk.Frame(card, bg="white")
            btn_f.pack(side="right", anchor="n")
            btn(btn_f, "✏️", lambda v=vid: self._form_veh(v),
                bg=ACCENT, width=3, pady=2).pack(pady=2)
            if estado not in ("Histórico","Baja"):
                btn(btn_f, "🚫 Baja",
                    lambda v=vid: self._dar_baja(v),
                    bg=DANGER, width=7, pady=2).pack(pady=2)

    def _form_veh(self, veh_id=None):
        FormVehiculo(self, self._sid,
                     self._s.get("codigo_puesto",""),
                     veh_id, callback=self._cargar_vehs)

    def _dar_baja(self, veh_id):
        motivo = ask_string(self, "Dar de Baja", "Motivo de baja:")
        if motivo is None: return
        conn = get_conn(); c = conn.cursor()
        c.execute("""UPDATE vehiculos_historial
                     SET estado='Histórico', fecha_baja=?, motivo_baja=?
                     WHERE id=?""",
                  (datetime.now().strftime("%Y-%m-%d"), motivo, veh_id))
        conn.commit(); conn.close()
        self._cargar_vehs()

    def _hist_veh_puesto(self):
        codigo = self._s.get("codigo_puesto","")
        win = tk.Toplevel(self)
        win.title(f"Historial vehículos — Puesto {codigo}")
        win.configure(bg=BG)
        win.geometry("820x500")
        cols = ("ID","Socio","Tipo","Placa","Marca","Modelo",
                "Estado","F.Asig","F.Baja")
        tree = ttk.Treeview(win, columns=cols, show="headings", height=20)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor="center")
        sb = ttk.Scrollbar(win, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        sb.pack(side="left", fill="y", pady=10)
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT v.id, s.nombre||' '||s.apellido,
                            v.tipo, v.placa, v.marca, v.modelo,
                            v.estado, v.fecha_asig, v.fecha_baja
                     FROM vehiculos_historial v
                     LEFT JOIN socios s ON s.id=v.socio_id
                     WHERE v.puesto_codigo=?
                     ORDER BY v.fecha_asig DESC""", (codigo,))
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()

    # ── Columna 3 — DOCUMENTOS DE SANCIONES ─────────────────────────────────
    def _build_col3(self):
        p = self._col3
        label(p, "DOCUMENTOS DE SANCIONES",
              bg=BG, fg=ACCENT, font=FB).pack(pady=(6, 4))

        btn(p, "+ Agregar Documento / Sanción",
            self._form_san, bg=DANGER).pack(fill="x", padx=4, pady=4)

        self._san_cont = tk.Frame(p, bg=BG)
        self._san_cont.pack(fill="both", expand=True, padx=4)
        self._cargar_sans()

    def _cargar_sans(self):
        for w in self._san_cont.winfo_children():
            w.destroy()
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT id,tipo,fecha,descripcion,
                            sancion_aplicada,estado,documento
                     FROM sanciones WHERE socio_id=?
                     ORDER BY fecha DESC""", (self._sid,))
        rows = c.fetchall(); conn.close()

        if not rows:
            label(self._san_cont, "No hay sanciones registradas.",
                  bg=BG, fg=SUBTEXT, font=FN).pack(pady=20)
            return

        for row in rows:
            sid2, tipo, fecha, desc, sancion, estado, doc = row
            e_color = DANGER if estado == "Vigente" else "#7f8c8d"
            card = tk.Frame(self._san_cont, bg="#d0d8e4",
                            relief="flat", pady=6, padx=8)
            card.pack(fill="x", pady=3)
            top_r = tk.Frame(card, bg="#d0d8e4"); top_r.pack(fill="x")
            tk.Label(top_r, text=f"⚠️  {tipo}",
                     bg="#d0d8e4", fg="#1a1a2e", font=FB).pack(side="left")
            tk.Label(top_r, text=estado,
                     bg="#d0d8e4", fg=e_color, font=FB).pack(side="right")
            tk.Label(card, text=f"📅 {fecha}",
                     bg="#d0d8e4", fg="#333", font=FS, anchor="w").pack(anchor="w")
            if desc:
                tk.Label(card,
                         text=desc[:80]+("…" if len(desc)>80 else ""),
                         bg="#d0d8e4", fg="#444", font=FS,
                         wraplength=300, justify="left").pack(anchor="w")
            if sancion:
                tk.Label(card, text=f"Sanción: {sancion}",
                         bg="#d0d8e4", fg="#8b0000", font=FS).pack(anchor="w")
            btn_r = tk.Frame(card, bg="#d0d8e4"); btn_r.pack(fill="x", pady=(4,0))
            if doc and os.path.isfile(doc):
                btn(btn_r, "📄 Ver Documento",
                    lambda d=doc: os.startfile(d),
                    bg=ACCENT, pady=2).pack(side="left", padx=(0,4))
            btn(btn_r, "✏️ Editar",
                lambda s2=sid2: self._form_san(s2),
                bg="#555", pady=2).pack(side="left")
            btn(btn_r, "🗑️",
                lambda s2=sid2: self._del_san(s2),
                bg=DANGER, width=3, pady=2).pack(side="right")

    def _form_san(self, san_id=None):
        FormSancion(self, self._sid, san_id, callback=self._cargar_sans)

    def _del_san(self, san_id):
        if messagebox.askyesno("Confirmar","¿Eliminar esta sanción?"):
            conn = get_conn(); c = conn.cursor()
            c.execute("DELETE FROM sanciones WHERE id=?", (san_id,))
            conn.commit(); conn.close()
            self._cargar_sans()

    # ── Refresh ──────────────────────────────────────────────────────────────
    def _refresh(self):
        self._cargar_socio()
        for w in self.winfo_children():
            w.destroy()
        self._refs.clear()
        self._build()


# ════════════════════════════════════════════════════════════════════════════
# FORMULARIO VEHÍCULO
# ════════════════════════════════════════════════════════════════════════════
class FormVehiculo(tk.Toplevel):
    def __init__(self, parent, socio_id, puesto, veh_id=None, callback=None):
        super().__init__(parent)
        self.title("Vehículo")
        self.configure(bg=BG)
        self.grab_set()
        self.resizable(False, False)
        self._sid      = socio_id
        self._puesto   = puesto
        self._vid      = veh_id
        self._callback = callback
        self._refs     = []
        self._foto_var = tk.StringVar()
        self._datos    = {}
        if veh_id:
            conn = get_conn(); c = conn.cursor()
            c.execute("SELECT * FROM vehiculos_historial WHERE id=?", (veh_id,))
            row = c.fetchone(); conn.close()
            if row:
                keys = ["id","socio_id","puesto_codigo","tipo","marca","modelo",
                        "placa","color","estado","km","foto","fecha_asig",
                        "fecha_baja","motivo_baja"]
                self._datos = dict(zip(keys, row))
        self._build()

    def _build(self):
        d = self._datos
        self._foto_var.set(d.get("foto",""))
        campos = [
            ("Tipo",         "tipo",      ["Automóvil","Camioneta","Moto","Camión","Otro"]),
            ("Marca",        "marca",     None),
            ("Modelo",       "modelo",    None),
            ("Placa",        "placa",     None),
            ("Color",        "color",     None),
            ("KM",           "km",        None),
            ("Fecha Asig.",  "fecha_asig",None),
        ]
        self._entries = {}
        for i,(lbl,key,opts) in enumerate(campos):
            label(self, lbl, bg=BG).grid(row=i, column=0, padx=12, pady=4, sticky="w")
            if opts:
                var = tk.StringVar(value=d.get(key,""))
                w   = ttk.Combobox(self, textvariable=var,
                                   values=opts, width=26, state="readonly")
                w.grid(row=i, column=1, padx=12, pady=4)
                self._entries[key] = var
            else:
                e = entry(self, width=28)
                e.insert(0, d.get(key,
                    datetime.now().strftime("%Y-%m-%d") if key=="fecha_asig" else ""))
                e.grid(row=i, column=1, padx=12, pady=4, ipady=3)
                self._entries[key] = e

        label(self, "Estado", bg=BG).grid(
            row=len(campos), column=0, padx=12, pady=4, sticky="w")
        self._estado_var = tk.StringVar(value=d.get("estado","Actual"))
        ttk.Combobox(self, textvariable=self._estado_var,
                     values=["Actual","Operativo","En Mantenimiento",
                             "Histórico","Baja"],
                     state="readonly", width=26
                     ).grid(row=len(campos), column=1, padx=12, pady=4)

        foto_lbl = tk.Label(self, bg=PANEL, width=14, height=7,
                            text="Sin foto", fg=SUBTEXT)
        foto_lbl.grid(row=0, column=2, rowspan=4, padx=14, pady=8)
        ph = load_img(self._foto_var.get(), (120,90))
        if ph:
            self._refs.append(ph)
            foto_lbl.config(image=ph, text="", width=120, height=90)

        def sel_foto():
            f = filedialog.askopenfilename(
                filetypes=[("Imágenes","*.jpg *.jpeg *.png")])
            if f:
                self._foto_var.set(f)
                p2 = load_img(f, (120,90))
                if p2:
                    self._refs.append(p2)
                    foto_lbl.config(image=p2, text="")

        btn(self, "📷 Foto", sel_foto, bg=ACCENT
            ).grid(row=4, column=2, padx=14)
        btn(self, "💾 Guardar", self._guardar,
            bg=SUCCESS, width=22, pady=6
            ).grid(row=len(campos)+1, column=0, columnspan=2, pady=12)

    def _get(self, key):
        v = self._entries.get(key)
        return v.get() if v is not None else ""

    def _guardar(self):
        foto_dest = (copiar_archivo(self._foto_var.get(), DIR_VEH)
                     if self._foto_var.get() else self._datos.get("foto",""))
        vals = (self._sid, self._puesto,
                self._get("tipo"), self._get("marca"), self._get("modelo"),
                self._get("placa"), self._get("color"),
                self._estado_var.get(), self._get("km"),
                foto_dest, self._get("fecha_asig"))
        conn = get_conn(); c = conn.cursor()
        if self._vid:
            c.execute("""UPDATE vehiculos_historial
                         SET socio_id=?,puesto_codigo=?,tipo=?,marca=?,modelo=?,
                             placa=?,color=?,estado=?,km=?,foto=?,fecha_asig=?
                         WHERE id=?""", vals + (self._vid,))
        else:
            c.execute("""INSERT INTO vehiculos_historial
                         (socio_id,puesto_codigo,tipo,marca,modelo,
                          placa,color,estado,km,foto,fecha_asig)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?)""", vals)
        conn.commit(); conn.close()
        messagebox.showinfo("OK","Vehículo guardado.")
        self.destroy()
        if self._callback: self._callback()


# ════════════════════════════════════════════════════════════════════════════
# FORMULARIO SANCIÓN
# ════════════════════════════════════════════════════════════════════════════
class FormSancion(tk.Toplevel):
    def __init__(self, parent, socio_id, san_id=None, callback=None):
        super().__init__(parent)
        self.title("Sanción / Documento")
        self.configure(bg=BG)
        self.grab_set()
        self.resizable(False, False)
        self._sid      = socio_id
        self._san_id   = san_id
        self._callback = callback
        self._doc_var  = tk.StringVar()
        self._datos    = {}
        if san_id:
            conn = get_conn(); c = conn.cursor()
            c.execute("SELECT * FROM sanciones WHERE id=?", (san_id,))
            row = c.fetchone(); conn.close()
            if row:
                keys = ["id","socio_id","tipo","fecha","descripcion",
                        "sancion_aplicada","estado","documento"]
                self._datos = dict(zip(keys, row))
        self._build()

    def _build(self):
        d = self._datos
        self._doc_var.set(d.get("documento",""))

        label(self,"Tipo",bg=BG).grid(row=0,column=0,padx=12,pady=5,sticky="w")
        self._tipo_var = tk.StringVar(value=d.get("tipo",""))
        ttk.Combobox(self, textvariable=self._tipo_var,
                     values=["Económica","Disciplinaria","Suspensión",
                             "Advertencia","Amonestación","Otro"],
                     width=28
                     ).grid(row=0,column=1,padx=12,pady=5)

        label(self,"Fecha",bg=BG).grid(row=1,column=0,padx=12,pady=5,sticky="w")
        self._fecha_e = entry(self, width=30)
        self._fecha_e.insert(0, d.get("fecha",
            datetime.now().strftime("%Y-%m-%d")))
        self._fecha_e.grid(row=1,column=1,padx=12,pady=5,ipady=3)

        label(self,"Descripción",bg=BG).grid(
            row=2,column=0,padx=12,pady=5,sticky="nw")
        self._desc_t = tk.Text(self,width=30,height=4,
                               bg=ENTRY_BG,fg=TEXT,
                               insertbackground="white",relief="flat")
        self._desc_t.insert("1.0",d.get("descripcion",""))
        self._desc_t.grid(row=2,column=1,padx=12,pady=5)

        label(self,"Sanción Aplicada",bg=BG).grid(
            row=3,column=0,padx=12,pady=5,sticky="nw")
        self._san_t = tk.Text(self,width=30,height=3,
                              bg=ENTRY_BG,fg=TEXT,
                              insertbackground="white",relief="flat")
        self._san_t.insert("1.0",d.get("sancion_aplicada",""))
        self._san_t.grid(row=3,column=1,padx=12,pady=5)

        label(self,"Estado",bg=BG).grid(
            row=4,column=0,padx=12,pady=5,sticky="w")
        self._estado_var = tk.StringVar(value=d.get("estado","Vigente"))
        ttk.Combobox(self, textvariable=self._estado_var,
                     values=["Vigente","Cumplida","Apelada","Anulada"],
                     state="readonly", width=28
                     ).grid(row=4,column=1,padx=12,pady=5)

        label(self,"Documento",bg=BG).grid(
            row=5,column=0,padx=12,pady=5,sticky="w")
        doc_r = tk.Frame(self,bg=BG)
        doc_r.grid(row=5,column=1,padx=12,pady=5,sticky="w")
        tk.Entry(doc_r, textvariable=self._doc_var, width=22,
                 bg=ENTRY_BG, fg=TEXT, state="readonly",
                 relief="flat").pack(side="left")
        btn(doc_r,"📎",
            lambda: self._doc_var.set(
                filedialog.askopenfilename(
                    filetypes=[("Archivos","*.pdf *.jpg *.png *.docx")])),
            bg=ACCENT, width=3).pack(side="left", padx=4)

        btn(self,"💾 Guardar",self._guardar,
            bg=SUCCESS,width=22,pady=6
            ).grid(row=6,column=0,columnspan=2,pady=12)

    def _guardar(self):
        doc_dest = (copiar_archivo(self._doc_var.get(), DIR_DOCS)
                    if self._doc_var.get() else self._datos.get("documento",""))
        vals = (self._sid, self._tipo_var.get(),
                self._fecha_e.get(),
                self._desc_t.get("1.0","end-1c"),
                self._san_t.get("1.0","end-1c"),
                self._estado_var.get(), doc_dest)
        conn = get_conn(); c = conn.cursor()
        if self._san_id:
            c.execute("""UPDATE sanciones
                         SET socio_id=?,tipo=?,fecha=?,descripcion=?,
                             sancion_aplicada=?,estado=?,documento=?
                         WHERE id=?""", vals+(self._san_id,))
        else:
            c.execute("""INSERT INTO sanciones
                         (socio_id,tipo,fecha,descripcion,
                          sancion_aplicada,estado,documento)
                         VALUES (?,?,?,?,?,?,?)""", vals)
        conn.commit(); conn.close()
        messagebox.showinfo("OK","Sanción guardada.")
        self.destroy()
        if self._callback: self._callback()


# ════════════════════════════════════════════════════════════════════════════
# FORMULARIO ARRENDATARIO
# ════════════════════════════════════════════════════════════════════════════
class FormArrendatario(tk.Toplevel):
    def __init__(self, parent, socio_id, puesto, arr_id=None, callback=None):
        super().__init__(parent)
        self.title("Arrendatario")
        self.configure(bg=BG)
        self.grab_set()
        self.resizable(False, False)
        self._sid      = socio_id
        self._puesto   = puesto
        self._arr_id   = arr_id
        self._callback = callback
        self._datos    = {}
        if arr_id:
            conn = get_conn(); c = conn.cursor()
            c.execute("SELECT * FROM arrendatarios WHERE id=?", (arr_id,))
            row = c.fetchone(); conn.close()
            if row:
                keys = ["id","socio_id","puesto_codigo","nombre","cedula",
                        "telefono","fecha_inicio","fecha_fin","estado"]
                self._datos = dict(zip(keys, row))
        self._build()

    def _build(self):
        d = self._datos
        campos = [
            ("Nombre",       "nombre"),
            ("Cédula",       "cedula"),
            ("Teléfono",     "telefono"),
            ("Fecha Inicio", "fecha_inicio"),
            ("Fecha Fin",    "fecha_fin"),
        ]
        self._entries = {}
        for i,(lbl,key) in enumerate(campos):
            label(self,lbl,bg=BG).grid(row=i,column=0,padx=12,pady=5,sticky="w")
            e = entry(self, width=30)
            e.insert(0, d.get(key,
                datetime.now().strftime("%Y-%m-%d") if "fecha" in key else ""))
            e.grid(row=i,column=1,padx=12,pady=5,ipady=3)
            self._entries[key] = e

        label(self,"Estado",bg=BG).grid(
            row=len(campos),column=0,padx=12,pady=5,sticky="w")
        self._estado_var = tk.StringVar(value=d.get("estado","ACTIVO"))
        ttk.Combobox(self, textvariable=self._estado_var,
                     values=["ACTIVO","INACTIVO","TERMINADO"],
                     state="readonly", width=28
                     ).grid(row=len(campos),column=1,padx=12,pady=5)

        btn(self,"💾 Guardar",self._guardar,
            bg=SUCCESS,width=22,pady=6
            ).grid(row=len(campos)+1,column=0,columnspan=2,pady=12)

    def _guardar(self):
        vals = (self._sid, self._puesto,
                self._entries["nombre"].get(),
                self._entries["cedula"].get(),
                self._entries["telefono"].get(),
                self._entries["fecha_inicio"].get(),
                self._entries["fecha_fin"].get(),
                self._estado_var.get())
        conn = get_conn(); c = conn.cursor()
        if self._arr_id:
            c.execute("""UPDATE arrendatarios
                         SET socio_id=?,puesto_codigo=?,nombre=?,cedula=?,
                             telefono=?,fecha_inicio=?,fecha_fin=?,estado=?
                         WHERE id=?""", vals+(self._arr_id,))
        else:
            c.execute("""INSERT INTO arrendatarios
                         (socio_id,puesto_codigo,nombre,cedula,
                          telefono,fecha_inicio,fecha_fin,estado)
                         VALUES (?,?,?,?,?,?,?,?)""", vals)
        conn.commit(); conn.close()
        messagebox.showinfo("OK","Arrendatario guardado.")
        self.destroy()
        if self._callback: self._callback()


# ════════════════════════════════════════════════════════════════════════════
# VER ARRENDATARIOS
# ════════════════════════════════════════════════════════════════════════════
class VerArrendatarios(tk.Toplevel):
    def __init__(self, parent, socio_id):
        super().__init__(parent)
        self.title("Arrendatarios del Puesto")
        self.configure(bg=BG)
        self.geometry("700x400")
        cols = ("ID","Nombre","Cédula","Teléfono","F.Inicio","F.Fin","Estado")
        tree = ttk.Treeview(self, columns=cols, show="headings", height=16)
        for col in cols:
            tree.heading(col, text=col)
            tree.column(col, width=90, anchor="center")
        sb = ttk.Scrollbar(self, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        sb.pack(side="left", fill="y", pady=10)
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT id,nombre,cedula,telefono,
                            fecha_inicio,fecha_fin,estado
                     FROM arrendatarios WHERE socio_id=?
                     ORDER BY fecha_inicio DESC""", (socio_id,))
        for row in c.fetchall():
            tree.insert("", "end", values=row)
        conn.close()


# ════════════════════════════════════════════════════════════════════════════
# VENTA DE PUESTO
# ════════════════════════════════════════════════════════════════════════════
class VentaPuesto(tk.Toplevel):
    def __init__(self, parent, ant_id, datos_ant, usuario, callback=None):
        super().__init__(parent)
        self.title("Venta de Puesto")
        self.configure(bg=BG)
        self.grab_set()
        self.resizable(False, False)
        self._ant_id   = ant_id
        self._ant      = datos_ant
        self._usuario  = usuario
        self._callback = callback
        self._doc_var  = tk.StringVar()
        self._build()

    def _build(self):
        label(self, "VENTA DE PUESTO",
              bg=BG, fg=DANGER, font=FT).grid(
            row=0,column=0,columnspan=2,pady=10)
        label(self,
              f"Puesto: {self._ant.get('codigo_puesto','')}",
              bg=BG, fg=WARN, font=FB).grid(
            row=1,column=0,columnspan=2,pady=2)
        label(self,
              f"Propietario actual: "
              f"{self._ant.get('nombre','')} {self._ant.get('apellido','')}",
              bg=BG, fg=TEXT, font=FN).grid(
            row=2,column=0,columnspan=2,pady=2)

        tk.Frame(self,bg=DANGER,height=1).grid(
            row=3,column=0,columnspan=2,sticky="ew",padx=12,pady=8)

        label(self,"— DATOS DEL NUEVO PROPIETARIO —",
              bg=BG,fg=TEXT,font=FB).grid(
            row=4,column=0,columnspan=2,pady=4)

        campos = [
            ("Nombre",         "nombre"),
            ("Apellido",       "apellido"),
            ("Cédula",         "cedula"),
            ("Rango",          "rango"),
            ("Unidad",         "unidad"),
            ("WhatsApp",       "whatsapp"),
            ("Valor de Venta", "valor"),
            ("Motivo / Notas", "motivo"),
        ]
        self._entries = {}
        for i,(lbl,key) in enumerate(campos,5):
            label(self,lbl,bg=BG).grid(row=i,column=0,padx=14,pady=4,sticky="w")
            e = entry(self,width=32)
            e.grid(row=i,column=1,padx=14,pady=4,ipady=3)
            self._entries[key] = e

        row_doc = len(campos)+5
        label(self,"Documento",bg=BG).grid(
            row=row_doc,column=0,padx=14,pady=4,sticky="w")
        doc_r = tk.Frame(self,bg=BG)
        doc_r.grid(row=row_doc,column=1,padx=14,pady=4,sticky="w")
        tk.Entry(doc_r, textvariable=self._doc_var, width=24,
                 bg=ENTRY_BG, fg=TEXT, state="readonly",
                 relief="flat").pack(side="left")
        btn(doc_r,"📎",
            lambda: self._doc_var.set(
                filedialog.askopenfilename(
                    filetypes=[("Archivos","*.pdf *.jpg *.png *.docx")])),
            bg=ACCENT, width=3).pack(side="left", padx=4)

        btn(self,"✅  CONFIRMAR VENTA",
            self._confirmar, bg=DANGER,
            width=28, pady=8, font=FB
            ).grid(row=row_doc+1,column=0,columnspan=2,pady=14)

    def _confirmar(self):
        nombre   = self._entries["nombre"].get().strip()
        apellido = self._entries["apellido"].get().strip()
        cedula   = self._entries["cedula"].get().strip()
        if not (nombre and apellido and cedula):
            messagebox.showerror("Error",
                "Nombre, apellido y cédula son obligatorios.")
            return
        if not messagebox.askyesno("Confirmar",
                f"¿Registrar venta del puesto "
                f"{self._ant.get('codigo_puesto','')} "
                f"a {nombre} {apellido}?"):
            return

        doc_dest = (copiar_archivo(self._doc_var.get(), DIR_VENTAS)
                    if self._doc_var.get() else "")
        codigo = self._ant.get("codigo_puesto","")
        fecha  = datetime.now().strftime("%Y-%m-%d")

        conn = get_conn(); c = conn.cursor()
        try:
            c.execute("""INSERT INTO socios
                         (nombre,apellido,cedula,codigo_puesto,rango,
                          estado,unidad,fecha_ingreso,whatsapp)
                         VALUES (?,?,?,?,?,?,?,?,?)""", (
                nombre, apellido, cedula, codigo,
                self._entries["rango"].get(),
                "ACTIVO",
                self._entries["unidad"].get(),
                fecha,
                self._entries["whatsapp"].get(),
            ))
            nuevo_id = c.lastrowid
            c.execute("UPDATE socios SET estado='VENDIDO' WHERE id=?",
                      (self._ant_id,))
            c.execute("""UPDATE vehiculos_historial SET socio_id=?
                         WHERE socio_id=? AND estado='Actual'""",
                      (nuevo_id, self._ant_id))
            c.execute("""UPDATE arrendatarios SET socio_id=?
                         WHERE socio_id=? AND estado='ACTIVO'""",
                      (nuevo_id, self._ant_id))
            c.execute("""INSERT INTO historial_puestos
                         (puesto_codigo,socio_anterior_id,socio_nuevo_id,
                          socio_anterior_nombre,socio_nuevo_nombre,
                          fecha_venta,valor,motivo,documento)
                         VALUES (?,?,?,?,?,?,?,?,?)""", (
                codigo,
                self._ant_id, nuevo_id,
                f"{self._ant.get('nombre','')} {self._ant.get('apellido','')}",
                f"{nombre} {apellido}",
                fecha,
                self._entries["valor"].get(),
                self._entries["motivo"].get(),
                doc_dest,
            ))
            conn.commit()
            messagebox.showinfo("Venta Registrada",
                f"Puesto {codigo} transferido a {nombre} {apellido}.\n"
                "Anterior marcado como VENDIDO.\n"
                "Vehículos actuales y arrendatarios activos transferidos.")
            self.destroy()
            if self._callback: self._callback()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error",
                "La cédula del nuevo propietario ya está registrada.")
        finally:
            conn.close()


# ════════════════════════════════════════════════════════════════════════════
# FORMULARIO USUARIO
# ════════════════════════════════════════════════════════════════════════════
class FormUsuario(tk.Toplevel):
    def __init__(self, parent, uid=None, callback=None):
        super().__init__(parent)
        self.title("Usuario")
        self.configure(bg=BG)
        self.grab_set()
        self.resizable(False, False)
        self._uid      = uid
        self._callback = callback
        self._datos    = {}
        if uid:
            conn = get_conn(); c = conn.cursor()
            c.execute("SELECT id,username,rol,nombre FROM usuarios WHERE id=?",
                      (uid,))
            row = c.fetchone(); conn.close()
            if row:
                self._datos = dict(zip(["id","username","rol","nombre"], row))
        self._build()

    def _build(self):
        d = self._datos
        campos = [("Username","username"),("Nombre completo","nombre")]
        self._entries = {}
        for i,(lbl,key) in enumerate(campos):
            label(self,lbl,bg=BG).grid(row=i,column=0,padx=14,pady=6,sticky="w")
            e = entry(self,width=28)
            e.insert(0,d.get(key,""))
            e.grid(row=i,column=1,padx=14,pady=6,ipady=3)
            self._entries[key] = e

        label(self,"Rol",bg=BG).grid(row=2,column=0,padx=14,pady=6,sticky="w")
        self._rol_var = tk.StringVar(value=d.get("rol","Operador"))
        ttk.Combobox(self, textvariable=self._rol_var,
                     values=["Administrador","Operador"],
                     state="readonly", width=26
                     ).grid(row=2,column=1,padx=14,pady=6)

        label(self,"Nueva Contraseña",bg=BG).grid(
            row=3,column=0,padx=14,pady=6,sticky="w")
        self._pwd_e = entry(self,width=28,show="●")
        self._pwd_e.grid(row=3,column=1,padx=14,pady=6,ipady=3)

        if self._uid:
            label(self,"(dejar vacío = no cambiar)",
                  bg=BG, fg=SUBTEXT, font=FS
                  ).grid(row=4,column=1,padx=14,sticky="w")

        btn(self,"💾 Guardar",self._guardar,
            bg=SUCCESS,width=22,pady=6
            ).grid(row=5,column=0,columnspan=2,pady=14)

    def _guardar(self):
        username = self._entries["username"].get().strip()
        nombre   = self._entries["nombre"].get().strip()
        rol      = self._rol_var.get()
        pwd      = self._pwd_e.get().strip()

        if not username or not nombre:
            messagebox.showerror("Error","Username y nombre son obligatorios.")
            return
        if not self._uid and not pwd:
            messagebox.showerror("Error","Ingresa una contraseña para el nuevo usuario.")
            return

        conn = get_conn(); c = conn.cursor()
        try:
            if self._uid:
                if pwd:
                    c.execute("""UPDATE usuarios SET username=?,rol=?,
                                 nombre=?,password=? WHERE id=?""",
                              (username,rol,nombre,hash_pwd(pwd),self._uid))
                else:
                    c.execute("UPDATE usuarios SET username=?,rol=?,nombre=? WHERE id=?",
                              (username,rol,nombre,self._uid))
            else:
                c.execute("""INSERT INTO usuarios(username,password,rol,nombre)
                             VALUES (?,?,?,?)""",
                          (username,hash_pwd(pwd),rol,nombre))
            conn.commit()
            messagebox.showinfo("OK","Usuario guardado.")
            self.destroy()
            if self._callback: self._callback()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error","Ese username ya existe.")
        finally:
            conn.close()


# ════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════
def _run_login():
    login = LoginWindow()
    login.mainloop()
    if login.usuario_logueado:
        app = MainApp(login.usuario_logueado)
        app.mainloop()


if __name__ == "__main__":
    _run_login()
