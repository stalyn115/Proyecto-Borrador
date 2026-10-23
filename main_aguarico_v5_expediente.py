"""
SISTEMA AGRUPACION AGUARICO - EXPEDIENTE PERSONAL v5
=====================================================
Tkinter + SQLite3  |  Python 3.8+
Pillow opcional (pip install pillow)
"""

import os
import sqlite3
import shutil
import webbrowser
import urllib.parse
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox

# ── Pillow opcional ──────────────────────────────────────────────────────────
try:
    from PIL import Image, ImageTk
    PIL_OK = True
except ImportError:
    PIL_OK = False

# ── Constantes ───────────────────────────────────────────────────────────────
DB          = "aguarico_v5.db"
DIR_FOTOS   = "fotos"
DIR_VEH     = "vehiculos_fotos"
DIR_DOCS    = "documentos_sanciones"
DIR_VENTAS  = "documentos_ventas"

for d in (DIR_FOTOS, DIR_VEH, DIR_DOCS, DIR_VENTAS):
    os.makedirs(d, exist_ok=True)

COLOR_BG      = "#0f2746"
COLOR_PANEL   = "#162d50"
COLOR_ACCENT  = "#1a73e8"
COLOR_DANGER  = "#c0392b"
COLOR_SUCCESS = "#27ae60"
COLOR_WARN    = "#f39c12"
COLOR_TEXT    = "#ffffff"
COLOR_SUBTEXT = "#b0bec5"
COLOR_CARD    = "#1e3a5f"
COLOR_ENTRY   = "#1c3358"

FONT_TITLE  = ("Segoe UI", 14, "bold")
FONT_BOLD   = ("Segoe UI", 10, "bold")
FONT_NORMAL = ("Segoe UI", 9)
FONT_SMALL  = ("Segoe UI", 8)


# ════════════════════════════════════════════════════════════════════════════
# BASE DE DATOS
# ════════════════════════════════════════════════════════════════════════════
def get_conn():
    return sqlite3.connect(DB)


def init_db():
    conn = get_conn()
    c = conn.cursor()

    c.execute("""
        CREATE TABLE IF NOT EXISTS socios (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre          TEXT,
            apellido        TEXT,
            cedula          TEXT UNIQUE,
            codigo_puesto   TEXT,
            rango           TEXT,
            estado          TEXT DEFAULT 'ACTIVO',
            unidad          TEXT,
            fecha_ingreso   TEXT,
            foto            TEXT,
            whatsapp        TEXT,
            observacion     TEXT
        )""")

    c.execute("""
        CREATE TABLE IF NOT EXISTS vehiculos_historial (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            socio_id        INTEGER,
            puesto_codigo   TEXT,
            tipo            TEXT,
            marca           TEXT,
            modelo          TEXT,
            placa           TEXT,
            color           TEXT,
            estado          TEXT DEFAULT 'Actual',
            km              TEXT,
            foto            TEXT,
            fecha_asig      TEXT,
            fecha_baja      TEXT,
            motivo_baja     TEXT
        )""")

    c.execute("""
        CREATE TABLE IF NOT EXISTS sanciones (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            socio_id        INTEGER,
            tipo            TEXT,
            fecha           TEXT,
            descripcion     TEXT,
            sancion_aplicada TEXT,
            estado          TEXT DEFAULT 'Vigente',
            documento       TEXT
        )""")

    c.execute("""
        CREATE TABLE IF NOT EXISTS arrendatarios (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,
            socio_id        INTEGER,
            puesto_codigo   TEXT,
            nombre          TEXT,
            cedula          TEXT,
            telefono        TEXT,
            fecha_inicio    TEXT,
            fecha_fin       TEXT,
            estado          TEXT DEFAULT 'ACTIVO'
        )""")

    c.execute("""
        CREATE TABLE IF NOT EXISTS historial_puestos (
            id                      INTEGER PRIMARY KEY AUTOINCREMENT,
            puesto_codigo           TEXT,
            socio_anterior_id       INTEGER,
            socio_nuevo_id          INTEGER,
            socio_anterior_nombre   TEXT,
            socio_nuevo_nombre      TEXT,
            fecha_venta             TEXT,
            valor                   TEXT,
            motivo                  TEXT,
            documento               TEXT
        )""")

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


def load_image(path, size):
    """Devuelve ImageTk.PhotoImage o None."""
    if not PIL_OK or not path or not os.path.isfile(path):
        return None
    try:
        img = Image.open(path)
        img.thumbnail(size, Image.LANCZOS)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None


def whatsapp_open(numero, mensaje=""):
    tel = str(numero).strip().replace(" ", "")
    if not tel.startswith("+"):
        tel = "+593" + tel.lstrip("0")
    url = ("https://wa.me/" + tel.lstrip("+") +
           ("?text=" + urllib.parse.quote(mensaje) if mensaje else ""))
    webbrowser.open(url)


def styled_btn(parent, text, command, bg=COLOR_ACCENT, fg=COLOR_TEXT,
               width=None, font=FONT_NORMAL, pady=4):
    kw = dict(text=text, command=command, bg=bg, fg=fg,
              font=font, relief="flat", cursor="hand2",
              activebackground=bg, activeforeground=fg, pady=pady)
    if width:
        kw["width"] = width
    return tk.Button(parent, **kw)


def lf(parent, text, fg=COLOR_TEXT, bg=COLOR_PANEL):
    """LabelFrame con estilo oscuro."""
    return tk.LabelFrame(parent, text=text, fg=fg, bg=bg,
                         font=FONT_BOLD, bd=1, relief="groove")


# ════════════════════════════════════════════════════════════════════════════
# VENTANA PRINCIPAL
# ════════════════════════════════════════════════════════════════════════════
class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SISTEMA AGRUPACION AGUARICO")
        self.geometry("1280x720")
        self.configure(bg=COLOR_BG)
        self._refs = []
        self._build()

    # ── Header ──────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=COLOR_BG, pady=8)
        hdr.pack(fill="x")
        tk.Label(hdr, text="SISTEMA AGRUPACION AGUARICO",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=("Segoe UI", 16, "bold")
                 ).pack(side="left", padx=20)
        tk.Label(hdr, text="Adm. Tnte. J. Paredes",
                 bg=COLOR_BG, fg=COLOR_SUBTEXT, font=FONT_NORMAL
                 ).pack(side="right", padx=20)

        # Tabs
        self.nb = ttk.Notebook(self)
        self.nb.pack(fill="both", expand=True, padx=0, pady=0)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("TNotebook", background=COLOR_BG, borderwidth=0)
        style.configure("TNotebook.Tab", background=COLOR_PANEL,
                        foreground=COLOR_TEXT, font=FONT_BOLD, padding=[14, 6])
        style.map("TNotebook.Tab",
                  background=[("selected", COLOR_ACCENT)],
                  foreground=[("selected", COLOR_TEXT)])
        style.configure("Treeview", background=COLOR_PANEL,
                        fieldbackground=COLOR_PANEL, foreground=COLOR_TEXT,
                        rowheight=26, font=FONT_NORMAL)
        style.configure("Treeview.Heading", background=COLOR_BG,
                        foreground=COLOR_TEXT, font=FONT_BOLD)
        style.map("Treeview", background=[("selected", COLOR_ACCENT)])

        self._tab_panel()
        self._tab_expedientes()
        self._tab_vehiculos_global()
        self._tab_sanciones_global()
        self._tab_reportes()
        self._tab_bitacora()

    # ── Tab Panel ────────────────────────────────────────────────────────────
    def _tab_panel(self):
        f = tk.Frame(self.nb, bg=COLOR_BG)
        self.nb.add(f, text="  Panel  ")

        tk.Label(f, text="PANEL PRINCIPAL", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_TITLE).pack(pady=20)

        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM socios WHERE estado='ACTIVO'")
        act = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM socios WHERE estado='VENDIDO'")
        vnd = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM vehiculos_historial WHERE estado='Actual'")
        veh = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM sanciones WHERE estado='Vigente'")
        san = c.fetchone()[0]
        conn.close()

        cards_f = tk.Frame(f, bg=COLOR_BG)
        cards_f.pack()
        for titulo, valor, color in [
            ("Socios Activos",     act, COLOR_SUCCESS),
            ("Puestos Vendidos",   vnd, COLOR_DANGER),
            ("Vehículos en Uso",   veh, COLOR_ACCENT),
            ("Sanciones Vigentes", san, COLOR_WARN),
        ]:
            card = tk.Frame(cards_f, bg=color, padx=30, pady=20)
            card.pack(side="left", padx=15, pady=10)
            tk.Label(card, text=str(valor), bg=color, fg="white",
                     font=("Segoe UI", 28, "bold")).pack()
            tk.Label(card, text=titulo, bg=color, fg="white",
                     font=FONT_NORMAL).pack()

    # ── Tab Expedientes ───────────────────────────────────────────────────────
    def _tab_expedientes(self):
        f = tk.Frame(self.nb, bg=COLOR_BG)
        self.nb.add(f, text="  Expedientes  ")

        # Barra superior
        bar = tk.Frame(f, bg=COLOR_BG, pady=6)
        bar.pack(fill="x", padx=10)
        tk.Label(bar, text="Buscar:", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).pack(side="left")
        self._buscar_var = tk.StringVar()
        tk.Entry(bar, textvariable=self._buscar_var, width=35,
                 bg=COLOR_ENTRY, fg=COLOR_TEXT, insertbackground="white",
                 font=FONT_NORMAL, relief="flat"
                 ).pack(side="left", padx=6, ipady=4)
        styled_btn(bar, "🔍 Buscar",
                   lambda: self._cargar_socios(self._buscar_var.get())
                   ).pack(side="left")
        styled_btn(bar, "➕ Nuevo Socio", self._form_socio,
                   bg=COLOR_SUCCESS).pack(side="right", padx=4)

        # Treeview
        cols = ("ID","Código","Nombre","Apellido","Cédula","Rango","Unidad","Estado")
        self.tree_socios = ttk.Treeview(f, columns=cols, show="headings", height=24)
        widths = [40, 100, 140, 140, 110, 110, 120, 80]
        for col, w in zip(cols, widths):
            self.tree_socios.heading(col, text=col)
            self.tree_socios.column(col, width=w, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=self.tree_socios.yview)
        self.tree_socios.configure(yscrollcommand=sb.set)
        self.tree_socios.pack(side="left", fill="both", expand=True, padx=(10,0), pady=5)
        sb.pack(side="left", fill="y", pady=5, padx=(0,10))

        # Menú contextual
        ctx = tk.Menu(self, tearoff=0)
        ctx.add_command(label="📂 Abrir Expediente", command=self._abrir_expediente)
        ctx.add_command(label="✏️ Editar datos", command=self._form_socio_editar)
        ctx.add_command(label="🗑️ Eliminar", command=self._eliminar_socio)
        self.tree_socios.bind("<Button-3>",
                              lambda e: ctx.post(e.x_root, e.y_root))
        self.tree_socios.bind("<Double-1>",
                              lambda e: self._abrir_expediente())

        self._cargar_socios()

    def _cargar_socios(self, filtro=""):
        for r in self.tree_socios.get_children():
            self.tree_socios.delete(r)
        conn = get_conn(); c = conn.cursor()
        sql = ("SELECT id,codigo_puesto,nombre,apellido,cedula,rango,unidad,estado "
               "FROM socios")
        if filtro:
            sql += (" WHERE nombre LIKE ? OR apellido LIKE ? "
                    "OR cedula LIKE ? OR codigo_puesto LIKE ?")
            c.execute(sql, (f"%{filtro}%",)*4)
        else:
            c.execute(sql + " ORDER BY apellido")
        for row in c.fetchall():
            self.tree_socios.insert("", "end", values=row)
        conn.close()

    def _abrir_expediente(self):
        sel = self.tree_socios.selection()
        if not sel:
            return
        sid = self.tree_socios.item(sel[0])["values"][0]
        ExpedienteWindow(self, sid)

    def _form_socio_editar(self):
        sel = self.tree_socios.selection()
        if not sel:
            return
        sid = self.tree_socios.item(sel[0])["values"][0]
        self._form_socio(sid)

    def _eliminar_socio(self):
        sel = self.tree_socios.selection()
        if not sel:
            return
        sid = self.tree_socios.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar", "¿Eliminar este socio?"):
            conn = get_conn(); c = conn.cursor()
            c.execute("DELETE FROM socios WHERE id=?", (sid,))
            conn.commit(); conn.close()
            self._cargar_socios()

    def _form_socio(self, socio_id=None):
        FormSocio(self, socio_id, callback=self._cargar_socios)

    # ── Tab Vehículos global ───────────────────────────────────────────────────
    def _tab_vehiculos_global(self):
        f = tk.Frame(self.nb, bg=COLOR_BG)
        self.nb.add(f, text="  Vehículos  ")

        bar = tk.Frame(f, bg=COLOR_BG, pady=6)
        bar.pack(fill="x", padx=10)
        tk.Label(bar, text="Todos los vehículos registrados",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_BOLD).pack(side="left")
        styled_btn(bar, "🔄 Actualizar",
                   lambda: self._cargar_vehiculos_global()
                   ).pack(side="right")

        cols = ("ID","Socio","Puesto","Tipo","Placa","Marca","Modelo","Estado","KM","F.Asig")
        self.tree_veh_g = ttk.Treeview(f, columns=cols, show="headings", height=25)
        for col in cols:
            self.tree_veh_g.heading(col, text=col)
            self.tree_veh_g.column(col, width=100, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=self.tree_veh_g.yview)
        self.tree_veh_g.configure(yscrollcommand=sb.set)
        self.tree_veh_g.pack(side="left", fill="both", expand=True, padx=(10,0), pady=5)
        sb.pack(side="left", fill="y", pady=5, padx=(0,10))

        self._cargar_vehiculos_global()

    def _cargar_vehiculos_global(self):
        for r in self.tree_veh_g.get_children():
            self.tree_veh_g.delete(r)
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT v.id, s.nombre||' '||s.apellido, v.puesto_codigo,
                            v.tipo, v.placa, v.marca, v.modelo,
                            v.estado, v.km, v.fecha_asig
                     FROM vehiculos_historial v
                     LEFT JOIN socios s ON s.id=v.socio_id
                     ORDER BY v.estado, v.fecha_asig DESC""")
        for row in c.fetchall():
            self.tree_veh_g.insert("", "end", values=row)
        conn.close()

    # ── Tab Sanciones global ───────────────────────────────────────────────────
    def _tab_sanciones_global(self):
        f = tk.Frame(self.nb, bg=COLOR_BG)
        self.nb.add(f, text="  Sanciones  ")

        bar = tk.Frame(f, bg=COLOR_BG, pady=6)
        bar.pack(fill="x", padx=10)
        tk.Label(bar, text="Todas las sanciones",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_BOLD).pack(side="left")
        styled_btn(bar, "🔄 Actualizar",
                   lambda: self._cargar_sanciones_global()
                   ).pack(side="right")

        cols = ("ID","Socio","Tipo","Fecha","Descripción","Sanción","Estado")
        self.tree_san_g = ttk.Treeview(f, columns=cols, show="headings", height=25)
        widths = [40, 160, 100, 90, 200, 150, 80]
        for col, w in zip(cols, widths):
            self.tree_san_g.heading(col, text=col)
            self.tree_san_g.column(col, width=w, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=self.tree_san_g.yview)
        self.tree_san_g.configure(yscrollcommand=sb.set)
        self.tree_san_g.pack(side="left", fill="both", expand=True, padx=(10,0), pady=5)
        sb.pack(side="left", fill="y", pady=5, padx=(0,10))

        self._cargar_sanciones_global()

    def _cargar_sanciones_global(self):
        for r in self.tree_san_g.get_children():
            self.tree_san_g.delete(r)
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT sa.id, s.nombre||' '||s.apellido,
                            sa.tipo, sa.fecha, sa.descripcion,
                            sa.sancion_aplicada, sa.estado
                     FROM sanciones sa
                     LEFT JOIN socios s ON s.id=sa.socio_id
                     ORDER BY sa.fecha DESC""")
        for row in c.fetchall():
            self.tree_san_g.insert("", "end", values=row)
        conn.close()

    # ── Tab Reportes ──────────────────────────────────────────────────────────
    def _tab_reportes(self):
        f = tk.Frame(self.nb, bg=COLOR_BG)
        self.nb.add(f, text="  Reportes  ")
        tk.Label(f, text="REPORTES Y ESTADÍSTICAS",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_TITLE).pack(pady=20)

        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM socios")
        total = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM socios WHERE estado='ACTIVO'")
        act = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM sanciones")
        san = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM historial_puestos")
        ventas = c.fetchone()[0]
        conn.close()

        row_f = tk.Frame(f, bg=COLOR_BG)
        row_f.pack()
        for titulo, val, color in [
            ("Total Socios", total, COLOR_ACCENT),
            ("Activos",      act,   COLOR_SUCCESS),
            ("Sanciones",    san,   COLOR_WARN),
            ("Ventas",       ventas,COLOR_DANGER),
        ]:
            card = tk.Frame(row_f, bg=color, padx=30, pady=20)
            card.pack(side="left", padx=15, pady=10)
            tk.Label(card, text=str(val), bg=color, fg="white",
                     font=("Segoe UI", 26, "bold")).pack()
            tk.Label(card, text=titulo, bg=color, fg="white",
                     font=FONT_NORMAL).pack()

        # Historial de ventas
        tk.Label(f, text="Historial de Ventas de Puestos",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_BOLD).pack(anchor="w", padx=20, pady=(20,4))
        cols = ("Puesto","Anterior","Nuevo","Fecha","Valor","Motivo")
        tree_v = ttk.Treeview(f, columns=cols, show="headings", height=10)
        for col in cols:
            tree_v.heading(col, text=col)
            tree_v.column(col, width=150, anchor="center")
        sb = ttk.Scrollbar(f, orient="vertical", command=tree_v.yview)
        tree_v.configure(yscrollcommand=sb.set)
        tree_v.pack(side="left", fill="x", expand=True, padx=(20,0))
        sb.pack(side="left", fill="y")

        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT puesto_codigo, socio_anterior_nombre, socio_nuevo_nombre,
                            fecha_venta, valor, motivo
                     FROM historial_puestos ORDER BY fecha_venta DESC""")
        for row in c.fetchall():
            tree_v.insert("", "end", values=row)
        conn.close()

    # ── Tab Bitácora ──────────────────────────────────────────────────────────
    def _tab_bitacora(self):
        f = tk.Frame(self.nb, bg=COLOR_BG)
        self.nb.add(f, text="  Bitácora  ")
        tk.Label(f, text="BITÁCORA DEL SISTEMA",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_TITLE).pack(pady=20)
        tk.Label(f, text="Módulo en desarrollo", bg=COLOR_BG,
                 fg=COLOR_SUBTEXT, font=FONT_NORMAL).pack()


# ════════════════════════════════════════════════════════════════════════════
# FORMULARIO SOCIO
# ════════════════════════════════════════════════════════════════════════════
class FormSocio(tk.Toplevel):
    def __init__(self, parent, socio_id=None, callback=None):
        super().__init__(parent)
        self.title("Datos del Socio")
        self.configure(bg=COLOR_BG)
        self.grab_set()
        self.resizable(False, False)
        self._socio_id = socio_id
        self._callback = callback
        self._refs = []
        self._foto_var = tk.StringVar()
        self._datos = {}

        if socio_id:
            conn = get_conn(); c = conn.cursor()
            c.execute("SELECT * FROM socios WHERE id=?", (socio_id,))
            row = c.fetchone(); conn.close()
            if row:
                keys = ["id","nombre","apellido","cedula","codigo_puesto",
                        "rango","estado","unidad","fecha_ingreso","foto",
                        "whatsapp","observacion"]
                self._datos = dict(zip(keys, row))
        self._build()

    def _build(self):
        d = self._datos
        campos_izq = [
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

        left = tk.Frame(self, bg=COLOR_BG, padx=20, pady=15)
        left.pack(side="left")

        for i, (label, key) in enumerate(campos_izq):
            tk.Label(left, text=label, bg=COLOR_BG, fg=COLOR_TEXT,
                     font=FONT_NORMAL, anchor="w").grid(row=i, column=0, sticky="w", pady=3)
            e = tk.Entry(left, width=30, bg=COLOR_ENTRY, fg=COLOR_TEXT,
                         insertbackground="white", relief="flat", font=FONT_NORMAL)
            e.insert(0, d.get(key, ""))
            e.grid(row=i, column=1, padx=8, pady=3, ipady=3)
            self._entries[key] = e

        # Estado
        tk.Label(left, text="Estado", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).grid(row=len(campos_izq), column=0, sticky="w", pady=3)
        self._estado_var = tk.StringVar(value=d.get("estado", "ACTIVO"))
        ttk.Combobox(left, textvariable=self._estado_var,
                     values=["ACTIVO","INACTIVO","SUSPENDIDO","VENDIDO"],
                     state="readonly", width=28
                     ).grid(row=len(campos_izq), column=1, padx=8, pady=3)

        # Observación
        tk.Label(left, text="Observación", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).grid(row=len(campos_izq)+1, column=0, sticky="nw", pady=3)
        self._obs = tk.Text(left, width=30, height=3, bg=COLOR_ENTRY,
                            fg=COLOR_TEXT, insertbackground="white", relief="flat")
        self._obs.insert("1.0", d.get("observacion",""))
        self._obs.grid(row=len(campos_izq)+1, column=1, padx=8, pady=3)

        # Botón guardar
        styled_btn(left, "💾  Guardar", self._guardar,
                   bg=COLOR_SUCCESS, width=20, pady=6
                   ).grid(row=len(campos_izq)+2, column=0, columnspan=2, pady=12)

        # Foto (derecha)
        right = tk.Frame(self, bg=COLOR_BG, padx=15, pady=15)
        right.pack(side="left", anchor="n")
        tk.Label(right, text="Foto", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_BOLD).pack()
        self._foto_lbl = tk.Label(right, bg=COLOR_PANEL, width=20, height=10)
        self._foto_lbl.pack(pady=5)
        self._foto_var.set(d.get("foto",""))
        self._actualizar_foto_preview()
        styled_btn(right, "📷 Seleccionar foto", self._sel_foto,
                   bg=COLOR_ACCENT).pack()

    def _sel_foto(self):
        f = filedialog.askopenfilename(
            filetypes=[("Imágenes","*.jpg *.jpeg *.png *.bmp")])
        if f:
            self._foto_var.set(f)
            self._actualizar_foto_preview()

    def _actualizar_foto_preview(self):
        ph = load_image(self._foto_var.get(), (160, 130))
        if ph:
            self._refs.append(ph)
            self._foto_lbl.config(image=ph, width=160, height=130)

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
            if self._socio_id:
                c.execute("""UPDATE socios SET nombre=?,apellido=?,cedula=?,
                             codigo_puesto=?,rango=?,estado=?,unidad=?,
                             fecha_ingreso=?,foto=?,whatsapp=?,observacion=?
                             WHERE id=?""", vals + (self._socio_id,))
            else:
                c.execute("""INSERT INTO socios
                             (nombre,apellido,cedula,codigo_puesto,rango,estado,
                              unidad,fecha_ingreso,foto,whatsapp,observacion)
                             VALUES (?,?,?,?,?,?,?,?,?,?,?)""", vals)
            conn.commit()
            messagebox.showinfo("OK","Socio guardado correctamente.")
            self.destroy()
            if self._callback:
                self._callback()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error","Cédula ya registrada.")
        finally:
            conn.close()


# ════════════════════════════════════════════════════════════════════════════
# VENTANA EXPEDIENTE (3 COLUMNAS)
# ════════════════════════════════════════════════════════════════════════════
class ExpedienteWindow(tk.Toplevel):
    def __init__(self, parent, socio_id):
        super().__init__(parent)
        self._socio_id = socio_id
        self._refs = []
        self._cargar_socio()
        self.title(f"Expediente — {self._s.get('nombre','')} {self._s.get('apellido','')}")
        self.geometry("1340x820")
        self.configure(bg=COLOR_BG)
        self._build()

    def _cargar_socio(self):
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT * FROM socios WHERE id=?", (self._socio_id,))
        row = c.fetchone(); conn.close()
        keys = ["id","nombre","apellido","cedula","codigo_puesto","rango",
                "estado","unidad","fecha_ingreso","foto","whatsapp","observacion"]
        self._s = dict(zip(keys, row)) if row else {}

    # ── Layout ───────────────────────────────────────────────────────────────
    def _build(self):
        # Header
        hdr = tk.Frame(self, bg=COLOR_BG, pady=8)
        hdr.pack(fill="x")
        tk.Label(hdr,
                 text=f"EXPEDIENTE PERSONAL  —  {self._s.get('nombre','')} {self._s.get('apellido','')}",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_TITLE).pack(side="left", padx=20)
        styled_btn(hdr, "✏️ Editar datos",
                   lambda: FormSocio(self, self._socio_id, callback=self._refresh),
                   bg=COLOR_ACCENT).pack(side="right", padx=10)

        # 3 columnas con scroll
        outer = tk.Frame(self, bg=COLOR_BG)
        outer.pack(fill="both", expand=True, padx=6, pady=6)

        # Columna 1
        col1_outer = tk.Frame(outer, bg=COLOR_BG, width=320)
        col1_outer.pack(side="left", fill="both", expand=False, padx=(0,4))
        col1_outer.pack_propagate(False)
        c1_canvas = tk.Canvas(col1_outer, bg=COLOR_BG, highlightthickness=0)
        c1_sb = ttk.Scrollbar(col1_outer, orient="vertical", command=c1_canvas.yview)
        self._col1 = tk.Frame(c1_canvas, bg=COLOR_BG)
        self._col1.bind("<Configure>",
                        lambda e: c1_canvas.configure(
                            scrollregion=c1_canvas.bbox("all")))
        c1_canvas.create_window((0,0), window=self._col1, anchor="nw")
        c1_canvas.configure(yscrollcommand=c1_sb.set)
        c1_canvas.pack(side="left", fill="both", expand=True)
        c1_sb.pack(side="right", fill="y")

        # Columna 2
        col2_outer = tk.Frame(outer, bg=COLOR_BG)
        col2_outer.pack(side="left", fill="both", expand=True, padx=4)
        c2_canvas = tk.Canvas(col2_outer, bg=COLOR_BG, highlightthickness=0)
        c2_sb = ttk.Scrollbar(col2_outer, orient="vertical", command=c2_canvas.yview)
        self._col2 = tk.Frame(c2_canvas, bg=COLOR_BG)
        self._col2.bind("<Configure>",
                        lambda e: c2_canvas.configure(
                            scrollregion=c2_canvas.bbox("all")))
        c2_canvas.create_window((0,0), window=self._col2, anchor="nw")
        c2_canvas.configure(yscrollcommand=c2_sb.set)
        c2_canvas.pack(side="left", fill="both", expand=True)
        c2_sb.pack(side="right", fill="y")

        # Columna 3
        col3_outer = tk.Frame(outer, bg=COLOR_BG, width=340)
        col3_outer.pack(side="left", fill="both", expand=False, padx=(4,0))
        col3_outer.pack_propagate(False)
        c3_canvas = tk.Canvas(col3_outer, bg=COLOR_BG, highlightthickness=0)
        c3_sb = ttk.Scrollbar(col3_outer, orient="vertical", command=c3_canvas.yview)
        self._col3 = tk.Frame(c3_canvas, bg=COLOR_BG)
        self._col3.bind("<Configure>",
                        lambda e: c3_canvas.configure(
                            scrollregion=c3_canvas.bbox("all")))
        c3_canvas.create_window((0,0), window=self._col3, anchor="nw")
        c3_canvas.configure(yscrollcommand=c3_sb.set)
        c3_canvas.pack(side="left", fill="both", expand=True)
        c3_sb.pack(side="right", fill="y")

        self._build_col1()
        self._build_col2()
        self._build_col3()

    # ────────────────────────────────────────────────────────────────────────
    # COLUMNA 1 — DATOS DEL PERSONAL
    # ────────────────────────────────────────────────────────────────────────
    def _build_col1(self):
        p = self._col1
        s = self._s

        tk.Label(p, text="DATOS DEL PERSONAL",
                 bg=COLOR_BG, fg=COLOR_ACCENT, font=FONT_BOLD).pack(pady=(6,4))

        # Foto
        foto_frame = tk.Frame(p, bg=COLOR_PANEL, width=300, height=250)
        foto_frame.pack(pady=4)
        foto_frame.pack_propagate(False)
        self._foto_lbl = tk.Label(foto_frame, bg=COLOR_PANEL,
                                  text="Sin foto", fg=COLOR_SUBTEXT)
        self._foto_lbl.pack(expand=True)
        ph = load_image(s.get("foto",""), (300, 250))
        if ph:
            self._refs.append(ph)
            self._foto_lbl.config(image=ph, text="")

        # Datos personales
        info_frame = lf(p, "Información Personal", bg=COLOR_PANEL)
        info_frame.pack(fill="x", padx=4, pady=4)

        def fila(parent, etiqueta, valor, vcolor=COLOR_TEXT):
            row = tk.Frame(parent, bg=COLOR_PANEL)
            row.pack(fill="x", padx=8, pady=2)
            tk.Label(row, text=etiqueta+":", bg=COLOR_PANEL,
                     fg=COLOR_SUBTEXT, font=FONT_SMALL, width=13, anchor="w").pack(side="left")
            tk.Label(row, text=str(valor or "—"), bg=COLOR_PANEL,
                     fg=vcolor, font=FONT_BOLD, anchor="w").pack(side="left")

        fila(info_frame, "Nombre",
             f"{s.get('nombre','')} {s.get('apellido','')}")
        fila(info_frame, "Cédula",       s.get("cedula",""))
        fila(info_frame, "Código",       s.get("codigo_puesto",""))
        fila(info_frame, "Rango",        s.get("rango",""))
        fila(info_frame, "Estado",       s.get("estado",""),
             COLOR_SUCCESS if s.get("estado")=="ACTIVO" else COLOR_DANGER)
        fila(info_frame, "Unidad",       s.get("unidad",""))
        fila(info_frame, "Fecha Ingreso",s.get("fecha_ingreso",""))

        # WhatsApp
        if s.get("whatsapp"):
            wa_f = tk.Frame(info_frame, bg=COLOR_PANEL)
            wa_f.pack(fill="x", padx=8, pady=4)
            styled_btn(wa_f, f"📱 WhatsApp {s.get('whatsapp','')}",
                       lambda: whatsapp_open(s.get("whatsapp","")),
                       bg="#25D366").pack(fill="x")

        # ── Arrendatario ──────────────────────────────────────────────────
        arr_lf = lf(p, "ARRENDATARIO", fg=COLOR_WARN, bg=COLOR_PANEL)
        arr_lf.pack(fill="x", padx=4, pady=6)

        arr_bar = tk.Frame(arr_lf, bg=COLOR_PANEL); arr_bar.pack(fill="x", padx=6, pady=4)

        self._arr_var = tk.StringVar(value="— Sin arrendatario activo —")
        self._arr_cb = ttk.Combobox(arr_lf, textvariable=self._arr_var,
                                    state="readonly", width=34, font=FONT_NORMAL)
        self._arr_cb.pack(padx=6, pady=2)
        self._cargar_arrendatarios_combo()

        btn_arr = tk.Frame(arr_lf, bg=COLOR_PANEL); btn_arr.pack(fill="x", padx=6, pady=4)
        styled_btn(btn_arr, "+ Agregar Arrendatario",
                   self._form_arrendatario, bg=COLOR_ACCENT).pack(side="left", padx=(0,4))
        styled_btn(btn_arr, "👁 Ver Arrendatarios",
                   self._ver_arrendatarios, bg=COLOR_PANEL).pack(side="left")

        # ── Venta de Puesto ───────────────────────────────────────────────
        styled_btn(p, "🔴  VENTA DE PUESTO",
                   self._venta_puesto, bg=COLOR_DANGER,
                   width=34, pady=8, font=FONT_BOLD).pack(pady=8, padx=4, fill="x")

        # ── Historial de este Puesto ──────────────────────────────────────
        hist_lf = lf(p, "Historial de este Puesto", bg=COLOR_PANEL)
        hist_lf.pack(fill="x", padx=4, pady=4)
        self._hist_frame = hist_lf
        self._cargar_historial_puesto()

    def _cargar_arrendatarios_combo(self):
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT id, nombre||' - '||cedula
                     FROM arrendatarios
                     WHERE socio_id=? AND estado='ACTIVO'""",
                  (self._socio_id,))
        rows = c.fetchall(); conn.close()
        nombres = [r[1] for r in rows]
        self._arr_ids = [r[0] for r in rows]
        self._arr_cb["values"] = nombres if nombres else ["— Sin arrendatario activo —"]
        if nombres:
            self._arr_cb.current(0)

    def _cargar_historial_puesto(self):
        for w in self._hist_frame.winfo_children():
            w.destroy()
        tk.Label(self._hist_frame, text="Historial de este Puesto",
                 bg=COLOR_PANEL, fg=COLOR_TEXT, font=FONT_BOLD).pack()
        codigo = self._s.get("codigo_puesto","")
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT fecha_venta, socio_anterior_nombre,
                            socio_nuevo_nombre, valor, motivo
                     FROM historial_puestos
                     WHERE puesto_codigo=?
                     ORDER BY fecha_venta DESC""", (codigo,))
        rows = c.fetchall(); conn.close()
        if not rows:
            tk.Label(self._hist_frame, text="Sin historial registrado.",
                     bg=COLOR_PANEL, fg=COLOR_SUBTEXT, font=FONT_SMALL).pack(padx=6, pady=4)
        for row in rows:
            f_date, ant, nvo, val, mot = row
            card = tk.Frame(self._hist_frame, bg=COLOR_CARD, pady=4, padx=6)
            card.pack(fill="x", padx=6, pady=2)
            tk.Label(card, text=f"📅 {f_date}  💰 ${val}",
                     bg=COLOR_CARD, fg=COLOR_WARN, font=FONT_SMALL).pack(anchor="w")
            tk.Label(card, text=f"  {ant} → {nvo}",
                     bg=COLOR_CARD, fg=COLOR_TEXT, font=FONT_SMALL).pack(anchor="w")
            if mot:
                tk.Label(card, text=f"  Motivo: {mot}",
                         bg=COLOR_CARD, fg=COLOR_SUBTEXT, font=FONT_SMALL).pack(anchor="w")

    # ── Arrendatario form ────────────────────────────────────────────────────
    def _form_arrendatario(self, arr_id=None):
        FormArrendatario(self, self._socio_id, self._s.get("codigo_puesto",""),
                         arr_id, callback=self._cargar_arrendatarios_combo)

    def _ver_arrendatarios(self):
        VerArrendatarios(self, self._socio_id)

    # ── Venta de Puesto ──────────────────────────────────────────────────────
    def _venta_puesto(self):
        VentaPuesto(self, self._socio_id, self._s,
                    callback=self._refresh)

    # ────────────────────────────────────────────────────────────────────────
    # COLUMNA 2 — VEHÍCULOS
    # ────────────────────────────────────────────────────────────────────────
    def _build_col2(self):
        p = self._col2

        tk.Label(p, text="VEHÍCULOS ASIGNADOS",
                 bg=COLOR_BG, fg=COLOR_ACCENT, font=FONT_BOLD).pack(pady=(6,4))

        bar = tk.Frame(p, bg=COLOR_BG); bar.pack(fill="x", padx=4, pady=4)
        styled_btn(bar, "+ Agregar Vehículo",
                   self._form_vehiculo, bg=COLOR_SUCCESS).pack(side="left", padx=(0,4))
        styled_btn(bar, "📋 Historial Completo del Puesto",
                   self._historial_vehiculos_puesto, bg=COLOR_PANEL).pack(side="left")

        # Contenedor de cards
        self._veh_container = tk.Frame(p, bg=COLOR_BG)
        self._veh_container.pack(fill="both", expand=True, padx=4)
        self._cargar_vehiculos()

    def _cargar_vehiculos(self):
        for w in self._veh_container.winfo_children():
            w.destroy()
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT id,tipo,marca,modelo,placa,color,estado,km,
                            foto,fecha_asig,fecha_baja,motivo_baja
                     FROM vehiculos_historial
                     WHERE socio_id=?
                     ORDER BY CASE estado
                         WHEN 'Actual' THEN 0
                         WHEN 'Operativo' THEN 1
                         WHEN 'En Mantenimiento' THEN 2
                         ELSE 3 END, fecha_asig DESC""",
                  (self._socio_id,))
        rows = c.fetchall(); conn.close()

        if not rows:
            tk.Label(self._veh_container,
                     text="No hay vehículos registrados.",
                     bg=COLOR_BG, fg=COLOR_SUBTEXT, font=FONT_NORMAL
                     ).pack(pady=20)
            return

        for row in rows:
            vid, tipo, marca, modelo, placa, color, estado, km, foto, f_asig, f_baja, motivo = row
            # Color de estado
            if estado in ("Actual","Operativo"):
                e_color = COLOR_SUCCESS
            elif estado == "En Mantenimiento":
                e_color = COLOR_WARN
            else:
                e_color = "#7f8c8d"

            card = tk.Frame(self._veh_container, bg="#ffffff",
                            relief="flat", pady=6, padx=8)
            card.pack(fill="x", pady=4)

            # Foto vehículo
            foto_lbl = tk.Label(card, bg="#ffffff", width=8, height=4)
            foto_lbl.pack(side="left", padx=(0,8))
            ph = load_image(foto, (80, 70))
            if ph:
                self._refs.append(ph)
                foto_lbl.config(image=ph, width=80, height=70)
            else:
                foto_lbl.config(text="🚗", font=("Segoe UI",20), fg="#aaa")

            info = tk.Frame(card, bg="#ffffff"); info.pack(side="left", fill="both", expand=True)

            tk.Label(info, text=f"{tipo}  {marca} {modelo}",
                     bg="#ffffff", fg="#1a1a2e", font=FONT_BOLD, anchor="w").pack(anchor="w")
            tk.Label(info, text=f"Placa: {placa}   Color: {color}",
                     bg="#ffffff", fg="#555", font=FONT_NORMAL, anchor="w").pack(anchor="w")
            tk.Label(info,
                     text=f"Estado: {estado}",
                     bg="#ffffff", fg=e_color, font=FONT_BOLD, anchor="w").pack(anchor="w")
            tk.Label(info, text=f"KM: {km}   F.Asig: {f_asig}",
                     bg="#ffffff", fg="#555", font=FONT_SMALL, anchor="w").pack(anchor="w")
            if f_baja:
                tk.Label(info, text=f"F.Baja: {f_baja}  Motivo: {motivo}",
                         bg="#ffffff", fg="#999", font=FONT_SMALL, anchor="w").pack(anchor="w")

            btn_f = tk.Frame(card, bg="#ffffff"); btn_f.pack(side="right", anchor="n")
            styled_btn(btn_f, "✏️", lambda v=vid: self._form_vehiculo(v),
                       bg=COLOR_ACCENT, width=3, pady=2).pack(pady=2)
            if estado not in ("Histórico", "Baja"):
                styled_btn(btn_f, "🚫 Baja",
                           lambda v=vid: self._dar_baja_vehiculo(v),
                           bg=COLOR_DANGER, width=6, pady=2).pack(pady=2)

    def _form_vehiculo(self, veh_id=None):
        FormVehiculo(self, self._socio_id, self._s.get("codigo_puesto",""),
                     veh_id, callback=self._cargar_vehiculos)

    def _dar_baja_vehiculo(self, veh_id):
        # Será reemplazado por el monkey-patch al final del módulo
        pass

    def _historial_vehiculos_puesto(self):
        codigo = self._s.get("codigo_puesto","")
        win = tk.Toplevel(self)
        win.title(f"Historial de vehículos — Puesto {codigo}")
        win.configure(bg=COLOR_BG)
        win.geometry("800x500")
        cols = ("ID","Socio","Tipo","Placa","Marca","Modelo","Estado","F.Asig","F.Baja")
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

    # ────────────────────────────────────────────────────────────────────────
    # COLUMNA 3 — DOCUMENTOS / SANCIONES
    # ────────────────────────────────────────────────────────────────────────
    def _build_col3(self):
        p = self._col3

        tk.Label(p, text="DOCUMENTOS DE SANCIONES",
                 bg=COLOR_BG, fg=COLOR_ACCENT, font=FONT_BOLD).pack(pady=(6,4))

        bar = tk.Frame(p, bg=COLOR_BG); bar.pack(fill="x", padx=4, pady=4)
        styled_btn(bar, "+ Agregar Documento / Sanción",
                   self._form_sancion, bg=COLOR_DANGER).pack(fill="x")

        self._san_container = tk.Frame(p, bg=COLOR_BG)
        self._san_container.pack(fill="both", expand=True, padx=4)
        self._cargar_sanciones()

    def _cargar_sanciones(self):
        for w in self._san_container.winfo_children():
            w.destroy()
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT id,tipo,fecha,descripcion,sancion_aplicada,estado,documento
                     FROM sanciones
                     WHERE socio_id=?
                     ORDER BY fecha DESC""", (self._socio_id,))
        rows = c.fetchall(); conn.close()

        if not rows:
            tk.Label(self._san_container,
                     text="No hay sanciones registradas.",
                     bg=COLOR_BG, fg=COLOR_SUBTEXT, font=FONT_NORMAL
                     ).pack(pady=20)
            return

        for row in rows:
            sid, tipo, fecha, desc, sancion, estado, doc = row
            e_color = COLOR_DANGER if estado == "Vigente" else "#7f8c8d"

            card = tk.Frame(self._san_container, bg="#d0d8e4",
                            relief="flat", pady=6, padx=8)
            card.pack(fill="x", pady=3)

            top_row = tk.Frame(card, bg="#d0d8e4"); top_row.pack(fill="x")
            tk.Label(top_row, text=f"⚠️  {tipo}",
                     bg="#d0d8e4", fg="#1a1a2e", font=FONT_BOLD).pack(side="left")
            tk.Label(top_row, text=estado,
                     bg="#d0d8e4", fg=e_color, font=FONT_BOLD).pack(side="right")

            tk.Label(card, text=f"📅 {fecha}",
                     bg="#d0d8e4", fg="#333", font=FONT_SMALL, anchor="w").pack(anchor="w")
            if desc:
                tk.Label(card, text=desc[:80]+("…" if len(desc)>80 else ""),
                         bg="#d0d8e4", fg="#444", font=FONT_SMALL,
                         wraplength=290, justify="left", anchor="w").pack(anchor="w")
            if sancion:
                tk.Label(card, text=f"Sanción: {sancion}",
                         bg="#d0d8e4", fg="#8b0000", font=FONT_SMALL, anchor="w").pack(anchor="w")

            btn_row = tk.Frame(card, bg="#d0d8e4"); btn_row.pack(fill="x", pady=(4,0))
            if doc and os.path.isfile(doc):
                styled_btn(btn_row, "📄 Ver Documento",
                           lambda d=doc: os.startfile(d),
                           bg=COLOR_ACCENT, pady=2).pack(side="left", padx=(0,4))
            styled_btn(btn_row, "✏️ Editar",
                       lambda s=sid: self._form_sancion(s),
                       bg="#555", pady=2).pack(side="left")
            styled_btn(btn_row, "🗑️",
                       lambda s=sid: self._eliminar_sancion(s),
                       bg=COLOR_DANGER, width=3, pady=2).pack(side="right")

    def _form_sancion(self, san_id=None):
        FormSancion(self, self._socio_id, san_id,
                    callback=self._cargar_sanciones)

    def _eliminar_sancion(self, san_id):
        if messagebox.askyesno("Confirmar","¿Eliminar esta sanción?"):
            conn = get_conn(); c = conn.cursor()
            c.execute("DELETE FROM sanciones WHERE id=?", (san_id,))
            conn.commit(); conn.close()
            self._cargar_sanciones()

    # ── Refresh global ───────────────────────────────────────────────────────
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
    def __init__(self, parent, socio_id, puesto_codigo, veh_id=None, callback=None):
        super().__init__(parent)
        self.title("Vehículo")
        self.configure(bg=COLOR_BG)
        self.grab_set()
        self.resizable(False, False)
        self._socio_id     = socio_id
        self._puesto       = puesto_codigo
        self._veh_id       = veh_id
        self._callback     = callback
        self._refs         = []
        self._foto_var     = tk.StringVar()
        self._datos        = {}

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
            ("Tipo",        "tipo",      ["Automóvil","Camioneta","Moto","Camión","Otro"]),
            ("Marca",       "marca",     None),
            ("Modelo",      "modelo",    None),
            ("Placa",       "placa",     None),
            ("Color",       "color",     None),
            ("KM",          "km",        None),
            ("Fecha Asig.", "fecha_asig",None),
        ]
        self._entries = {}
        for i, (lbl, key, opts) in enumerate(campos):
            tk.Label(self, text=lbl, bg=COLOR_BG, fg=COLOR_TEXT,
                     font=FONT_NORMAL).grid(row=i, column=0, padx=12, pady=4, sticky="w")
            if opts:
                var = tk.StringVar(value=d.get(key,""))
                w = ttk.Combobox(self, textvariable=var, values=opts,
                                 width=26, state="readonly")
                w.grid(row=i, column=1, padx=12, pady=4)
                self._entries[key] = var
            else:
                e = tk.Entry(self, width=28, bg=COLOR_ENTRY, fg=COLOR_TEXT,
                             insertbackground="white", relief="flat", font=FONT_NORMAL)
                e.insert(0, d.get(key, datetime.now().strftime("%Y-%m-%d")
                                   if key=="fecha_asig" else ""))
                e.grid(row=i, column=1, padx=12, pady=4, ipady=3)
                self._entries[key] = e

        # Estado
        tk.Label(self, text="Estado", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).grid(row=len(campos), column=0, padx=12, pady=4, sticky="w")
        self._estado_var = tk.StringVar(value=d.get("estado","Actual"))
        ttk.Combobox(self, textvariable=self._estado_var,
                     values=["Actual","Operativo","En Mantenimiento","Histórico","Baja"],
                     state="readonly", width=26
                     ).grid(row=len(campos), column=1, padx=12, pady=4)

        # Foto
        tk.Label(self, text="Foto", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).grid(row=len(campos)+1, column=0, padx=12, sticky="w")
        foto_lbl = tk.Label(self, bg=COLOR_PANEL, width=12, height=6,
                            text="Sin foto", fg=COLOR_SUBTEXT)
        foto_lbl.grid(row=len(campos)+1, column=1, padx=12, pady=4)
        ph = load_image(self._foto_var.get(), (120, 90))
        if ph:
            self._refs.append(ph)
            foto_lbl.config(image=ph, text="")

        def sel_foto():
            f = filedialog.askopenfilename(
                filetypes=[("Imágenes","*.jpg *.jpeg *.png")])
            if f:
                self._foto_var.set(f)
                p2 = load_image(f, (120,90))
                if p2:
                    self._refs.append(p2)
                    foto_lbl.config(image=p2, text="")

        styled_btn(self, "📷 Seleccionar", sel_foto,
                   bg=COLOR_ACCENT).grid(row=len(campos)+2, column=1,
                                         padx=12, pady=2, sticky="w")

        styled_btn(self, "💾 Guardar", self._guardar,
                   bg=COLOR_SUCCESS, width=20, pady=6
                   ).grid(row=len(campos)+3, column=0,
                          columnspan=2, pady=12)

    def _get(self, key):
        v = self._entries.get(key)
        if v is None:
            return ""
        return v.get() if hasattr(v, "get") else ""

    def _guardar(self):
        foto_dest = (copiar_archivo(self._foto_var.get(), DIR_VEH)
                     if self._foto_var.get() else self._datos.get("foto",""))
        vals = (
            self._socio_id,
            self._puesto,
            self._get("tipo"),
            self._get("marca"),
            self._get("modelo"),
            self._get("placa"),
            self._get("color"),
            self._estado_var.get(),
            self._get("km"),
            foto_dest,
            self._get("fecha_asig"),
        )
        conn = get_conn(); c = conn.cursor()
        if self._veh_id:
            c.execute("""UPDATE vehiculos_historial
                         SET socio_id=?,puesto_codigo=?,tipo=?,marca=?,modelo=?,
                             placa=?,color=?,estado=?,km=?,foto=?,fecha_asig=?
                         WHERE id=?""", vals + (self._veh_id,))
        else:
            c.execute("""INSERT INTO vehiculos_historial
                         (socio_id,puesto_codigo,tipo,marca,modelo,
                          placa,color,estado,km,foto,fecha_asig)
                         VALUES (?,?,?,?,?,?,?,?,?,?,?)""", vals)
        conn.commit(); conn.close()
        messagebox.showinfo("OK","Vehículo guardado.")
        self.destroy()
        if self._callback:
            self._callback()


# ════════════════════════════════════════════════════════════════════════════
# FORMULARIO SANCIÓN
# ════════════════════════════════════════════════════════════════════════════
class FormSancion(tk.Toplevel):
    def __init__(self, parent, socio_id, san_id=None, callback=None):
        super().__init__(parent)
        self.title("Sanción / Documento")
        self.configure(bg=COLOR_BG)
        self.grab_set()
        self.resizable(False, False)
        self._socio_id = socio_id
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

        tk.Label(self, text="Tipo", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).grid(row=0, column=0, padx=12, pady=5, sticky="w")
        self._tipo_var = tk.StringVar(value=d.get("tipo",""))
        ttk.Combobox(self, textvariable=self._tipo_var,
                     values=["Económica","Disciplinaria","Suspensión",
                             "Advertencia","Amonestación","Otro"],
                     width=28).grid(row=0, column=1, padx=12, pady=5)

        tk.Label(self, text="Fecha", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).grid(row=1, column=0, padx=12, pady=5, sticky="w")
        self._fecha_e = tk.Entry(self, width=30, bg=COLOR_ENTRY, fg=COLOR_TEXT,
                                 insertbackground="white", relief="flat")
        self._fecha_e.insert(0, d.get("fecha", datetime.now().strftime("%Y-%m-%d")))
        self._fecha_e.grid(row=1, column=1, padx=12, pady=5, ipady=3)

        tk.Label(self, text="Descripción", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).grid(row=2, column=0, padx=12, pady=5, sticky="nw")
        self._desc_t = tk.Text(self, width=30, height=4, bg=COLOR_ENTRY,
                               fg=COLOR_TEXT, insertbackground="white", relief="flat")
        self._desc_t.insert("1.0", d.get("descripcion",""))
        self._desc_t.grid(row=2, column=1, padx=12, pady=5)

        tk.Label(self, text="Sanción Aplicada", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).grid(row=3, column=0, padx=12, pady=5, sticky="nw")
        self._san_t = tk.Text(self, width=30, height=3, bg=COLOR_ENTRY,
                              fg=COLOR_TEXT, insertbackground="white", relief="flat")
        self._san_t.insert("1.0", d.get("sancion_aplicada",""))
        self._san_t.grid(row=3, column=1, padx=12, pady=5)

        tk.Label(self, text="Estado", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).grid(row=4, column=0, padx=12, pady=5, sticky="w")
        self._estado_var = tk.StringVar(value=d.get("estado","Vigente"))
        ttk.Combobox(self, textvariable=self._estado_var,
                     values=["Vigente","Cumplida","Apelada","Anulada"],
                     state="readonly", width=28
                     ).grid(row=4, column=1, padx=12, pady=5)

        # Documento adjunto
        tk.Label(self, text="Documento", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).grid(row=5, column=0, padx=12, pady=5, sticky="w")
        doc_row = tk.Frame(self, bg=COLOR_BG); doc_row.grid(row=5, column=1, padx=12, pady=5, sticky="w")
        tk.Entry(doc_row, textvariable=self._doc_var, width=22,
                 bg=COLOR_ENTRY, fg=COLOR_TEXT, state="readonly",
                 relief="flat").pack(side="left")
        styled_btn(doc_row, "📎",
                   lambda: self._doc_var.set(
                       filedialog.askopenfilename(
                           filetypes=[("Archivos","*.pdf *.jpg *.png *.docx")])),
                   bg=COLOR_ACCENT, width=3).pack(side="left", padx=4)

        styled_btn(self, "💾 Guardar", self._guardar,
                   bg=COLOR_SUCCESS, width=20, pady=6
                   ).grid(row=6, column=0, columnspan=2, pady=12)

    def _guardar(self):
        doc_dest = (copiar_archivo(self._doc_var.get(), DIR_DOCS)
                    if self._doc_var.get() else self._datos.get("documento",""))
        vals = (
            self._socio_id,
            self._tipo_var.get(),
            self._fecha_e.get(),
            self._desc_t.get("1.0","end-1c"),
            self._san_t.get("1.0","end-1c"),
            self._estado_var.get(),
            doc_dest,
        )
        conn = get_conn(); c = conn.cursor()
        if self._san_id:
            c.execute("""UPDATE sanciones
                         SET socio_id=?,tipo=?,fecha=?,descripcion=?,
                             sancion_aplicada=?,estado=?,documento=?
                         WHERE id=?""", vals + (self._san_id,))
        else:
            c.execute("""INSERT INTO sanciones
                         (socio_id,tipo,fecha,descripcion,
                          sancion_aplicada,estado,documento)
                         VALUES (?,?,?,?,?,?,?)""", vals)
        conn.commit(); conn.close()
        messagebox.showinfo("OK","Sanción guardada.")
        self.destroy()
        if self._callback:
            self._callback()


# ════════════════════════════════════════════════════════════════════════════
# FORMULARIO ARRENDATARIO
# ════════════════════════════════════════════════════════════════════════════
class FormArrendatario(tk.Toplevel):
    def __init__(self, parent, socio_id, puesto_codigo, arr_id=None, callback=None):
        super().__init__(parent)
        self.title("Arrendatario")
        self.configure(bg=COLOR_BG)
        self.grab_set()
        self.resizable(False, False)
        self._socio_id = socio_id
        self._puesto   = puesto_codigo
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
        for i, (lbl, key) in enumerate(campos):
            tk.Label(self, text=lbl, bg=COLOR_BG, fg=COLOR_TEXT,
                     font=FONT_NORMAL).grid(row=i, column=0, padx=12, pady=5, sticky="w")
            e = tk.Entry(self, width=30, bg=COLOR_ENTRY, fg=COLOR_TEXT,
                         insertbackground="white", relief="flat", font=FONT_NORMAL)
            e.insert(0, d.get(key, datetime.now().strftime("%Y-%m-%d")
                               if "fecha" in key else ""))
            e.grid(row=i, column=1, padx=12, pady=5, ipady=3)
            self._entries[key] = e

        tk.Label(self, text="Estado", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).grid(row=len(campos), column=0, padx=12, pady=5, sticky="w")
        self._estado_var = tk.StringVar(value=d.get("estado","ACTIVO"))
        ttk.Combobox(self, textvariable=self._estado_var,
                     values=["ACTIVO","INACTIVO","TERMINADO"],
                     state="readonly", width=28
                     ).grid(row=len(campos), column=1, padx=12, pady=5)

        styled_btn(self, "💾 Guardar", self._guardar,
                   bg=COLOR_SUCCESS, width=20, pady=6
                   ).grid(row=len(campos)+1, column=0, columnspan=2, pady=12)

    def _guardar(self):
        vals = (
            self._socio_id,
            self._puesto,
            self._entries["nombre"].get(),
            self._entries["cedula"].get(),
            self._entries["telefono"].get(),
            self._entries["fecha_inicio"].get(),
            self._entries["fecha_fin"].get(),
            self._estado_var.get(),
        )
        conn = get_conn(); c = conn.cursor()
        if self._arr_id:
            c.execute("""UPDATE arrendatarios
                         SET socio_id=?,puesto_codigo=?,nombre=?,cedula=?,
                             telefono=?,fecha_inicio=?,fecha_fin=?,estado=?
                         WHERE id=?""", vals + (self._arr_id,))
        else:
            c.execute("""INSERT INTO arrendatarios
                         (socio_id,puesto_codigo,nombre,cedula,
                          telefono,fecha_inicio,fecha_fin,estado)
                         VALUES (?,?,?,?,?,?,?,?)""", vals)
        conn.commit(); conn.close()
        messagebox.showinfo("OK","Arrendatario guardado.")
        self.destroy()
        if self._callback:
            self._callback()


# ════════════════════════════════════════════════════════════════════════════
# VER ARRENDATARIOS
# ════════════════════════════════════════════════════════════════════════════
class VerArrendatarios(tk.Toplevel):
    def __init__(self, parent, socio_id):
        super().__init__(parent)
        self.title("Arrendatarios del Puesto")
        self.configure(bg=COLOR_BG)
        self.geometry("700x400")
        cols = ("ID","Nombre","Cédula","Teléfono","F.Inicio","F.Fin","Estado")
        tree = ttk.Treeview(self, columns=cols, show="headings", height=15)
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
    """
    Flujo:
      1. Ingresar datos del nuevo socio comprador.
      2. Al confirmar:
         - Crea nuevo socio con mismo codigo_puesto.
         - Marca socio anterior como VENDIDO.
         - Transfiere vehículos estado='Actual' al nuevo socio.
         - Transfiere arrendatarios estado='ACTIVO' al nuevo socio.
         - Registra en historial_puestos.
    """
    def __init__(self, parent, socio_anterior_id, datos_anterior, callback=None):
        super().__init__(parent)
        self.title("Venta de Puesto")
        self.configure(bg=COLOR_BG)
        self.grab_set()
        self.resizable(False, False)
        self._ant_id   = socio_anterior_id
        self._ant      = datos_anterior
        self._callback = callback
        self._doc_var  = tk.StringVar()
        self._build()

    def _build(self):
        tk.Label(self, text="VENTA DE PUESTO",
                 bg=COLOR_BG, fg=COLOR_DANGER, font=FONT_TITLE).grid(
            row=0, column=0, columnspan=2, pady=10)

        tk.Label(self, text=f"Puesto: {self._ant.get('codigo_puesto','')}",
                 bg=COLOR_BG, fg=COLOR_WARN, font=FONT_BOLD).grid(
            row=1, column=0, columnspan=2, pady=4)
        tk.Label(self, text=f"Propietario actual: {self._ant.get('nombre','')} {self._ant.get('apellido','')}",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_NORMAL).grid(
            row=2, column=0, columnspan=2, pady=2)

        sep = tk.Frame(self, bg=COLOR_DANGER, height=1); sep.grid(
            row=3, column=0, columnspan=2, sticky="ew", padx=12, pady=8)

        tk.Label(self, text="— DATOS DEL NUEVO PROPIETARIO —",
                 bg=COLOR_BG, fg=COLOR_TEXT, font=FONT_BOLD).grid(
            row=4, column=0, columnspan=2, pady=4)

        campos = [
            ("Nombre",        "nombre"),
            ("Apellido",      "apellido"),
            ("Cédula",        "cedula"),
            ("Rango",         "rango"),
            ("Unidad",        "unidad"),
            ("WhatsApp",      "whatsapp"),
            ("Valor de Venta","valor"),
            ("Motivo/Notas",  "motivo"),
        ]
        self._entries = {}
        for i, (lbl, key) in enumerate(campos, 5):
            tk.Label(self, text=lbl, bg=COLOR_BG, fg=COLOR_TEXT,
                     font=FONT_NORMAL).grid(row=i, column=0, padx=14, pady=4, sticky="w")
            e = tk.Entry(self, width=32, bg=COLOR_ENTRY, fg=COLOR_TEXT,
                         insertbackground="white", relief="flat", font=FONT_NORMAL)
            e.grid(row=i, column=1, padx=14, pady=4, ipady=3)
            self._entries[key] = e

        # Documento
        row_doc = len(campos) + 5
        tk.Label(self, text="Documento", bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).grid(row=row_doc, column=0, padx=14, pady=4, sticky="w")
        doc_row = tk.Frame(self, bg=COLOR_BG)
        doc_row.grid(row=row_doc, column=1, padx=14, pady=4, sticky="w")
        tk.Entry(doc_row, textvariable=self._doc_var, width=24,
                 bg=COLOR_ENTRY, fg=COLOR_TEXT, state="readonly",
                 relief="flat").pack(side="left")
        styled_btn(doc_row, "📎",
                   lambda: self._doc_var.set(
                       filedialog.askopenfilename(
                           filetypes=[("Archivos","*.pdf *.jpg *.png *.docx")])),
                   bg=COLOR_ACCENT, width=3).pack(side="left", padx=4)

        styled_btn(self, "✅  CONFIRMAR VENTA",
                   self._confirmar, bg=COLOR_DANGER,
                   width=28, pady=8, font=FONT_BOLD
                   ).grid(row=row_doc+1, column=0, columnspan=2, pady=14)

    def _confirmar(self):
        nombre  = self._entries["nombre"].get().strip()
        apellido= self._entries["apellido"].get().strip()
        cedula  = self._entries["cedula"].get().strip()
        if not (nombre and apellido and cedula):
            messagebox.showerror("Error","Nombre, apellido y cédula son obligatorios.")
            return
        if not messagebox.askyesno("Confirmar",
                f"¿Registrar venta del puesto {self._ant.get('codigo_puesto','')} "
                f"a {nombre} {apellido}?"):
            return

        doc_dest = (copiar_archivo(self._doc_var.get(), DIR_VENTAS)
                    if self._doc_var.get() else "")
        codigo   = self._ant.get("codigo_puesto","")
        fecha    = datetime.now().strftime("%Y-%m-%d")

        conn = get_conn(); c = conn.cursor()
        try:
            # 1. Crear nuevo socio
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

            # 2. Marcar anterior como VENDIDO
            c.execute("UPDATE socios SET estado='VENDIDO' WHERE id=?",
                      (self._ant_id,))

            # 3. Transferir vehículos Actual
            c.execute("""UPDATE vehiculos_historial
                         SET socio_id=?
                         WHERE socio_id=? AND estado='Actual'""",
                      (nuevo_id, self._ant_id))

            # 4. Transferir arrendatarios ACTIVO
            c.execute("""UPDATE arrendatarios
                         SET socio_id=?
                         WHERE socio_id=? AND estado='ACTIVO'""",
                      (nuevo_id, self._ant_id))

            # 5. Historial
            c.execute("""INSERT INTO historial_puestos
                         (puesto_codigo, socio_anterior_id, socio_nuevo_id,
                          socio_anterior_nombre, socio_nuevo_nombre,
                          fecha_venta, valor, motivo, documento)
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
                "El socio anterior fue marcado como VENDIDO.\n"
                "Los vehículos actuales y arrendatarios activos fueron transferidos.")
            self.destroy()
            if self._callback:
                self._callback()
        except sqlite3.IntegrityError:
            messagebox.showerror("Error","La cédula del nuevo propietario ya está registrada.")
        finally:
            conn.close()


# ════════════════════════════════════════════════════════════════════════════
# PATCH: simpledialog compatible (evita importar simpledialog completo)
# ════════════════════════════════════════════════════════════════════════════
class _AskStringDialog(tk.Toplevel):
    def __init__(self, parent, title, prompt):
        super().__init__(parent)
        self.title(title)
        self.configure(bg=COLOR_BG)
        self.grab_set()
        self.result = None
        tk.Label(self, text=prompt, bg=COLOR_BG, fg=COLOR_TEXT,
                 font=FONT_NORMAL).pack(padx=20, pady=10)
        self._e = tk.Entry(self, width=40, bg=COLOR_ENTRY, fg=COLOR_TEXT,
                           insertbackground="white", relief="flat")
        self._e.pack(padx=20, pady=4, ipady=4)
        btn_f = tk.Frame(self, bg=COLOR_BG); btn_f.pack(pady=10)
        styled_btn(btn_f, "OK", self._ok, bg=COLOR_SUCCESS, width=10).pack(side="left", padx=6)
        styled_btn(btn_f, "Cancelar", self.destroy, bg=COLOR_DANGER, width=10).pack(side="left", padx=6)
        self._e.focus_set()
        self.bind("<Return>", lambda e: self._ok())

    def _ok(self):
        self.result = self._e.get()
        self.destroy()


def _ask_string(parent, title, prompt):
    d = _AskStringDialog(parent, title, prompt)
    parent.wait_window(d)
    return d.result


# Reemplaza el método placeholder _dar_baja_vehiculo con la implementación real
def _dar_baja_vehiculo_fixed(self, veh_id):
    motivo = _ask_string(self, "Dar de Baja", "Motivo de baja:")
    if motivo is None:
        return
    conn = get_conn(); c = conn.cursor()
    c.execute("""UPDATE vehiculos_historial
                 SET estado='Histórico', fecha_baja=?, motivo_baja=?
                 WHERE id=?""",
              (datetime.now().strftime("%Y-%m-%d"), motivo, veh_id))
    conn.commit(); conn.close()
    self._cargar_vehiculos()

ExpedienteWindow._dar_baja_vehiculo = _dar_baja_vehiculo_fixed


# ════════════════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    app = MainApp()
    app.mainloop()
