import sqlite3, os, hashlib, json, threading
from datetime import datetime
import requests

from kivy.lang import Builder
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivymd.uix.menu import MDDropdownMenu
from kivy.metrics import dp

SERVER_URL = "https://proyecto-borrador.onrender.com"
DB_NAME = "aguarico_v6.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios (id INTEGER PRIMARY KEY, username TEXT UNIQUE, password TEXT, nombre TEXT, rol TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS socios (id INTEGER PRIMARY KEY, nombre TEXT, cedula TEXT, telefono TEXT, estado TEXT DEFAULT 'activo')""")
    c.execute("""CREATE TABLE IF NOT EXISTS asistencias (id INTEGER PRIMARY KEY, codigo TEXT, socio_id INTEGER, nombre TEXT, fecha TEXT, entrada TEXT, salida TEXT, estado TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS vehiculos (id INTEGER PRIMARY KEY, placa TEXT, socio TEXT)""")
    # usuario staly minuscula
    pwd_hash = hashlib.sha256("1234".encode()).hexdigest()
    c.execute("INSERT OR IGNORE INTO usuarios (username,password,nombre,rol) VALUES (?,?,?,?)", ("staly", pwd_hash, "Staly Aguarico", "Administrador"))
    c.execute("SELECT COUNT(*) FROM socios")
    if c.fetchone()[0]==0:
        for n in [("Juan Perez","0102030405"),("Maria Lopez","0102030406"),("Carlos Aguarico","0102030407")]:
            c.execute("INSERT INTO socios (nombre,cedula) VALUES (?,?)", n)
    conn.commit()
    conn.close()

KV = '''
MDScreen:
    MDBoxLayout:
        orientation: "vertical"
        md_bg_color: 0.05, 0.1, 0.21, 1

        MDBoxLayout:
            size_hint_y: None
            height: dp(50)
            md_bg_color: 0.12, 0.56, 1, 1
            padding: dp(10)
            MDLabel:
                text: "SISTEMA AGRUPACION AGUARICO v6"
                bold: True
            MDLabel:
                id: api_status
                text: "API: Render"
                font_size: "10sp"
                halign: "right"

        MDBottomNavigation:
            id: nav
            panel_color: 0.06, 0.13, 0.24, 1

            MDBottomNavigationItem:
                name: "inicio"
                text: "Inicio"
                icon: "home"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: dp(15)
                    spacing: dp(10)
                    MDLabel:
                        text: "Bienvenido, Staly Aguarico"
                        halign: "center"
                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(100)
                        spacing: dp(10)
                        MDCard:
                            md_bg_color: 0.12, 0.56, 1, 1
                            padding: dp(10)
                            MDLabel:
                                id: card_total
                                text: "0\\nTotal Socios"
                                halign: "center"
                        MDCard:
                            md_bg_color: 0.29, 0.68, 0.31, 1
                            MDLabel:
                                id: card_activos
                                text: "0\\nActivos"
                                halign: "center"
                        MDCard:
                            md_bg_color: 1, 0.6, 0, 1
                            MDLabel:
                                id: card_hoy
                                text: "0\\nHoy"
                                halign: "center"
                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(50)
                        spacing: dp(10)
                        MDRaisedButton:
                            text: "Verificar API"
                            on_release: app.verificar_api()
                        MDRaisedButton:
                            text: "Actualizar"
                            on_release: app.cargar_dashboard()

            MDBottomNavigationItem:
                name: "asistencia"
                text: "Asistencia"
                icon: "account-check"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: dp(10)
                    spacing: dp(8)
                    MDLabel:
                        text: "CONTROL DE ASISTENCIA"
                        bold: True
                        size_hint_y: None
                        height: dp(30)
                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(48)
                        spacing: dp(8)
                        MDLabel:
                            text: "Socio:"
                            size_hint_x: None
                            width: dp(50)
                        MDRaisedButton:
                            id: btn_socio
                            text: "Seleccionar Socio"
                            on_release: app.open_socio_menu()
                    MDLabel:
                        id: lbl_cedula
                        text: "Cedula: ---"
                        size_hint_y: None
                        height: dp(25)
                    MDBoxLayout:
                        size_hint_y: None
                        height: dp(45)
                        spacing: dp(8)
                        MDTextField:
                            id: obs_field
                            hint_text: "Observacion"
                        MDRaisedButton:
                            text: "ENTRADA"
                            md_bg_color: 0.18, 0.49, 0.19, 1
                            on_release: app.registrar("entrada")
                        MDRaisedButton:
                            text: "SALIDA"
                            md_bg_color: 0.93, 0.42, 0, 1
                            on_release: app.registrar("salida")
                    ScrollView:
                        MDList:
                            id: lista_hoy

            MDBottomNavigationItem:
                name: "login"
                text: "Login"
                icon: "login"
                MDBoxLayout:
                    orientation: "vertical"
                    padding: dp(40)
                    spacing: dp(15)
                    MDLabel:
                        text: "AGRUPACION AGUARICO\\nLogin v6"
                        halign: "center"
                        font_size: "22sp"
                        bold: True
                    MDTextField:
                        id: user_field
                        hint_text: "Usuario"
                        text: "staly"
                    MDTextField:
                        id: pass_field
                        hint_text: "Contraseña"
                        password: True
                        text: "1234"
                    MDRaisedButton:
                        text: "INGRESAR con staly / 1234"
                        pos_hint: {"center_x": .5}
                        on_release: app.do_login()
                    MDLabel:
                        id: login_msg
                        text: ""
                        halign: "center"
                        font_size: "12sp"
'''

class AppAguarico(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.token = ""
        self.socios = []
        self.selected_socio = None
        self.menu = None

    def build(self):
        init_db()
        self.theme_cls.primary_palette = "Blue"
        return Builder.load_string(KV)

    def on_start(self):
        self.cargar_socios_local()
        self.verificar_api()

    def do_login(self):
        user = self.root.ids.user_field.text.strip()
        pwd = self.root.ids.pass_field.text.strip()
        self.root.ids.login_msg.text = f"Validando {user}..."
        # 1. Local check staly minuscula
        if user == "staly" and pwd == "1234":
            self.root.ids.login_msg.text = "Login local OK - Conectando a Render..."
            self.root.ids.nav.switch_tab("inicio")
            threading.Thread(target=self.login_render, args=(user,pwd), daemon=True).start()
            return
        # 2. hash check
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        h = hashlib.sha256(pwd.encode()).hexdigest()
        c.execute("SELECT * FROM usuarios WHERE username=? AND password=?", (user,h))
        if c.fetchone():
            self.root.ids.nav.switch_tab("inicio")
        else:
            self.root.ids.login_msg.text = "Usuario o clave incorrecta. Usa staly / 1234"
        conn.close()

    def login_render(self, u, p):
        try:
            try: requests.get(SERVER_URL+"/", timeout=15)
            except: pass
            r = requests.post(f"{SERVER_URL}/login", data={"username":u,"password":p}, timeout=60)
            if r.status_code==200:
                j = r.json()
                self.token = j.get("access_token","")
                self.root.ids.api_status.text = "API Conectada"
        except Exception as e:
            self.root.ids.api_status.text = f"Offline: {e}"

    def cargar_socios_local(self):
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute("SELECT id,nombre,cedula FROM socios")
        self.socios = [{"id":r[0],"nombre":r[1],"cedula":r[2]} for r in c.fetchall()]
        conn.close()
        if self.socios:
            self.selected_socio = self.socios[0]
            self.root.ids.btn_socio.text = f"{self.selected_socio['id']} - {self.selected_socio['nombre']}"
            self.root.ids.lbl_cedula.text = f"Cedula: {self.selected_socio['cedula']}"

    def open_socio_menu(self):
        items = [{"text": f"{s['id']} - {s['nombre']}", "viewclass": "OneLineListItem", "on_release": lambda x=s: self.select_socio(x)} for s in self.socios]
        self.menu = MDDropdownMenu(caller=self.root.ids.btn_socio, items=items, width_mult=4)
        self.menu.open()

    def select_socio(self, s):
        self.selected_socio = s
        self.root.ids.btn_socio.text = f"{s['id']} - {s['nombre']}"
        self.root.ids.lbl_cedula.text = f"Cedula: {s['cedula']}"
        if self.menu: self.menu.dismiss()

    def verificar_api(self):
        self.root.ids.api_status.text = "Conectando... 50s"
        threading.Thread(target=self._verificar, daemon=True).start()

    def _verificar(self):
        try:
            r = requests.get(f"{SERVER_URL}/socios", headers={"Authorization":f"Bearer {self.token}"} if self.token else {}, timeout=60)
            if r.status_code==200:
                self.root.ids.api_status.text = "API Conectada a Render"
                self.cargar_dashboard()
            else:
                self.root.ids.api_status.text = f"API {r.status_code}"
        except Exception as e:
            self.root.ids.api_status.text = f"Render dormido, reintenta"

    def cargar_dashboard(self):
        def run():
            try:
                headers = {"Authorization":f"Bearer {self.token}"} if self.token else {}
                r = requests.get(f"{SERVER_URL}/socios", headers=headers, timeout=60)
                if r.status_code==200:
                    data = r.json()
                    arr = data if isinstance(data,list) else data.get("socios",[]) or data.get("data",[])
                    self.root.ids.card_total.text = f"{len(arr)}\nTotal Socios"
                    act = len([x for x in arr if str(x.get("estado","activo")).lower()=="activo"])
                    self.root.ids.card_activos.text = f"{act}\nActivos"
            except: pass
            try:
                r = requests.get(f"{SERVER_URL}/asistencia/hoy", headers=headers, timeout=60)
                if r.status_code==200:
                    j = r.json()
                    total = j.get("total",0) if isinstance(j,dict) else len(j)
                    self.root.ids.card_hoy.text = f"{total}\nHoy"
            except: pass
        threading.Thread(target=run, daemon=True).start()

    def registrar(self, tipo):
        if not self.selected_socio:
            return
        obs = self.root.ids.obs_field.text
        payload = {"socio_id": self.selected_socio["id"], "tipo": tipo, "observacion": obs}
        def run():
            try:
                headers = {"Authorization":f"Bearer {self.token}"} if self.token else {}
                for url in [f"{SERVER_URL}/asistencia", f"{SERVER_URL}/asistencia/registrar"]:
                    try:
                        r = requests.post(url, json=payload, headers=headers, timeout=30)
                        if r.status_code in [200,201]:
                            # guardar local
                            conn = sqlite3.connect(DB_NAME)
                            c = conn.cursor()
                            c.execute("INSERT INTO asistencias (socio_id,nombre,fecha,entrada,estado) VALUES (?,?,?,?,?)",
                                (self.selected_socio["id"], self.selected_socio["nombre"], datetime.now().strftime("%Y-%m-%d"), datetime.now().strftime("%H:%M"), tipo))
                            conn.commit()
                            conn.close()
                            self.root.ids.login_msg.text = f"{tipo.upper()} OK"
                            return
                    except: continue
            except Exception as e:
                self.root.ids.login_msg.text = str(e)
        threading.Thread(target=run, daemon=True).start()

if __name__ == "__main__":
    AppAguarico().run()