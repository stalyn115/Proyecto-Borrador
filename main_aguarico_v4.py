import os, sqlite3, shutil, webbrowser, urllib.parse
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk

DB = "aguarico.db"
FOTOS = "fotos"
DOCS = "documentos_sanciones"
os.makedirs(FOTOS, exist_ok=True)
os.makedirs(DOCS, exist_ok=True)

# ─────────────────────────────────────────────
# BASE DE DATOS
# ─────────────────────────────────────────────
def init_db():
    conn = sqlite3.connect(DB)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS socios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        codigo TEXT, nombre TEXT, apellido TEXT,
        cedula TEXT UNIQUE, telefono TEXT,
        rango TEXT, unidad TEXT, estado TEXT, foto TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS vehiculos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        socio_id INTEGER, placa TEXT, marca TEXT, modelo TEXT, foto TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS sanciones (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        socio_id INTEGER, tipo TEXT, fecha TEXT,
        descripcion TEXT, documento TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS asistencia (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        socio_id INTEGER, fecha TEXT, presente INTEGER,
        hora TEXT, observacion TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS plantillas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nombre TEXT, texto TEXT)""")
    c.execute("SELECT COUNT(*) FROM plantillas")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO plantillas VALUES (NULL,?,?)", (
            "Citacion",
            "Estimado {rango} {nombre} {apellido} CI:{cedula} Cod:{codigo} "
            "sancion {tipo} fecha {fecha} {descripcion} "
            "Presentarse AGRUPACION AGUARICO"
        ))
    conn.commit()
    conn.close()

init_db()

# ─────────────────────────────────────────────
# HELPERS
# ─────────────────────────────────────────────
def get_conn():
    return sqlite3.connect(DB)

def thumb(path, size=(80, 80)):
    """Devuelve un ImageTk.PhotoImage redimensionado o None."""
    try:
        img = Image.open(path)
        img.thumbnail(size)
        return ImageTk.PhotoImage(img)
    except Exception:
        return None

def copiar_archivo(origen, carpeta):
    """Copia un archivo a la carpeta dada y devuelve el nuevo path."""
    if not origen:
        return ""
    nombre = os.path.basename(origen)
    destino = os.path.join(carpeta, nombre)
    shutil.copy2(origen, destino)
    return destino

def enviar_whatsapp(telefono, mensaje):
    tel = telefono.strip().replace(" ", "")
    if not tel.startswith("+"):
        tel = "+593" + tel.lstrip("0")
    url = "https://wa.me/" + tel.lstrip("+") + "?text=" + urllib.parse.quote(mensaje)
    webbrowser.open(url)

# ─────────────────────────────────────────────
# VENTANA PRINCIPAL
# ─────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Agrupación Aguarico v4")
        self.geometry("1100x680")
        self.configure(bg="#1a1a2e")
        self._foto_refs = []  # evitar garbage collection de imágenes
        self._build_ui()

    def _build_ui(self):
        # Barra lateral
        sidebar = tk.Frame(self, bg="#16213e", width=180)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="AGUARICO", bg="#16213e", fg="#e94560",
                 font=("Arial", 14, "bold")).pack(pady=20)

        botones = [
            ("👥 Socios",      self.tab_socios),
            ("🚗 Vehículos",   self.tab_vehiculos),
            ("⚠️ Sanciones",   self.tab_sanciones),
            ("📋 Asistencia",  self.tab_asistencia),
            ("📨 Mensajes",    self.tab_mensajes),
            ("📊 Reportes",    self.tab_reportes),
        ]
        for texto, cmd in botones:
            tk.Button(sidebar, text=texto, bg="#0f3460", fg="white",
                      activebackground="#e94560", activeforeground="white",
                      font=("Arial", 10), relief="flat", cursor="hand2",
                      command=cmd, anchor="w", padx=10
                      ).pack(fill="x", pady=2, padx=6)

        # Área de contenido
        self.content = tk.Frame(self, bg="#1a1a2e")
        self.content.pack(side="left", fill="both", expand=True)

        self.tab_socios()

    def _clear(self):
        for w in self.content.winfo_children():
            w.destroy()
        self._foto_refs.clear()

    # ─── TAB SOCIOS ───────────────────────────
    def tab_socios(self):
        self._clear()
        frame = tk.Frame(self.content, bg="#1a1a2e")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(frame, text="Gestión de Socios", bg="#1a1a2e", fg="#e94560",
                 font=("Arial", 14, "bold")).pack(anchor="w")

        # Barra de búsqueda
        bar = tk.Frame(frame, bg="#1a1a2e")
        bar.pack(fill="x", pady=5)
        tk.Label(bar, text="Buscar:", bg="#1a1a2e", fg="white").pack(side="left")
        self.buscar_socio_var = tk.StringVar()
        tk.Entry(bar, textvariable=self.buscar_socio_var, width=30).pack(side="left", padx=5)
        tk.Button(bar, text="🔍 Buscar", bg="#0f3460", fg="white",
                  command=lambda: self._cargar_socios(self.buscar_socio_var.get())
                  ).pack(side="left")
        tk.Button(bar, text="➕ Nuevo Socio", bg="#e94560", fg="white",
                  command=self._form_socio).pack(side="right")

        # Tabla
        cols = ("ID", "Código", "Nombre", "Apellido", "Cédula", "Teléfono", "Rango", "Unidad", "Estado")
        self.tree_socios = ttk.Treeview(frame, columns=cols, show="headings", height=20)
        for c in cols:
            self.tree_socios.heading(c, text=c)
            self.tree_socios.column(c, width=90, anchor="center")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree_socios.yview)
        self.tree_socios.configure(yscrollcommand=scroll.set)
        self.tree_socios.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

        # Menú contextual
        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="✏️ Editar", command=self._editar_socio)
        menu.add_command(label="🗑️ Eliminar", command=self._eliminar_socio)
        menu.add_separator()
        menu.add_command(label="📨 Enviar WhatsApp", command=self._wa_socio)
        self.tree_socios.bind("<Button-3>", lambda e: menu.post(e.x_root, e.y_root))
        self.tree_socios.bind("<Double-1>", lambda e: self._editar_socio())

        self._cargar_socios()

    def _cargar_socios(self, filtro=""):
        for row in self.tree_socios.get_children():
            self.tree_socios.delete(row)
        conn = get_conn(); c = conn.cursor()
        q = "SELECT id,codigo,nombre,apellido,cedula,telefono,rango,unidad,estado FROM socios"
        if filtro:
            q += " WHERE nombre LIKE ? OR apellido LIKE ? OR cedula LIKE ? OR codigo LIKE ?"
            c.execute(q, (f"%{filtro}%",)*4)
        else:
            c.execute(q)
        for row in c.fetchall():
            self.tree_socios.insert("", "end", values=row)
        conn.close()

    def _form_socio(self, socio_id=None):
        win = tk.Toplevel(self)
        win.title("Socio")
        win.configure(bg="#1a1a2e")
        win.grab_set()

        datos = {}
        if socio_id:
            conn = get_conn(); c = conn.cursor()
            c.execute("SELECT * FROM socios WHERE id=?", (socio_id,))
            row = c.fetchone(); conn.close()
            if row:
                keys = ["id","codigo","nombre","apellido","cedula","telefono","rango","unidad","estado","foto"]
                datos = dict(zip(keys, row))

        campos = [
            ("Código", "codigo"), ("Nombre", "nombre"), ("Apellido", "apellido"),
            ("Cédula", "cedula"), ("Teléfono", "telefono"), ("Rango", "rango"),
            ("Unidad", "unidad"),
        ]
        entries = {}
        for i, (label, key) in enumerate(campos):
            tk.Label(win, text=label, bg="#1a1a2e", fg="white").grid(row=i, column=0, padx=10, pady=4, sticky="w")
            e = tk.Entry(win, width=30)
            e.insert(0, datos.get(key, ""))
            e.grid(row=i, column=1, padx=10, pady=4)
            entries[key] = e

        # Estado
        tk.Label(win, text="Estado", bg="#1a1a2e", fg="white").grid(row=len(campos), column=0, padx=10, pady=4, sticky="w")
        estado_var = tk.StringVar(value=datos.get("estado", "Activo"))
        ttk.Combobox(win, textvariable=estado_var,
                     values=["Activo", "Inactivo", "Suspendido"],
                     state="readonly", width=28).grid(row=len(campos), column=1, padx=10, pady=4)

        # Foto
        foto_var = tk.StringVar(value=datos.get("foto", ""))
        foto_label = tk.Label(win, bg="#1a1a2e")
        foto_label.grid(row=0, column=2, rowspan=4, padx=10)
        if foto_var.get():
            ph = thumb(foto_var.get(), (100, 100))
            if ph:
                foto_label.config(image=ph)
                self._foto_refs.append(ph)

        def sel_foto():
            f = filedialog.askopenfilename(filetypes=[("Imágenes", "*.jpg *.jpeg *.png *.bmp")])
            if f:
                foto_var.set(f)
                ph = thumb(f, (100, 100))
                if ph:
                    foto_label.config(image=ph)
                    self._foto_refs.append(ph)

        tk.Button(win, text="📷 Foto", bg="#0f3460", fg="white",
                  command=sel_foto).grid(row=4, column=2, padx=10)

        def guardar():
            foto_dest = copiar_archivo(foto_var.get(), FOTOS) if foto_var.get() else datos.get("foto","")
            conn = get_conn(); c = conn.cursor()
            vals = (entries["codigo"].get(), entries["nombre"].get(), entries["apellido"].get(),
                    entries["cedula"].get(), entries["telefono"].get(), entries["rango"].get(),
                    entries["unidad"].get(), estado_var.get(), foto_dest)
            try:
                if socio_id:
                    c.execute("""UPDATE socios SET codigo=?,nombre=?,apellido=?,cedula=?,
                                 telefono=?,rango=?,unidad=?,estado=?,foto=? WHERE id=?""",
                              vals + (socio_id,))
                else:
                    c.execute("""INSERT INTO socios
                                 (codigo,nombre,apellido,cedula,telefono,rango,unidad,estado,foto)
                                 VALUES (?,?,?,?,?,?,?,?,?)""", vals)
                conn.commit()
                messagebox.showinfo("OK", "Socio guardado.")
                win.destroy()
                self._cargar_socios()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Cédula ya existe.")
            finally:
                conn.close()

        row_btn = len(campos) + 1
        tk.Button(win, text="💾 Guardar", bg="#e94560", fg="white",
                  command=guardar).grid(row=row_btn, column=0, columnspan=2, pady=10)

    def _editar_socio(self):
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
        if messagebox.askyesno("Confirmar", "¿Eliminar socio?"):
            conn = get_conn(); c = conn.cursor()
            c.execute("DELETE FROM socios WHERE id=?", (sid,))
            conn.commit(); conn.close()
            self._cargar_socios()

    def _wa_socio(self):
        sel = self.tree_socios.selection()
        if not sel:
            return
        vals = self.tree_socios.item(sel[0])["values"]
        sid, nombre, apellido, telefono = vals[0], vals[2], vals[3], vals[5]
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT texto FROM plantillas WHERE nombre='Citacion'")
        row = c.fetchone(); conn.close()
        plantilla = row[0] if row else "Hola {nombre} {apellido}"
        # Obtener datos completos
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT * FROM socios WHERE id=?", (sid,))
        s = c.fetchone(); conn.close()
        keys = ["id","codigo","nombre","apellido","cedula","telefono","rango","unidad","estado","foto"]
        sd = dict(zip(keys, s)) if s else {}
        sd["tipo"] = ""; sd["fecha"] = datetime.now().strftime("%Y-%m-%d"); sd["descripcion"] = ""
        try:
            msg = plantilla.format(**sd)
        except KeyError:
            msg = plantilla
        enviar_whatsapp(str(telefono), msg)

    # ─── TAB VEHÍCULOS ────────────────────────
    def tab_vehiculos(self):
        self._clear()
        frame = tk.Frame(self.content, bg="#1a1a2e")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(frame, text="Vehículos", bg="#1a1a2e", fg="#e94560",
                 font=("Arial", 14, "bold")).pack(anchor="w")

        bar = tk.Frame(frame, bg="#1a1a2e")
        bar.pack(fill="x", pady=5)
        tk.Button(bar, text="➕ Nuevo Vehículo", bg="#e94560", fg="white",
                  command=self._form_vehiculo).pack(side="right")

        cols = ("ID", "Socio ID", "Socio", "Placa", "Marca", "Modelo")
        self.tree_veh = ttk.Treeview(frame, columns=cols, show="headings", height=22)
        for c in cols:
            self.tree_veh.heading(c, text=c)
            self.tree_veh.column(c, width=120, anchor="center")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree_veh.yview)
        self.tree_veh.configure(yscrollcommand=scroll.set)
        self.tree_veh.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="✏️ Editar", command=self._editar_vehiculo)
        menu.add_command(label="🗑️ Eliminar", command=self._eliminar_vehiculo)
        self.tree_veh.bind("<Button-3>", lambda e: menu.post(e.x_root, e.y_root))

        self._cargar_vehiculos()

    def _cargar_vehiculos(self):
        for row in self.tree_veh.get_children():
            self.tree_veh.delete(row)
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT v.id, v.socio_id,
                     s.nombre||' '||s.apellido, v.placa, v.marca, v.modelo
                     FROM vehiculos v
                     LEFT JOIN socios s ON s.id=v.socio_id""")
        for row in c.fetchall():
            self.tree_veh.insert("", "end", values=row)
        conn.close()

    def _form_vehiculo(self, vid=None):
        win = tk.Toplevel(self); win.title("Vehículo"); win.configure(bg="#1a1a2e"); win.grab_set()
        datos = {}
        if vid:
            conn = get_conn(); c = conn.cursor()
            c.execute("SELECT * FROM vehiculos WHERE id=?", (vid,))
            row = c.fetchone(); conn.close()
            if row:
                datos = dict(zip(["id","socio_id","placa","marca","modelo","foto"], row))

        # Selector de socio
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT id, nombre||' '||apellido FROM socios ORDER BY nombre")
        socios = c.fetchall(); conn.close()
        socio_map = {f"{n} (#{i})": i for i, n in socios}
        socio_names = list(socio_map.keys())

        tk.Label(win, text="Socio", bg="#1a1a2e", fg="white").grid(row=0, column=0, padx=10, pady=4, sticky="w")
        socio_var = tk.StringVar()
        cb = ttk.Combobox(win, textvariable=socio_var, values=socio_names, state="readonly", width=30)
        cb.grid(row=0, column=1, padx=10, pady=4)
        if datos.get("socio_id"):
            for k, v in socio_map.items():
                if v == datos["socio_id"]:
                    socio_var.set(k); break

        campos = [("Placa","placa"),("Marca","marca"),("Modelo","modelo")]
        entries = {}
        for i,(label,key) in enumerate(campos,1):
            tk.Label(win, text=label, bg="#1a1a2e", fg="white").grid(row=i, column=0, padx=10, pady=4, sticky="w")
            e = tk.Entry(win, width=32); e.insert(0, datos.get(key,""))
            e.grid(row=i, column=1, padx=10, pady=4); entries[key] = e

        foto_var = tk.StringVar(value=datos.get("foto",""))

        def sel_foto():
            f = filedialog.askopenfilename(filetypes=[("Imágenes","*.jpg *.jpeg *.png")])
            if f: foto_var.set(f)

        tk.Button(win, text="📷 Foto vehículo", bg="#0f3460", fg="white",
                  command=sel_foto).grid(row=4, column=1, pady=4, sticky="w", padx=10)

        def guardar():
            sid = socio_map.get(socio_var.get())
            if not sid:
                messagebox.showerror("Error","Seleccione un socio."); return
            foto_dest = copiar_archivo(foto_var.get(), FOTOS) if foto_var.get() else datos.get("foto","")
            conn = get_conn(); c = conn.cursor()
            if vid:
                c.execute("UPDATE vehiculos SET socio_id=?,placa=?,marca=?,modelo=?,foto=? WHERE id=?",
                          (sid, entries["placa"].get(), entries["marca"].get(), entries["modelo"].get(), foto_dest, vid))
            else:
                c.execute("INSERT INTO vehiculos (socio_id,placa,marca,modelo,foto) VALUES (?,?,?,?,?)",
                          (sid, entries["placa"].get(), entries["marca"].get(), entries["modelo"].get(), foto_dest))
            conn.commit(); conn.close()
            messagebox.showinfo("OK","Vehículo guardado.")
            win.destroy(); self._cargar_vehiculos()

        tk.Button(win, text="💾 Guardar", bg="#e94560", fg="white",
                  command=guardar).grid(row=5, column=0, columnspan=2, pady=10)

    def _editar_vehiculo(self):
        sel = self.tree_veh.selection()
        if not sel: return
        vid = self.tree_veh.item(sel[0])["values"][0]
        self._form_vehiculo(vid)

    def _eliminar_vehiculo(self):
        sel = self.tree_veh.selection()
        if not sel: return
        vid = self.tree_veh.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar","¿Eliminar vehículo?"):
            conn = get_conn(); c = conn.cursor()
            c.execute("DELETE FROM vehiculos WHERE id=?", (vid,))
            conn.commit(); conn.close()
            self._cargar_vehiculos()

    # ─── TAB SANCIONES ────────────────────────
    def tab_sanciones(self):
        self._clear()
        frame = tk.Frame(self.content, bg="#1a1a2e")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(frame, text="Sanciones", bg="#1a1a2e", fg="#e94560",
                 font=("Arial", 14, "bold")).pack(anchor="w")

        bar = tk.Frame(frame, bg="#1a1a2e"); bar.pack(fill="x", pady=5)
        tk.Button(bar, text="➕ Nueva Sanción", bg="#e94560", fg="white",
                  command=self._form_sancion).pack(side="right")

        cols = ("ID","Socio","Tipo","Fecha","Descripción","Documento")
        self.tree_san = ttk.Treeview(frame, columns=cols, show="headings", height=22)
        for c in cols:
            self.tree_san.heading(c, text=c)
            self.tree_san.column(c, width=130, anchor="center")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree_san.yview)
        self.tree_san.configure(yscrollcommand=scroll.set)
        self.tree_san.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")

        menu = tk.Menu(self, tearoff=0)
        menu.add_command(label="✏️ Editar", command=self._editar_sancion)
        menu.add_command(label="🗑️ Eliminar", command=self._eliminar_sancion)
        menu.add_command(label="📨 Notificar WhatsApp", command=self._wa_sancion)
        self.tree_san.bind("<Button-3>", lambda e: menu.post(e.x_root, e.y_root))

        self._cargar_sanciones()

    def _cargar_sanciones(self):
        for row in self.tree_san.get_children():
            self.tree_san.delete(row)
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT sa.id, s.nombre||' '||s.apellido,
                     sa.tipo, sa.fecha, sa.descripcion, sa.documento
                     FROM sanciones sa
                     LEFT JOIN socios s ON s.id=sa.socio_id""")
        for row in c.fetchall():
            self.tree_san.insert("", "end", values=row)
        conn.close()

    def _form_sancion(self, san_id=None):
        win = tk.Toplevel(self); win.title("Sanción"); win.configure(bg="#1a1a2e"); win.grab_set()
        datos = {}
        if san_id:
            conn = get_conn(); c = conn.cursor()
            c.execute("SELECT * FROM sanciones WHERE id=?", (san_id,))
            row = c.fetchone(); conn.close()
            if row:
                datos = dict(zip(["id","socio_id","tipo","fecha","descripcion","documento"], row))

        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT id, nombre||' '||apellido FROM socios ORDER BY nombre")
        socios = c.fetchall(); conn.close()
        socio_map = {f"{n} (#{i})": i for i,n in socios}

        tk.Label(win, text="Socio", bg="#1a1a2e", fg="white").grid(row=0, column=0, padx=10, pady=4, sticky="w")
        socio_var = tk.StringVar()
        ttk.Combobox(win, textvariable=socio_var, values=list(socio_map.keys()),
                     state="readonly", width=30).grid(row=0, column=1, padx=10, pady=4)
        if datos.get("socio_id"):
            for k, v in socio_map.items():
                if v == datos["socio_id"]:
                    socio_var.set(k); break

        tk.Label(win, text="Tipo", bg="#1a1a2e", fg="white").grid(row=1, column=0, padx=10, pady=4, sticky="w")
        tipo_var = tk.StringVar(value=datos.get("tipo",""))
        ttk.Combobox(win, textvariable=tipo_var,
                     values=["Económica","Disciplinaria","Suspensión","Otro"],
                     width=30).grid(row=1, column=1, padx=10, pady=4)

        tk.Label(win, text="Fecha", bg="#1a1a2e", fg="white").grid(row=2, column=0, padx=10, pady=4, sticky="w")
        fecha_e = tk.Entry(win, width=32)
        fecha_e.insert(0, datos.get("fecha", datetime.now().strftime("%Y-%m-%d")))
        fecha_e.grid(row=2, column=1, padx=10, pady=4)

        tk.Label(win, text="Descripción", bg="#1a1a2e", fg="white").grid(row=3, column=0, padx=10, pady=4, sticky="nw")
        desc_t = tk.Text(win, width=30, height=4, bg="#0f3460", fg="white", insertbackground="white")
        desc_t.insert("1.0", datos.get("descripcion",""))
        desc_t.grid(row=3, column=1, padx=10, pady=4)

        doc_var = tk.StringVar(value=datos.get("documento",""))
        tk.Label(win, text="Documento", bg="#1a1a2e", fg="white").grid(row=4, column=0, padx=10, pady=4, sticky="w")
        tk.Entry(win, textvariable=doc_var, width=25, state="readonly").grid(row=4, column=1, padx=10, pady=4, sticky="w")
        tk.Button(win, text="📎", bg="#0f3460", fg="white",
                  command=lambda: doc_var.set(
                      filedialog.askopenfilename(filetypes=[("Archivos","*.pdf *.jpg *.png *.docx")])
                  )).grid(row=4, column=1, sticky="e", padx=10)

        def guardar():
            sid = socio_map.get(socio_var.get())
            if not sid:
                messagebox.showerror("Error","Seleccione un socio."); return
            doc_dest = copiar_archivo(doc_var.get(), DOCS) if doc_var.get() else datos.get("documento","")
            conn = get_conn(); c = conn.cursor()
            vals = (sid, tipo_var.get(), fecha_e.get(), desc_t.get("1.0","end-1c"), doc_dest)
            if san_id:
                c.execute("UPDATE sanciones SET socio_id=?,tipo=?,fecha=?,descripcion=?,documento=? WHERE id=?",
                          vals+(san_id,))
            else:
                c.execute("INSERT INTO sanciones (socio_id,tipo,fecha,descripcion,documento) VALUES (?,?,?,?,?)", vals)
            conn.commit(); conn.close()
            messagebox.showinfo("OK","Sanción guardada.")
            win.destroy(); self._cargar_sanciones()

        tk.Button(win, text="💾 Guardar", bg="#e94560", fg="white",
                  command=guardar).grid(row=5, column=0, columnspan=2, pady=10)

    def _editar_sancion(self):
        sel = self.tree_san.selection()
        if not sel: return
        self._form_sancion(self.tree_san.item(sel[0])["values"][0])

    def _eliminar_sancion(self):
        sel = self.tree_san.selection()
        if not sel: return
        sid = self.tree_san.item(sel[0])["values"][0]
        if messagebox.askyesno("Confirmar","¿Eliminar sanción?"):
            conn = get_conn(); c = conn.cursor()
            c.execute("DELETE FROM sanciones WHERE id=?", (sid,))
            conn.commit(); conn.close()
            self._cargar_sanciones()

    def _wa_sancion(self):
        sel = self.tree_san.selection()
        if not sel: return
        vals = self.tree_san.item(sel[0])["values"]
        san_id = vals[0]
        conn = get_conn(); c = conn.cursor()
        c.execute("""SELECT s.*, sa.tipo, sa.fecha, sa.descripcion
                     FROM sanciones sa JOIN socios s ON s.id=sa.socio_id
                     WHERE sa.id=?""", (san_id,))
        row = c.fetchone()
        c.execute("SELECT texto FROM plantillas WHERE nombre='Citacion'")
        tpl = c.fetchone(); conn.close()
        if not row: return
        keys = ["id","codigo","nombre","apellido","cedula","telefono","rango","unidad","estado","foto","tipo","fecha","descripcion"]
        sd = dict(zip(keys, row))
        plantilla = tpl[0] if tpl else "Hola {nombre} sancion {tipo}"
        try:
            msg = plantilla.format(**sd)
        except KeyError:
            msg = plantilla
        enviar_whatsapp(str(sd.get("telefono","")), msg)

    # ─── TAB ASISTENCIA ───────────────────────
    def tab_asistencia(self):
        self._clear()
        frame = tk.Frame(self.content, bg="#1a1a2e")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(frame, text="Control de Asistencia", bg="#1a1a2e", fg="#e94560",
                 font=("Arial", 14, "bold")).pack(anchor="w")

        bar = tk.Frame(frame, bg="#1a1a2e"); bar.pack(fill="x", pady=5)
        tk.Label(bar, text="Fecha:", bg="#1a1a2e", fg="white").pack(side="left")
        self.asist_fecha_var = tk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        tk.Entry(bar, textvariable=self.asist_fecha_var, width=12).pack(side="left", padx=5)
        tk.Button(bar, text="📋 Cargar lista", bg="#0f3460", fg="white",
                  command=self._cargar_asistencia).pack(side="left", padx=5)
        tk.Button(bar, text="💾 Guardar asistencia", bg="#e94560", fg="white",
                  command=self._guardar_asistencia).pack(side="right")

        # Tabla
        cols = ("ID","Nombre","Apellido","Rango","Presente","Hora","Observación")
        self.tree_asist = ttk.Treeview(frame, columns=cols, show="headings", height=22)
        for col in cols:
            self.tree_asist.heading(col, text=col)
            self.tree_asist.column(col, width=110, anchor="center")
        scroll = ttk.Scrollbar(frame, orient="vertical", command=self.tree_asist.yview)
        self.tree_asist.configure(yscrollcommand=scroll.set)
        self.tree_asist.pack(side="left", fill="both", expand=True)
        scroll.pack(side="left", fill="y")
        self.tree_asist.bind("<Double-1>", self._toggle_asistencia)
        self._asist_data = {}  # socio_id -> {presente, hora, obs}

        self._cargar_asistencia()

    def _cargar_asistencia(self):
        fecha = self.asist_fecha_var.get()
        for row in self.tree_asist.get_children():
            self.tree_asist.delete(row)
        self._asist_data = {}
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT id,nombre,apellido,rango FROM socios WHERE estado='Activo' ORDER BY apellido")
        socios = c.fetchall()
        # Cargar asistencia existente
        c.execute("SELECT socio_id,presente,hora,observacion FROM asistencia WHERE fecha=?", (fecha,))
        existing = {row[0]: row[1:] for row in c.fetchall()}
        conn.close()

        for sid, nom, ape, rango in socios:
            presente, hora, obs = existing.get(sid, (0, "", ""))
            estado_str = "✅ Sí" if presente else "❌ No"
            self.tree_asist.insert("", "end", iid=str(sid),
                                   values=(sid, nom, ape, rango, estado_str, hora, obs))
            self._asist_data[sid] = {"presente": presente, "hora": hora or "", "obs": obs or ""}

    def _toggle_asistencia(self, event):
        sel = self.tree_asist.selection()
        if not sel: return
        sid = int(sel[0])
        d = self._asist_data[sid]
        d["presente"] = 0 if d["presente"] else 1
        if d["presente"]:
            d["hora"] = datetime.now().strftime("%H:%M")
        vals = self.tree_asist.item(sel[0])["values"]
        self.tree_asist.item(sel[0], values=(
            vals[0], vals[1], vals[2], vals[3],
            "✅ Sí" if d["presente"] else "❌ No",
            d["hora"], d["obs"]
        ))

    def _guardar_asistencia(self):
        fecha = self.asist_fecha_var.get()
        conn = get_conn(); c = conn.cursor()
        c.execute("DELETE FROM asistencia WHERE fecha=?", (fecha,))
        for sid, d in self._asist_data.items():
            c.execute("INSERT INTO asistencia (socio_id,fecha,presente,hora,observacion) VALUES (?,?,?,?,?)",
                      (sid, fecha, d["presente"], d["hora"], d["obs"]))
        conn.commit(); conn.close()
        messagebox.showinfo("OK", f"Asistencia del {fecha} guardada.")

    # ─── TAB MENSAJES / PLANTILLAS ────────────
    def tab_mensajes(self):
        self._clear()
        frame = tk.Frame(self.content, bg="#1a1a2e")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(frame, text="Plantillas de Mensajes", bg="#1a1a2e", fg="#e94560",
                 font=("Arial", 14, "bold")).pack(anchor="w")

        # Lista de plantillas
        list_frame = tk.Frame(frame, bg="#1a1a2e"); list_frame.pack(fill="x", pady=5)
        self.lista_plantillas = tk.Listbox(list_frame, bg="#0f3460", fg="white",
                                           selectbackground="#e94560", width=30, height=8)
        self.lista_plantillas.pack(side="left", padx=(0,10))
        self.lista_plantillas.bind("<<ListboxSelect>>", self._sel_plantilla)

        btn_f = tk.Frame(list_frame, bg="#1a1a2e"); btn_f.pack(side="left", fill="y")
        tk.Button(btn_f, text="➕ Nueva", bg="#0f3460", fg="white",
                  command=self._nueva_plantilla).pack(fill="x", pady=2)
        tk.Button(btn_f, text="🗑️ Eliminar", bg="#e94560", fg="white",
                  command=self._eliminar_plantilla).pack(fill="x", pady=2)

        # Editor
        edit_frame = tk.Frame(frame, bg="#1a1a2e"); edit_frame.pack(fill="both", expand=True)
        tk.Label(edit_frame, text="Nombre:", bg="#1a1a2e", fg="white").grid(row=0, column=0, sticky="w", pady=4)
        self.plantilla_nombre_var = tk.StringVar()
        tk.Entry(edit_frame, textvariable=self.plantilla_nombre_var, width=40
                 ).grid(row=0, column=1, sticky="w", padx=5)

        tk.Label(edit_frame, text="Texto:\n(variables: {nombre} {apellido}\n{cedula} {codigo}\n{rango} {tipo}\n{fecha} {descripcion})",
                 bg="#1a1a2e", fg="#aaa", justify="left"
                 ).grid(row=1, column=0, sticky="nw", pady=4)
        self.plantilla_texto = tk.Text(edit_frame, width=55, height=8,
                                       bg="#0f3460", fg="white", insertbackground="white")
        self.plantilla_texto.grid(row=1, column=1, padx=5, pady=4)

        tk.Button(edit_frame, text="💾 Guardar plantilla", bg="#e94560", fg="white",
                  command=self._guardar_plantilla).grid(row=2, column=1, sticky="e", pady=5)

        tk.Label(frame, text="─── Envío masivo ───", bg="#1a1a2e", fg="#aaa").pack(anchor="w", pady=(10,0))
        mass_frame = tk.Frame(frame, bg="#1a1a2e"); mass_frame.pack(fill="x")
        tk.Button(mass_frame, text="📨 Enviar a todos los socios activos (WhatsApp)",
                  bg="#25D366", fg="white", command=self._envio_masivo
                  ).pack(side="left", padx=5)

        self._cargar_lista_plantillas()

    def _cargar_lista_plantillas(self):
        self.lista_plantillas.delete(0, "end")
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT id,nombre FROM plantillas")
        self._plantilla_ids = []
        for pid, nombre in c.fetchall():
            self.lista_plantillas.insert("end", nombre)
            self._plantilla_ids.append(pid)
        conn.close()

    def _sel_plantilla(self, event=None):
        sel = self.lista_plantillas.curselection()
        if not sel: return
        pid = self._plantilla_ids[sel[0]]
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT nombre,texto FROM plantillas WHERE id=?", (pid,))
        row = c.fetchone(); conn.close()
        if row:
            self.plantilla_nombre_var.set(row[0])
            self.plantilla_texto.delete("1.0","end")
            self.plantilla_texto.insert("1.0", row[1])

    def _nueva_plantilla(self):
        self.plantilla_nombre_var.set("Nueva plantilla")
        self.plantilla_texto.delete("1.0","end")

    def _guardar_plantilla(self):
        nombre = self.plantilla_nombre_var.get()
        texto = self.plantilla_texto.get("1.0","end-1c")
        if not nombre: return
        conn = get_conn(); c = conn.cursor()
        sel = self.lista_plantillas.curselection()
        if sel:
            pid = self._plantilla_ids[sel[0]]
            c.execute("UPDATE plantillas SET nombre=?,texto=? WHERE id=?", (nombre,texto,pid))
        else:
            c.execute("INSERT INTO plantillas (nombre,texto) VALUES (?,?)", (nombre,texto))
        conn.commit(); conn.close()
        self._cargar_lista_plantillas()
        messagebox.showinfo("OK","Plantilla guardada.")

    def _eliminar_plantilla(self):
        sel = self.lista_plantillas.curselection()
        if not sel: return
        pid = self._plantilla_ids[sel[0]]
        if messagebox.askyesno("Confirmar","¿Eliminar plantilla?"):
            conn = get_conn(); c = conn.cursor()
            c.execute("DELETE FROM plantillas WHERE id=?", (pid,))
            conn.commit(); conn.close()
            self._cargar_lista_plantillas()

    def _envio_masivo(self):
        sel = self.lista_plantillas.curselection()
        if not sel:
            messagebox.showwarning("Aviso","Seleccione una plantilla primero."); return
        pid = self._plantilla_ids[sel[0]]
        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT texto FROM plantillas WHERE id=?", (pid,))
        tpl_row = c.fetchone()
        c.execute("SELECT id,codigo,nombre,apellido,cedula,telefono,rango FROM socios WHERE estado='Activo'")
        socios = c.fetchall(); conn.close()
        if not tpl_row: return
        plantilla = tpl_row[0]
        if not messagebox.askyesno("Confirmar",f"¿Enviar a {len(socios)} socios activos?"):
            return
        for s in socios:
            sid,codigo,nombre,apellido,cedula,telefono,rango = s
            try:
                msg = plantilla.format(codigo=codigo,nombre=nombre,apellido=apellido,
                                       cedula=cedula,telefono=telefono,rango=rango,
                                       tipo="",fecha=datetime.now().strftime("%Y-%m-%d"),descripcion="")
            except KeyError:
                msg = plantilla
            enviar_whatsapp(str(telefono), msg)
        messagebox.showinfo("OK",f"Se abrieron {len(socios)} chats de WhatsApp.")

    # ─── TAB REPORTES ─────────────────────────
    def tab_reportes(self):
        self._clear()
        frame = tk.Frame(self.content, bg="#1a1a2e")
        frame.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Label(frame, text="Reportes y Estadísticas", bg="#1a1a2e", fg="#e94560",
                 font=("Arial", 14, "bold")).pack(anchor="w", pady=(0,10))

        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM socios")
        total_socios = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM socios WHERE estado='Activo'")
        activos = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM socios WHERE estado='Inactivo'")
        inactivos = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM socios WHERE estado='Suspendido'")
        suspendidos = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM vehiculos")
        total_veh = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM sanciones")
        total_san = c.fetchone()[0]
        fecha_hoy = datetime.now().strftime("%Y-%m-%d")
        c.execute("SELECT COUNT(*) FROM asistencia WHERE fecha=? AND presente=1", (fecha_hoy,))
        presentes_hoy = c.fetchone()[0]
        conn.close()

        stats = [
            ("👥 Total socios",        total_socios,  "#0f3460"),
            ("✅ Activos",              activos,       "#27ae60"),
            ("❌ Inactivos",            inactivos,     "#7f8c8d"),
            ("🚫 Suspendidos",         suspendidos,   "#e74c3c"),
            ("🚗 Vehículos registrados",total_veh,    "#2980b9"),
            ("⚠️ Sanciones totales",   total_san,     "#e67e22"),
            ("📋 Presentes hoy",       presentes_hoy, "#16a085"),
        ]

        cards = tk.Frame(frame, bg="#1a1a2e"); cards.pack(fill="x")
        for i, (label, valor, color) in enumerate(stats):
            card = tk.Frame(cards, bg=color, padx=15, pady=10)
            card.grid(row=i//4, column=i%4, padx=8, pady=8, sticky="nsew")
            tk.Label(card, text=str(valor), bg=color, fg="white",
                     font=("Arial", 22, "bold")).pack()
            tk.Label(card, text=label, bg=color, fg="white",
                     font=("Arial", 9)).pack()

        # Socios por rango
        tk.Label(frame, text="Socios por Rango", bg="#1a1a2e", fg="white",
                 font=("Arial", 11, "bold")).pack(anchor="w", pady=(20,5))
        cols = ("Rango","Cantidad")
        tree_r = ttk.Treeview(frame, columns=cols, show="headings", height=6)
        for col in cols:
            tree_r.heading(col, text=col)
            tree_r.column(col, width=200, anchor="center")
        tree_r.pack(fill="x")

        conn = get_conn(); c = conn.cursor()
        c.execute("SELECT rango, COUNT(*) FROM socios GROUP BY rango ORDER BY COUNT(*) DESC")
        for row in c.fetchall():
            tree_r.insert("", "end", values=row)
        conn.close()

        tk.Button(frame, text="🔄 Actualizar", bg="#0f3460", fg="white",
                  command=self.tab_reportes).pack(pady=10)


# ─────────────────────────────────────────────
# ENTRY POINT
# ─────────────────────────────────────────────
if __name__ == "__main__":
    app = App()
    app.mainloop()
