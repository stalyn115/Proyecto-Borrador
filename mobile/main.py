import os, json, requests, flet as ft
SERVER_URL="https://proyecto-borrador.onrender.com"
PRIMARY="#2E7D32"; ACCENT="#4CAF50"; BG="#121212"; SURFACE="#1E1E1E"; SURFACE2="#262626"; WHITE="#FFFFFF"; MUTED="#B0BEC5"; DANGER="#D32F2F"

class Store:
    def __init__(self):
        self.f=os.path.join(os.path.dirname(os.path.abspath(__file__)), ".client_storage.json")
    def set(self,k,v):
        try:
            d={}; 
            if os.path.isfile(self.f): d=json.load(open(self.f,"r",encoding="utf-8"))
            d[k]=v; json.dump(d, open(self.f,"w",encoding="utf-8"))
        except: pass
    def get(self,k):
        try:
            if os.path.isfile(self.f): return json.load(open(self.f,"r",encoding="utf-8")).get(k)
        except: pass
        return None

def main(page: ft.Page):
    page.title="Aguarico v6"; page.bgcolor=BG; page.theme_mode=ft.ThemeMode.DARK
    page.padding=0
    store=Store()
    holder={"token": store.get("token"), "user": store.get("user"), "info": store.get("user_info")}

    def login_page():
        page.controls.clear()
        txt_user=ft.TextField(label="Usuario", prefix_icon=ft.Icons.PERSON, bgcolor=SURFACE, color=WHITE, border_color=PRIMARY, width=300, value=holder["user"] or "staly")
        txt_pass=ft.TextField(label="Contrasena", prefix_icon=ft.Icons.LOCK, password=True, can_reveal_password=True, bgcolor=SURFACE, color=WHITE, border_color=PRIMARY, width=300)
        status=ft.Text("Conectado a Render", color=MUTED, size=10)
        def do_login(e):
            u=txt_user.value.strip(); p=txt_pass.value
            status.value="Conectando..."; page.update()
            try:
                r=requests.post(f"{SERVER_URL}/login", data={"username": u, "password": p}, timeout=20)
                if r.status_code==200:
                    j=r.json(); token=j.get("access_token",""); usuario=j.get("usuario",{})
                    holder["token"]=token; holder["user"]=u; holder["info"]=usuario
                    store.set("token", token); store.set("user", u); store.set("user_info", usuario)
                    dashboard_page(); return
                status.value=f"Error {r.status_code}: {r.text[:200]}"
            except Exception as ex:
                status.value=str(ex)
            page.update()
        page.add(ft.Container(content=ft.Column([ft.Icon(ft.Icons.WATER_DROP, color=ACCENT, size=70), ft.Text("AGRUPACION AGUARICO", color=WHITE, size=22, weight=ft.FontWeight.BOLD), txt_user, txt_pass, ft.ElevatedButton(text="ENTRAR", icon=ft.Icons.LOGIN, on_click=do_login, bgcolor=PRIMARY, color=WHITE, width=300, height=48), status], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=12), padding=30, expand=True, alignment=ft.alignment.center))
        page.update()

    def dashboard_page():
        page.controls.clear()
        info=holder.get("info") or {}; nombre=info.get("nombre") or holder["user"] or "Staly"; rol=info.get("rol") or "Administrador"
        token=holder["token"]; headers={"Authorization": f"Bearer {token}"} if token else {}
        lista=ft.ListView(expand=True, spacing=8, padding=10)
        title_status=ft.Text(f"{nombre} - {rol} | Socios: cargando...", color=ACCENT, size=11, weight=ft.FontWeight.BOLD)
        socios_cache=[]

        def snack(msg, err=False):
            page.snack_bar=ft.SnackBar(content=ft.Text(msg), bgcolor=DANGER if err else PRIMARY, open=True); page.update()

        def load_socios(e=None):
            lista.controls.clear(); lista.controls.append(ft.ProgressRing(color=ACCENT)); page.update()
            try:
                r=requests.get(f"{SERVER_URL}/socios", headers=headers, timeout=15)
                print(f"GET /socios {r.status_code} {r.text[:2000]}")
                lista.controls.clear()
                if r.status_code==200:
                    data=r.json()
                    socios=data if isinstance(data, list) else data.get("socios", []) or data.get("data", []) or []
                    nonlocal_list=globals().get("socios_cache", [])
                    socios_cache.clear(); socios_cache.extend(socios)
                    title_status.value=f"{nombre} - {rol} | Socios: {len(socios)}"
                    if not socios:
                        lista.controls.append(ft.Container(content=ft.Column([ft.Icon(ft.Icons.PEOPLE_OUTLINE, size=50, color=MUTED), ft.Text("No hay socios. Dale a + Nuevo Socio", color=WHITE)], horizontal_alignment=ft.CrossAxisAlignment.CENTER), padding=20, alignment=ft.alignment.center))
                    for s in socios:
                        nom=s.get("nombre") or s.get("nombres") or f"ID {s.get('id')}"
                        ced=s.get("cedula") or ""; tel=s.get("telefono") or ""; id_s=s.get("id")
                        lista.controls.append(ft.Container(content=ft.Row([ft.CircleAvatar(content=ft.Text(str(nom)[0].upper(), color=WHITE), bgcolor=PRIMARY), ft.Column([ft.Text(nom, color=WHITE, weight=ft.FontWeight.BOLD, size=14), ft.Text(f"CI: {ced} | Tel: {tel} | ID: {id_s}", color=MUTED, size=10)], expand=True), ft.IconButton(icon=ft.Icons.CHECK_CIRCLE, icon_color=ACCENT, on_click=lambda e, sid=id_s: registrar_asistencia_directa(sid))]), bgcolor=SURFACE2, padding=12, border_radius=12))
                else:
                    lista.controls.append(ft.Text(f"Error {r.status_code}: {r.text[:400]}", color=DANGER))
            except Exception as ex:
                lista.controls.append(ft.Text(str(ex), color=DANGER))
            page.update()

        def registrar_asistencia_directa(socio_id):
            try:
                payload={"socio_id": socio_id, "fecha": "2025-10-28", "estado": "presente"}
                r=requests.post(f"{SERVER_URL}/asistencia", json=payload, headers=headers, timeout=15)
                if r.status_code==404:
                    r=requests.post(f"{SERVER_URL}/asistencia/registrar", json=payload, headers=headers, timeout=15)
                print(f"POST asistencia {r.status_code} {r.text[:500]}")
                if r.status_code in [200,201]:
                    snack(f"Asistencia registrada socio {socio_id} OK")
                else:
                    snack(f"Error asistencia: {r.text[:150]}", err=True)
            except Exception as ex:
                snack(str(ex), err=True)

        # DIALOGO NUEVO SOCIO
        def open_nuevo_socio(e):
            tf_nombre=ft.TextField(label="Nombres completos", bgcolor=SURFACE, color=WHITE, border_color=PRIMARY)
            tf_cedula=ft.TextField(label="Cedula", bgcolor=SURFACE, color=WHITE, border_color=PRIMARY)
            tf_tel=ft.TextField(label="Telefono", bgcolor=SURFACE, color=WHITE, border_color=PRIMARY)
            tf_dir=ft.TextField(label="Direccion", bgcolor=SURFACE, color=WHITE, border_color=PRIMARY)
            def guardar(e):
                if not tf_nombre.value: snack("Pon nombre", err=True); return
                payload={
                    "nombre": tf_nombre.value.strip(),
                    "nombres": tf_nombre.value.strip(),
                    "cedula": tf_cedula.value.strip(),
                    "telefono": tf_tel.value.strip(),
                    "direccion": tf_dir.value.strip(),
                    "estado": "activo"
                }
                print(f"POST /socios {payload}")
                try:
                    r=requests.post(f"{SERVER_URL}/socios", json=payload, headers=headers, timeout=15)
                    if r.status_code==404:
                        r=requests.post(f"{SERVER_URL}/socios/", json=payload, headers=headers, timeout=15)
                    print(f"Respuesta {r.status_code} {r.text[:1000]}")
                    if r.status_code in [200,201]:
                        snack(f"Socio {tf_nombre.value} creado!"); page.dialog.open=False; page.update(); load_socios()
                    else:
                        snack(f"Error {r.status_code}: {r.text[:250]}", err=True)
                except Exception as ex:
                    snack(str(ex), err=True)

            dlg=ft.AlertDialog(title=ft.Text("Nuevo Socio"), content=ft.Column([tf_nombre, tf_cedula, tf_tel, tf_dir], tight=True, spacing=10), actions=[ft.TextButton("Cancelar", on_click=lambda e: setattr(page.dialog, 'open', False) or page.update()), ft.ElevatedButton("Guardar", bgcolor=PRIMARY, color=WHITE, on_click=guardar)])
            page.dialog=dlg; dlg.open=True; page.update()

        # DIALOGO REGISTRAR ASISTENCIA MANUAL
        def open_asistencia_manual(e):
            tf_id=ft.TextField(label="ID Socio", bgcolor=SURFACE, color=WHITE, border_color=PRIMARY, hint_text="Ej: 1")
            dd_estado=ft.Dropdown(label="Estado", options=[ft.dropdown.Option("presente"), ft.dropdown.Option("ausente"), ft.dropdown.Option("justificado")], value="presente", bgcolor=SURFACE, color=WHITE, border_color=PRIMARY)
            def guardar_asist(e):
                if not tf_id.value: snack("Pon ID", err=True); return
                try:
                    sid=int(tf_id.value)
                    payload={"socio_id": sid, "estado": dd_estado.value}
                    r=requests.post(f"{SERVER_URL}/asistencia", json=payload, headers=headers, timeout=15)
                    if r.status_code==404:
                        r=requests.post(f"{SERVER_URL}/asistencia/registrar", json=payload, headers=headers, timeout=15)
                    if r.status_code==404:
                        r=requests.post(f"{SERVER_URL}/asistencia/qr", json={"codigo": str(sid)}, headers=headers, timeout=15)
                    print(f"Asistencia manual {r.status_code} {r.text[:1000]}")
                    if r.status_code in [200,201]:
                        snack(f"Asistencia {dd_estado.value} para ID {sid}"); page.dialog.open=False; page.update()
                    else:
                        snack(f"Error: {r.text[:200]}", err=True)
                except Exception as ex:
                    snack(str(ex), err=True)
            dlg=ft.AlertDialog(title=ft.Text("Registrar Asistencia"), content=ft.Column([tf_id, dd_estado, ft.Text("Tip: Si no sabes el ID, primero dale a Socios y mira el ID", color=MUTED, size=10)], tight=True), actions=[ft.TextButton("Cancelar", on_click=lambda e: setattr(page.dialog, 'open', False) or page.update()), ft.ElevatedButton("Registrar", bgcolor=PRIMARY, color=WHITE, on_click=guardar_asist)])
            page.dialog=dlg; dlg.open=True; page.update()

        def load_hoy(e):
            lista.controls.clear(); lista.controls.append(ft.ProgressRing(color=ACCENT)); page.update()
            try:
                r=requests.get(f"{SERVER_URL}/asistencia/hoy", headers=headers, timeout=15)
                print(r.text[:2000])
                lista.controls.clear()
                j=r.json()
                lista.controls.append(ft.Text(f"Asistencia {j.get('fecha','')} - Total: {j.get('total',0)}", color=WHITE, weight=ft.FontWeight.BOLD))
                regs=j.get("registros", []) or []
                if not regs:
                    lista.controls.append(ft.Text("Aun no hay asistencias hoy", color=MUTED))
                for reg in regs:
                    lista.controls.append(ft.Container(content=ft.Text(str(reg), color=WHITE, size=11), bgcolor=SURFACE2, padding=8, border_radius=8))
            except Exception as ex:
                lista.controls.append(ft.Text(str(ex), color=DANGER))
            page.update()

        top=ft.Container(content=ft.Column([
            ft.Row([ft.Icon(ft.Icons.CHECK_CIRCLE, color=ACCENT, size=26), ft.Column([ft.Text(f"Hola {nombre}!", color=WHITE, size=16, weight=ft.FontWeight.BOLD), title_status], spacing=0)], alignment=ft.MainAxisAlignment.START),
            ft.Row([ft.ElevatedButton(text="Socios", icon=ft.Icons.PEOPLE, on_click=load_socios, bgcolor=PRIMARY, color=WHITE, width=90, height=36), ft.ElevatedButton(text="Hoy", icon=ft.Icons.TODAY, on_click=load_hoy, bgcolor=SURFACE2, color=WHITE, width=80, height=36), ft.ElevatedButton(text="+ Socio", icon=ft.Icons.PERSON_ADD, on_click=open_nuevo_socio, bgcolor=ACCENT, color=WHITE, width=95, height=36)], alignment=ft.MainAxisAlignment.CENTER),
            ft.Row([ft.ElevatedButton(text="+ Asistencia", icon=ft.Icons.ADD_TASK, on_click=open_asistencia_manual, bgcolor=SURFACE2, color=ACCENT, width=200, height=36), ft.IconButton(icon=ft.Icons.LOGOUT, icon_color=MUTED, on_click=lambda _: login_page())], alignment=ft.MainAxisAlignment.CENTER)
        ], spacing=8), bgcolor=SURFACE, padding=12, border_radius=ft.border_radius.only(bottom_left=16, bottom_right=16))

        page.add(ft.Column([top, lista], expand=True))
        page.update()
        load_socios()

    login_page()

if __name__=="__main__":
    ft.app(target=main)
