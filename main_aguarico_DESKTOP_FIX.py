import tkinter as tk
from tkinter import messagebox
import requests, json, time

SERVER_URL = "https://proyecto-borrador.onrender.com"

class LoginApp:
    def __init__(self, root):
        self.root = root
        root.title("AGRUPACION AGUARICO - Login")
        root.geometry("400x380")
        root.configure(bg="#1a2a4a")
        tk.Label(root, text="AGRUPACION AGUARICO", font=("Arial", 18, "bold"), bg="#1a2a4a", fg="white").pack(pady=(30,5))
        tk.Label(root, text="Sistema v6", bg="#1a2a4a", fg="#a0b0d0").pack()
        frm = tk.Frame(root, bg="#1a2a4a")
        frm.pack(pady=20)
        tk.Label(frm, text="Usuario:", bg="#1a2a4a", fg="white").grid(row=0, column=0, padx=10, pady=10)
        self.entry_user = tk.Entry(frm, width=22, font=("Arial", 12))
        self.entry_user.grid(row=0, column=1)
        self.entry_user.insert(0, "staly")
        tk.Label(frm, text="Contrasena:", bg="#1a2a4a", fg="white").grid(row=1, column=0, padx=10, pady=10)
        self.entry_pass = tk.Entry(frm, width=22, font=("Arial", 12), show="*")
        self.entry_pass.grid(row=1, column=1)
        self.lbl_error = tk.Label(root, text="", bg="#1a2a4a", fg="white", font=("Arial", 10), wraplength=350, justify="center")
        self.lbl_error.pack(pady=5)
        tk.Button(root, text="INGRESAR", command=self.login, bg="#1976D2", fg="white", font=("Arial", 12, "bold"), width=15).pack(pady=10)
        tk.Label(root, text=f"{SERVER_URL}", bg="#1a2a4a", fg="#6a8ab0", font=("Arial", 8)).pack(side=tk.BOTTOM, pady=10)

    def login(self):
        user = self.entry_user.get().strip()
        pwd = self.entry_pass.get().strip()
        if not user or not pwd:
            self.lbl_error.config(text="Ingresa usuario y clave", fg="red")
            return
        for intento in range(1,4):
            try:
                self.lbl_error.config(text=f"Despertando Render... intento {intento}/3 (puede tardar 50s)", fg="yellow")
                self.root.update()
                # Primero ping para despertar
                try:
                    requests.get(f"{SERVER_URL}/", timeout=30)
                except:
                    pass
                time.sleep(2)
                r = requests.post(f"{SERVER_URL}/login", data={"username": user, "password": pwd}, timeout=90)
                print(f"LOGIN {r.status_code} {r.text[:500]}")
                if r.status_code == 200:
                    data = r.json()
                    usuario = data.get("usuario", {})
                    nombre = usuario.get("nombre", user)
                    self.lbl_error.config(text=f"Bienvenido {nombre}!", fg="#4CAF50")
                    messagebox.showinfo("OK", f"Bienvenido {nombre}\nRol: {usuario.get('rol')}")
                    self.root.destroy()
                    self.mostrar_dashboard(usuario, data.get("access_token",""))
                    return
                else:
                    self.lbl_error.config(text=f"Error {r.status_code}: {r.text[:150]}", fg="red")
                    return
            except requests.exceptions.ReadTimeout:
                self.lbl_error.config(text=f"Render se esta despertando... reintentando {intento}/3", fg="orange")
                self.root.update()
                time.sleep(5)
                continue
            except Exception as ex:
                self.lbl_error.config(text=f"Intento {intento} fallo: {ex}\nReintentando...", fg="red")
                self.root.update()
                time.sleep(3)
                continue
        self.lbl_error.config(text="No se pudo conectar. Dale de nuevo a INGRESAR en 30s. Render es lento en gratis.", fg="red")

    def mostrar_dashboard(self, usuario, token):
        import tkinter as tk
        from tkinter import messagebox
        dash = tk.Tk()
        dash.title(f"Aguarico v6 - {usuario.get('nombre','')}")
        dash.geometry("850x650")
        dash.configure(bg="#121212")
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        tk.Label(dash, text=f"Hola {usuario.get('nombre','')} - {usuario.get('rol','')}", bg="#1E1E1E", fg="white", font=("Arial", 14, "bold")).pack(fill=tk.X, padx=10, pady=10)
        btns = tk.Frame(dash, bg="#121212"); btns.pack(fill=tk.X, padx=10)
        txt = tk.Text(dash, bg="#1E1E1E", fg="white"); txt.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        def cargar_socios():
            txt.delete("1.0", tk.END); txt.insert(tk.END, "Cargando socios...\n")
            dash.update()
            try:
                r = requests.get(f"{SERVER_URL}/socios", headers=headers, timeout=60)
                txt.insert(tk.END, f"Status {r.status_code}\n{r.text[:8000]}\n")
            except Exception as e:
                txt.insert(tk.END, f"Error: {e}")
        def cargar_hoy():
            txt.delete("1.0", tk.END)
            try:
                r = requests.get(f"{SERVER_URL}/asistencia/hoy", headers=headers, timeout=60)
                txt.insert(tk.END, r.text[:8000])
            except Exception as e:
                txt.insert(tk.END, str(e))
        def nuevo_socio():
            win = tk.Toplevel(dash); win.title("Nuevo Socio"); win.geometry("350x350"); win.configure(bg="#1E1E1E")
            tk.Label(win, text="Nombre", bg="#1E1E1E", fg="white").pack(); e1=tk.Entry(win, width=30); e1.pack()
            tk.Label(win, text="Cedula", bg="#1E1E1E", fg="white").pack(); e2=tk.Entry(win, width=30); e2.pack()
            tk.Label(win, text="Telefono", bg="#1E1E1E", fg="white").pack(); e3=tk.Entry(win, width=30); e3.pack()
            def guardar():
                payload={"nombre": e1.get(), "nombres": e1.get(), "cedula": e2.get(), "telefono": e3.get(), "direccion": "", "estado": "activo"}
                try:
                    r=requests.post(f"{SERVER_URL}/socios", json=payload, headers=headers, timeout=60)
                    messagebox.showinfo("OK", f"{r.status_code}: {r.text[:300]}")
                    win.destroy(); cargar_socios()
                except Exception as ex:
                    messagebox.showerror("Error", str(ex))
            tk.Button(win, text="Guardar", command=guardar, bg="#2E7D32", fg="white").pack(pady=15)
        tk.Button(btns, text="Ver Socios", command=cargar_socios, bg="#2E7D32", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="Hoy", command=cargar_hoy, bg="#424242", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btns, text="+ Nuevo Socio", command=nuevo_socio, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        dash.mainloop()

if __name__ == "__main__":
    root = tk.Tk()
    app = LoginApp(root)
    root.mainloop()
