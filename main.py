import os
import json
import threading
import requests
from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.popup import Popup
from kivy.clock import Clock
from kivy.core.window import Window

API_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
MEMORIA_FILE = "waifu_memoria.json"
CONFIG_FILE = "config.json"
LORE_FILE = "cyberpunk_lore.json"
WORLDS_FILE = "worlds.json"
OBJETOS_FILE = "objetos_usuario.json"

MODELOS_SUGERIDOS = [
    "gpt-oss-20b",
    "gemma-4-31b-it",
    "nvidia/nemotron-3-ultra-550b-a55b",
    "meta/llama-3.1-8b-instruct",
    "meta/llama-3.1-70b-instruct",
]


class WaifuApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.mundo = {
            "nombre": "Narrador de Night City",
            "personalidad": "neutral, descriptivo, inmersivo, cyberpunk",
            "historia": "Eres el narrador del mundo de Cyberpunk 2077 y Cyberpunk: Edgerunners. Describes Night City, sus distritos, corporaciones, pandillas, tecnología y los NPCs que el usuario encuentra. Los personajes como Lucy, David Martinez, Johnny Silverhand, Rogue, etc. aparecen como parte del mundo, no como el interlocutor directo.",
            "saludo": "Bienvenido a Night City, año 2077. Las megacorporaciones mandan, las pandillas controlan las calles y el cromo puede salvarte o destruirte. ¿Qué haces aquí?",
        }
        self.hechos = []
        self.historial = []
        self.config = {}
        self.api_key = ""
        self.lore = {}
        self.max_tokens_contexto = 4000
        self.trasfondo_protagonista = ""
        self.objetos = []
        self.worlds = [
            {
                "nombre": "Narrador de Night City",
                "personalidad": "neutral, descriptivo, inmersivo, cyberpunk",
                "historia": "Eres el narrador del mundo de Cyberpunk 2077 y Cyberpunk: Edgerunners. Describes Night City, sus distritos, corporaciones, pandillas, tecnología y los NPCs que el usuario encuentra. Los personajes como Lucy, David Martinez, Johnny Silverhand, Rogue, etc. aparecen como parte del mundo, no como el interlocutor directo.",
                "saludo": "Bienvenido a Night City, año 2077. Las megacorporaciones mandan, las pandillas controlan las calles y el cromo puede salvarte o destruirte. ¿Qué haces aquí?",
            }
        ]
        self.mundo_activo_nombre = self.worlds[0]["nombre"]
        self.mundo = dict(self.worlds[0])

    def build(self):
        self.config = self._cargar_config()
        self.api_key = self.config.get("api_key", "")
        self._cargar_memoria()
        self._cargar_worlds()
        self._cargar_objetos()
        self._cargar_lore()

        sm = ScreenManager()
        chat = ChatScreen(name="chat")
        customize = CustomizeScreen(name="customize")
        chatbots = ChatbotsScreen(name="chatbots")
        chat.app_ref = self
        customize.app_ref = self
        chatbots.app_ref = self

        sm.add_widget(chat)
        sm.add_widget(customize)
        sm.add_widget(chatbots)
        return sm

    # ---------- Persistencia ----------
    def _cargar_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _guardar_config(self):
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, ensure_ascii=False, indent=2)

    def _cargar_worlds(self):
        if os.path.exists(WORLDS_FILE):
            try:
                with open(WORLDS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.worlds = data.get("worlds", self.worlds)
                self.mundo_activo_nombre = data.get("mundo_activo_nombre", self.worlds[0]["nombre"])
                for w in self.worlds:
                    if w["nombre"] == self.mundo_activo_nombre:
                        self.mundo = dict(w)
                        break
            except Exception:
                pass

    def _guardar_worlds(self):
        data = {
            "worlds": self.worlds,
            "mundo_activo_nombre": self.mundo_activo_nombre,
        }
        with open(WORLDS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _cargar_objetos(self):
        if os.path.exists(OBJETOS_FILE):
            try:
                with open(OBJETOS_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.objetos = data.get("objetos", [])
                self.cyberware = data.get("cyberware", [])
                self.armas = data.get("armas", [])
                self.dinero = data.get("dinero", 0)
                self.notas_objetos = data.get("notas", [])
            except Exception:
                self.objetos = []
                self.cyberware = []
                self.armas = []
                self.dinero = 0
                self.notas_objetos = []
        else:
            self.objetos = []
            self.cyberware = []
            self.armas = []
            self.dinero = 0
            self.notas_objetos = []

    def guardar_objetos(self):
        data = {
            "objetos": self.objetos,
            "cyberware": self.cyberware,
            "armas": self.armas,
            "dinero": self.dinero,
            "notas": self.notas_objetos,
        }
        with open(OBJETOS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)


    def _cargar_memoria(self):
        if os.path.exists(MEMORIA_FILE):
            try:
                with open(MEMORIA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self.mundo = data.get("mundo", self.mundo)
                self.hechos = data.get("hechos", [])
                self.historial = data.get("historial", [])
                self.trasfondo_protagonista = data.get("trasfondo_protagonista", "")
            except Exception:
                pass

    def guardar_memoria(self):
        data = {
            "mundo": self.mundo,
            "hechos": self.hechos,
            "historial": self.historial,
            "trasfondo_protagonista": self.trasfondo_protagonista,
        }
        with open(MEMORIA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        self._guardar_worlds()
        self.guardar_objetos()

    def estimar_tokens(self, texto):
        """Estima tokens aproximados (1 token ~ 4 caracteres en español)."""
        if not texto:
            return 0
        return max(1, len(texto) // 4)

    def calcular_tokens_historial(self):
        total = self.estimar_tokens(json.dumps(self.historial, ensure_ascii=False))
        total += self.estimar_tokens(json.dumps(self.hechos, ensure_ascii=False))
        total += self.estimar_tokens(json.dumps(self.mundo, ensure_ascii=False))
        return total

    def porcentaje_memoria(self):
        if self.max_tokens_contexto <= 0:
            return 0
        return min(100, int((self.calcular_tokens_historial() / self.max_tokens_contexto) * 100))

    def comprimir_historial(self, app):
        """Pide a la IA que resuma el historial conservando solo lo importante y lo reemplaza."""
        if not app.api_key or len(app.historial) < 4:
            return False

        hechos_txt = "\n".join([f"- {h}" for h in app.hechos]) if app.hechos else "(ninguno aún)"
        system = f"""
Eres un asistente de resumen de conversaciones. Tu tarea es leer el historial de chat siguiente y extraer únicamente:
1. Hechos importantes del usuario (nombre, gustos, datos personales, eventos clave).
2. Resumen breve de lo ocurrido en la historia hasta ahora (continuidad narrativa).
3. Decisiones o compromisos pendientes.

Descarta saludos repetidos, relleno, y conversaciones triviales. Devuelve SOLO una lista de hechos clave y un resumen corto en español, sin explicaciones extra.

Historial de chat:
{json.dumps(app.historial[-20:], ensure_ascii=False, indent=2)}

Hechos previos guardados:
{hechos_txt}
"""

        mensajes = [{"role": "system", "content": system}]

        headers = {
            "Authorization": f"Bearer {app.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": app.config.get("modelo", "meta/llama-3.1-8b-instruct"),
            "messages": mensajes,
            "temperature": 0.5,
            "max_tokens": 800,
        }

        try:
            r = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            resumen = data["choices"][0]["message"]["content"]

            # Guardar el resumen como nuevos hechos y limpiar historial
            lineas = [l.strip("- ").strip() for l in resumen.splitlines() if l.strip()]
            nuevos_hechos = []
            for l in lineas:
                if l and len(l) > 3:
                    nuevos_hechos.append(l)

            app.hechos = list(dict.fromkeys(nuevos_hechos))  # deduplicar
            app.historial = []  # limpiar historial
            app.guardar_memoria()
            return True
        except Exception:
            return False

    def _cargar_lore(self):
        if os.path.exists(LORE_FILE):
            try:
                with open(LORE_FILE, "r", encoding="utf-8") as f:
                    self.lore = json.load(f)
            except Exception:
                self.lore = {}


class ChatScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = None
        self.padding = 10
        self.spacing = 10
        self._saludo_pendiente = True
        self._puntos_spinner = 0
        self._spinner_event = None

        self.main = BoxLayout(orientation="vertical", spacing=10, padding=10)
        self.add_widget(self.main)

        # Área de mensajes
        self.scroll_view = ScrollView(size_hint=(1, 0.72))
        self.msgs_layout = GridLayout(cols=1, size_hint_y=None, spacing=8, padding=5)
        self.msgs_layout.bind(minimum_height=self.msgs_layout.setter('height'))
        self.scroll_view.add_widget(self.msgs_layout)
        self.main.add_widget(self.scroll_view)

        # Indicador de carga (oculto por defecto)
        self.lbl_cargando = Label(
            text="",
            size_hint_y=None,
            height=30,
            halign="left",
            valign="middle",
            color=(0.5, 0.8, 1, 1),
            font_size='14sp',
        )
        self.main.add_widget(self.lbl_cargando)

        # Indicador de memoria
        self.lbl_memoria = Label(
            text="Memoria: 0%",
            size_hint_y=None,
            height=24,
            halign="left",
            valign="middle",
            color=(0.8, 0.8, 0.8, 1),
            font_size='12sp',
        )
        self.main.add_widget(self.lbl_memoria)

        # Entrada y botón
        input_box = BoxLayout(size_hint=(1, 0.17), spacing=5)
        self.input = TextInput(hint_text="Escribe tu mensaje...", multiline=False)
        self.input.bind(on_text_validate=self._enviar)
        self.btn_enviar = Button(text="Enviar", size_hint_x=0.3)
        self.btn_enviar.bind(on_press=self._enviar)
        input_box.add_widget(self.input)
        input_box.add_widget(self.btn_enviar)
        self.main.add_widget(input_box)

        # Navegación inferior
        nav = BoxLayout(size_hint=(1, 0.08), spacing=5)
        btn_custom = Button(text="Personalizar mundo y modelo")
        btn_custom.bind(on_press=lambda x: setattr(self.manager, 'current', 'customize'))
        btn_chatbots = Button(text="Cambiar mundo/chatbot", size_hint_x=0.3)
        btn_chatbots.bind(on_press=lambda x: setattr(self.manager, 'current', 'chatbots'))
        btn_opt = Button(text="Optimizar memoria", size_hint_x=0.25)
        btn_opt.bind(on_press=self._optimizar_memoria)
        btn_reiniciar = Button(text="Reiniciar historia", size_hint_x=0.3)
        btn_reiniciar.bind(on_press=self._reiniciar_historia)
        btn_objetos = Button(text="Ver objetos", size_hint_x=0.25)
        btn_objetos.bind(on_press=self._mostrar_objetos)
        nav.add_widget(btn_custom)
        nav.add_widget(btn_chatbots)
        nav.add_widget(btn_opt)
        nav.add_widget(btn_reiniciar)
        nav.add_widget(btn_objetos)
        self.main.add_widget(nav)

    def _mostrar_objetos(self, instance):
        app = self.app_ref
        if not app:
            return
        app._cargar_objetos()
        lineas = []
        if app.dinero:
            lineas.append(f"💵 Dinero: {app.dinero} eddies")
        if app.cyberware:
            for cw in app.cyberware:
                lineas.append(f"🔧 Cyberware: {cw.get('nombre', cw)}")
        if app.armas:
            for arma in app.armas:
                lineas.append(f"🔫 Arma: {arma.get('nombre', arma)}")
        if app.objetos:
            for obj in app.objetos:
                lineas.append(f"📦 Objeto: {obj.get('nombre', obj)}")
        if app.notas_objetos:
            for n in app.notas_objetos:
                lineas.append(f"📝 Nota: {n}")
        if not lineas:
            lineas.append("Inventario vacío.")
        texto = "\n".join(lineas)
        Popup(title="Tu inventario", content=Label(text=texto), size_hint=(0.85, 0.6)).open()

    def _pedir_api_key(self):
        app = self.app_ref
        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        box.add_widget(Label(text="Ingresa tu API Key de NVIDIA:"))
        ti = TextInput(multiline=False, password=True)
        box.add_widget(ti)
        btn = Button(text="Guardar", size_hint_y=None, height=50)
        box.add_widget(btn)

        popup = Popup(title="API Key requerida", content=box, size_hint=(0.85, 0.4))

        def guardar(instance):
            clave = ti.text.strip()
            if clave:
                app.api_key = clave
                app.config["api_key"] = clave
                app._guardar_config()
                popup.dismiss()

        btn.bind(on_press=guardar)
        popup.open()

    def _actualizar_memoria_label(self):
        app = self.app_ref
        if not app:
            return
        pct = app.porcentaje_memoria()
        self.lbl_memoria.text = f"Memoria: {pct}% ({app.calcular_tokens_historial()} tok / {app.max_tokens_contexto})"
        if pct >= 80:
            self.lbl_memoria.color = (1, 0.4, 0.4, 1)
        elif pct >= 60:
            self.lbl_memoria.color = (1, 0.8, 0.2, 1)
        else:
            self.lbl_memoria.color = (0.8, 0.8, 0.8, 1)

    def _iniciar_spinner(self):
        self.lbl_cargando.text = "Night City está respondiendo"
        self._puntos_spinner = 0
        self.btn_enviar.disabled = True
        self.input.disabled = True
        if self._spinner_event:
            Clock.unschedule(self._spinner_event)
        self._spinner_event = Clock.schedule_interval(self._animar_spinner, 0.5)

    def _animar_spinner(self, dt):
        self._puntos_spinner = (self._puntos_spinner + 1) % 4
        puntos = "." * self._puntos_spinner
        self.lbl_cargando.text = f"Night City está respondiendo{puntos}"

    def _detener_spinner(self):
        if self._spinner_event:
            Clock.unschedule(self._spinner_event)
            self._spinner_event = None
        self.lbl_cargando.text = ""
        self.btn_enviar.disabled = False
        self.input.disabled = False

    def _reiniciar_historia(self, instance):
        app = self.app_ref
        if not app:
            return
        app.historial = []
        app.hechos = []
        app.trasfondo_protagonista = ""
        app.guardar_memoria()
        self._actualizar_memoria_label()
        # Limpiar pantalla de mensajes
        self.msgs_layout.clear_widgets()
        self._saludo_pendiente = True
        self.on_pre_enter()
        popup = Popup(title="Historia reiniciada", content=Label(text="Se borró el historial. Se iniciará una nueva conversación en Night City."), size_hint=(0.85, 0.35))
        popup.open()

    def _optimizar_memoria(self, instance):
        app = self.app_ref
        if not app:
            return
        if not app.api_key:
            popup = Popup(title="Error", content=Label(text="No hay API key configurada."), size_hint=(0.85, 0.35))
            popup.open()
            return
        if len(app.historial) < 4:
            popup = Popup(title="Memoria", content=Label(text="Aún no hay suficiente historial para comprimir."), size_hint=(0.85, 0.35))
            popup.open()
            return

        self._iniciar_spinner()
        self.lbl_cargando.text = "Comprimiendo memoria..."
        threading.Thread(target=self._ejecutar_compresion, args=(app,), daemon=True).start()

    def _ejecutar_compresion(self, app):
        try:
            ok = app.comprimir_historial(app)
            Clock.schedule_once(lambda dt: self._detener_spinner(), 0)
            if ok:
                Clock.schedule_once(lambda dt: self._actualizar_memoria_label(), 0)
                Clock.schedule_once(lambda dt: self._agregar_mensaje(
                    app.mundo["nombre"], "*La memoria se ha comprimido. Se conservaron solo los hechos clave para mantener la continuidad de la historia.*", ia=True), 0)
            else:
                Clock.schedule_once(lambda dt: self._mostrar_error("No se pudo comprimir la memoria."), 0)
        except Exception as e:
            Clock.schedule_once(lambda dt: self._detener_spinner(), 0)
            Clock.schedule_once(lambda dt, err=e: self._mostrar_error(str(err)), 0)

    def on_pre_enter(self):
        app = self.app_ref
        if not app:
            return
        # Si es conversación nueva (sin historial y sin trasfondo elegido), mostrar opciones de trasfondo
        if not app.historial and not app.trasfondo_protagonista:
            self._saludo_pendiente = False
            self._generar_trasfondos_protagonista()
            return
        # Restaurar mensajes del historial previo al entrar
        self.msgs_layout.clear_widgets()
        for m in app.historial:
            remitente = app.mundo["nombre"] if m.get("role") == "assistant" else "Tú"
            self._agregar_mensaje(remitente, m.get("content", ""), ia=(m.get("role") == "assistant"))
        self._saludo_pendiente = False
        if not app.api_key:
            Clock.schedule_once(lambda dt: self._pedir_api_key(), 0.5)
        self._actualizar_memoria_label()

    def _agregar_mensaje(self, remitente, texto, ia=False):
        lbl = Label(
            text=f"[b]{remitente}:[/b] {texto}",
            markup=True,
            size_hint_y=None,
            text_size=(Window.width - 40, None),
            halign="left",
            valign="top",
            color=(0.75, 0.9, 1, 1) if ia else (1, 1, 1, 1),
        )
        lbl.bind(width=lambda *x: lbl.setter('text_size')(lbl, (lbl.width - 40, None)))
        lbl.bind(texture_size=lambda instance, size: setattr(lbl, 'height', size[1] + 20))
        self.msgs_layout.add_widget(lbl)
        # Auto-scroll al final para ver el mensaje nuevo sin subir manualmente
        Clock.schedule_once(lambda dt: self._scroll_final(), 0.1)

    def _scroll_final(self):
        try:
            # En Kivy, scroll_y = 0 es el final (abajo), 1 es el inicio (arriba)
            self.scroll_view.scroll_y = 0
        except Exception:
            pass

    def _enviar(self, instance):
        texto = self.input.text.strip()
        if not texto:
            return
        self.input.text = ""
        app = self.app_ref
        self._agregar_mensaje("Tú", texto, ia=False)
        app.historial.append({"role": "user", "content": texto})
        self._iniciar_spinner()
        self._actualizar_memoria_label()
        threading.Thread(target=self._obtener_respuesta, args=(texto,), daemon=True).start()

    def _obtener_respuesta(self, usuario):
        app = self.app_ref
        try:
            if not app.api_key:
                Clock.schedule_once(lambda dt: self._detener_spinner(), 0)
                Clock.schedule_once(lambda dt: self._mostrar_error("No hay API key configurada."), 0)
                return

            modelo = app.config.get("modelo", "meta/llama-3.1-8b-instruct")

            hechos_txt = "\n".join([f"- {h}" for h in app.hechos]) if app.hechos else "(ninguno aún)"
            lore_resumen = self._resumen_lore(app)

            # --- Optimización de tokens: objetos solo se cargan si se mencionan ---
            palabras_objeto = ["cyberware", "pistola", "arma", "dinero", "creditos", "eddies", "objeto", "item",
                               "equipar", "comprar", "vender", "inventario", "mochila", "crom", "implante"]
            mencionar_objetos = any(p in usuario.lower() for p in palabras_objeto)

            objetos_txt = ""
            if mencionar_objetos:
                app._cargar_objetos()
                lineas = []
                if app.dinero:
                    lineas.append(f"- Dinero: {app.dinero} eddies")
                if app.cyberware:
                    for cw in app.cyberware:
                        lineas.append(f"- Cyberware: {cw}")
                if app.armas:
                    for arma in app.armas:
                        lineas.append(f"- Arma: {arma}")
                if app.objetos:
                    for obj in app.objetos:
                        lineas.append(f"- Objeto: {obj}")
                if app.notas_objetos:
                    for n in app.notas_objetos:
                        lineas.append(f"- Nota: {n}")
                if lineas:
                    objetos_txt = "\nOBJETOS DEL USUARIO (solo consultar si es necesario):\n" + "\n".join(lineas)
                else:
                    objetos_txt = "\nOBJETOS DEL USUARIO: (inventario vacío)\n"

            system = f"""\
Eres {app.mundo['nombre']}, el narrador del mundo de Cyberpunk 2077 y Cyberpunk: Edgerunners.
Personalidad: {app.mundo['personalidad']}
Historia: {app.mundo['historia']}

LORE DE CYBERPUNK (referencia):
{lore_resumen}

Reglas:
- Responde siempre en español.
- El USUARIO es el protagonista. Tú narras el mundo, los escenarios, los NPCs y las consecuencias de sus acciones.
- NO eres un personaje con el que chatear uno a uno. Eres el mundo mismo: describes lo que ve, oye y siente el usuario en Night City.
- Los personajes de Cyberpunk (Lucy, David Martinez, Johnny Silverhand, Rogue, etc.) aparecen como NPCs dentro de la historia, no como el interlocutor directo.
- Escribe como una página de novela: narración y diálogos entre comillas.
- Mantén el tono distópico y cyberpunk de Night City.
- No rompas la cuarta pared.
- Usa los hechos del usuario para recordar detalles personales y retómalos después.
- SI el usuario obtiene, pierde, compra o vende un objeto (arma, cyberware, dinero, ítem), inclúyelo entre corchetes así: [OBJETO: accion, nombre, tipo, cantidad]
  Ejemplo: [OBJETO: obtener, Pistola Maloro, arma, 1]
  Ejemplo: [OBJETO: gastar, Creditos, moneda, -200]
  La app lo registrará automáticamente en el inventario.

Hechos que debes recordar del usuario:
{hechos_txt}
{objetos_txt}
"""

            mensajes = [{"role": "system", "content": system}] + app.historial[-12:]

            headers = {
                "Authorization": f"Bearer {app.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": modelo,
                "messages": mensajes,
                "temperature": 0.8,
                "max_tokens": 1000,
            }

            r = requests.post(API_URL, headers=headers, json=payload, timeout=120)
            r.raise_for_status()
            data = r.json()
            respuesta = data["choices"][0]["message"]["content"]

            # --- Parsear cambios de inventario en la respuesta ---
            self._procesar_objetos_ia(respuesta)

            Clock.schedule_once(lambda dt: self._detener_spinner(), 0)
            Clock.schedule_once(lambda dt: self._mostrar_respuesta(respuesta), 0)

        except Exception as e:
            Clock.schedule_once(lambda dt: self._detener_spinner(), 0)
            Clock.schedule_once(lambda dt, err=e: self._mostrar_error(str(err)), 0)

    def _procesar_objetos_ia(self, texto):
        """Busca patrones [OBJETO: accion, nombre, tipo, cantidad] en la respuesta de la IA y actualiza el inventario."""
        import re
        app = self.app_ref
        if not app:
            return

        patron = r"\[OBJETO:\s*([^\]]+)\]"
        matches = re.findall(patron, texto)
        if not matches:
            return

        for m in matches:
            partes = [p.strip() for p in m.split(",")]
            if len(partes) < 3:
                continue
            accion = partes[0].lower()
            nombre = partes[1]
            tipo = partes[2].lower()
            try:
                cantidad = int(partes[3]) if len(partes) > 3 else 1
            except Exception:
                cantidad = 1

            if accion in ("obtener", "comprar", "recibir", "encontrar"):
                if tipo == "moneda" or nombre.lower() in ("creditos", "eddies", "dinero"):
                    app.dinero += cantidad
                    # Agregar a hechos para que la IA lo recuerde
                    app.hechos.append(f"Obtuvo {cantidad} {nombre}")
                elif tipo == "arma":
                    app.armas.append({"nombre": nombre, "cantidad": cantidad})
                elif tipo == "cyberware":
                    app.cyberware.append({"nombre": nombre, "cantidad": cantidad})
                else:
                    app.objetos.append({"nombre": nombre, "tipo": tipo, "cantidad": cantidad})
            elif accion in ("perder", "vender", "gastar", "usar"):
                if tipo == "moneda" or nombre.lower() in ("creditos", "eddies", "dinero"):
                    app.dinero = max(0, app.dinero - abs(cantidad))
                    app.hechos.append(f"Gastó/perdió {abs(cantidad)} {nombre}")
                elif tipo == "arma":
                    app.armas = [a for a in app.armas if a.get("nombre") != nombre]
                elif tipo == "cyberware":
                    app.cyberware = [c for c in app.cyberware if c.get("nombre") != nombre]
                else:
                    app.objetos = [o for o in app.objetos if o.get("nombre") != nombre]

        # Limpiar patrones [OBJETO: ...] de la respuesta mostrada al usuario
        respuesta_limpia = re.sub(r"\s*\[OBJETO:[^\]]*\]", "", texto)
        # Guardar memoria con objetos actualizados
        app.guardar_memoria()
        # Reemplazar la respuesta guardada en historial por la limpia
        if app.historial and app.historial[-1].get("role") == "assistant":
            app.historial[-1]["content"] = respuesta_limpia
        app.guardar_memoria()


    def _mostrar_respuesta(self, texto):
        app = self.app_ref
        self._agregar_mensaje(app.mundo["nombre"], texto, ia=True)
        app.historial.append({"role": "assistant", "content": texto})
        app.guardar_memoria()

    def _mostrar_error(self, texto):
        popup = Popup(title="Error", content=Label(text=texto), size_hint=(0.85, 0.35))
        popup.open()

    def _resumen_lore(self, app):
        """Genera un resumen del lore de Cyberpunk desde el JSON cargado."""
        if not app.lore:
            return "(lore no disponible)"
        lg = app.lore.get("lore_general", {})
        mundo = lg.get("mundo", {})
        night_city = mundo.get("night_city", {})
        distritos = lg.get("distritos_de_night_city", {}).get("lista", [])
        facciones = lg.get("corporaciones_y_facciones", {})
        tech = lg.get("tecnologia_y_conceptos_clave", {})

        lineas = []
        lineas.append(f"- Mundo: {mundo.get('ambientacion','')}")
        lineas.append(f"- Night City: {night_city.get('estatus_legal','')}. {night_city.get('realidad_actual','')}")
        lineas.append("- Distritos: " + "; ".join([f"{d['nombre']} ({d['descripcion'][:60]}...)" for d in distritos[:4]]))
        megas = facciones.get("megacorporaciones", [])
        if megas:
            lineas.append("- Corporaciones: " + "; ".join([f"{m['nombre']} ({m['especialidad']})" for m in megas]))
        pandillas = facciones.get("pandillas", [])
        if pandillas:
            lineas.append("- Pandillas: " + "; ".join([f"{p['nombre']} ({p.get('territorio','')})" for p in pandillas[:4]]))
        lineas.append("- Tecnología: Braindance, Netrunning, Blackwall, Soulkiller, Ciberpsicosis.")
        cp2077 = app.lore.get("cyberpunk_2077", {})
        protagonistas = cp2077.get("protagonistas_y_aliados_clave", [])
        if protagonistas:
            lineas.append("- Personajes clave: " + "; ".join([f"{p['nombre']} ({p['rol']})" for p in protagonistas[:5]]))
        return "\n".join(lineas)

    def _generar_trasfondos_protagonista(self):
        app = self.app_ref
        if not app or not app.api_key:
            # Sin API key, ir directo al chat con trasfondo vacío
            app.trasfondo_protagonista = ""
            self._saludo_pendiente = True
            self.on_pre_enter()
            return

        self._iniciar_spinner()
        self.lbl_cargando.text = "Generando trasfondos..."
        threading.Thread(target=self._ejecutar_generacion_trasfondos_protagonista, daemon=True).start()

    def _ejecutar_generacion_trasfondos_protagonista(self):
        app = self.app_ref
        try:
            system = """
Eres un escritor creativo de guiones para anime/cyberpunk. El usuario va a empezar una nueva historia en Night City (Cyberpunk 2077).

Genera EXACTAMENTE 2 opciones de trasfondo (origen) distintas para el PROTAGONISTA (el jugador), no para un NPC.

Cada trasfondo debe:
- Tener 2-4 oraciones
- Ser interesante y encajar en el universo cyberpunk (corporaciones, pandillas, distritos, tecnología)
- Dar al protagonista un punto de partida en Night City

Devuelve SOLO los 2 trasfondos, separados por una línea en blanco. Sin numeración, sin explicaciones extra.
"""

            headers = {
                "Authorization": f"Bearer {app.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": app.config.get("modelo", "meta/llama-3.1-8b-instruct"),
                "messages": [{"role": "system", "content": system}],
                "temperature": 0.8,
                "max_tokens": 600,
            }

            r = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            texto = data["choices"][0]["message"]["content"]

            partes = [p.strip() for p in texto.split("\n\n") if p.strip()]
            if len(partes) < 2:
                lineas = [l.strip() for l in texto.splitlines() if l.strip()]
                partes = lineas[:2] if len(lineas) >= 2 else lineas + ["Un ex-corporativo de Arasaka en fuga por las calles de Watson."]

            t1 = partes[0] if len(partes) > 0 else "Un netrunner callejero buscando venganza en Night City."
            t2 = partes[1] if len(partes) > 1 else "Un ex-soldado de Militech intentando sobrevivir en Pacifica."

            Clock.schedule_once(lambda dt: self._mostrar_trasfondos_protagonista(t1, t2), 0)

        except Exception as e:
            Clock.schedule_once(lambda dt: self._detener_spinner(), 0)
            Clock.schedule_once(lambda dt: self._mostrar_error(str(e)), 0)

    def _mostrar_trasfondos_protagonista(self, t1, t2):
        self._detener_spinner()
        app = self.app_ref
        if not app:
            return

        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        box.add_widget(Label(text="Elige tu trasfondo en Night City:", size_hint_y=None, height=30, font_size='16sp'))

        btn1 = Button(text=t1, size_hint_y=None, height=100, halign="left", valign="top", text_size=(None, None))
        btn1.bind(width=lambda *x: btn1.setter('text_size')(btn1, (btn1.width - 20, None)))
        btn1.bind(texture_size=lambda instance, size: setattr(btn1, 'height', max(100, size[1] + 20)))
        btn1.bind(on_press=lambda x: self._seleccionar_trasfondo_protagonista(t1))

        btn2 = Button(text=t2, size_hint_y=None, height=100, halign="left", valign="top", text_size=(None, None))
        btn2.bind(width=lambda *x: btn2.setter('text_size')(btn2, (btn2.width - 20, None)))
        btn2.bind(texture_size=lambda instance, size: setattr(btn2, 'height', max(100, size[1] + 20)))
        btn2.bind(on_press=lambda x: self._seleccionar_trasfondo_protagonista(t2))

        btn_escrito = Button(text="Escribir el mío propio", size_hint_y=None, height=40)
        btn_escrito.bind(on_press=lambda x: self._abrir_trasfondo_personalizado())

        box.add_widget(btn1)
        box.add_widget(btn2)
        box.add_widget(btn_escrito)

        self._popup_trasfondos = Popup(title="Tu trasfondo", content=box, size_hint=(0.9, 0.7))
        self._popup_trasfondos.open()

    def _abrir_trasfondo_personalizado(self):
        if hasattr(self, '_popup_trasfondos') and self._popup_trasfondos:
            self._popup_trasfondos.dismiss()
        app = self.app_ref
        if not app:
            return
        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        box.add_widget(Label(text="Escribe tu trasfondo:", size_hint_y=None, height=30, font_size='16sp'))
        ti = TextInput(multiline=True, hint_text="Ej. Ex-netrunner de Arasaka en fuga por Watson...", size_hint_y=None, height=140)
        box.add_widget(ti)

        btns = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_ok = Button(text="Usar este trasfondo")
        btn_cancelar = Button(text="Cancelar")
        btns.add_widget(btn_ok)
        btns.add_widget(btn_cancelar)
        box.add_widget(btns)

        popup = Popup(title="Tu trasfondo", content=box, size_hint=(0.9, 0.6))

        def usar(instance):
            texto = ti.text.strip()
            if not texto:
                Popup(title="Error", content=Label(text="Escribe algo antes de continuar."), size_hint=(0.7, 0.3)).open()
                return
            popup.dismiss()
            self._seleccionar_trasfondo_protagonista(texto)

        btn_ok.bind(on_press=usar)
        btn_cancelar.bind(on_press=lambda x: popup.dismiss())
        popup.open()

    def _seleccionar_trasfondo_protagonista(self, trasfondo):
        app = self.app_ref
        if not app:
            return
        app.trasfondo_protagonista = trasfondo
        app.hechos.append(f"Trasfondo del protagonista: {trasfondo}")
        app.guardar_memoria()
        if hasattr(self, '_popup_trasfondos') and self._popup_trasfondos:
            self._popup_trasfondos.dismiss()
        # Mostrar saludo del mundo y habilitar chat
        self._saludo_pendiente = True
        self.on_pre_enter()


class CustomizeScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = None

        scroll = ScrollView()
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        scroll.add_widget(self.layout)
        self.add_widget(scroll)

        self.layout.add_widget(Label(text="Personaliza el mundo de Night City", size_hint_y=None, height=40, font_size='20sp'))

        def campo(etiqueta, multiline=False):
            box = BoxLayout(size_hint_y=None, height=60 if not multiline else 140, spacing=5)
            box.add_widget(Label(text=etiqueta, size_hint_x=0.35, halign="right", valign="middle"))
            ti = TextInput(multiline=multiline)
            box.add_widget(ti)
            self.layout.add_widget(box)
            return ti

        self.ti_nombre = campo("Nombre del narrador:")
        self.ti_personalidad = campo("Personalidad del mundo:")
        self.ti_historia = campo("Historia del mundo:", multiline=True)
        self.ti_saludo = campo("Saludo inicial:")

        # ---- Sección de modelo ----
        self.layout.add_widget(Label(text="Modelo de IA (NVIDIA API)", size_hint_y=None, height=40, font_size='18sp'))

        self.ti_modelo_personalizado = TextInput(
            hint_text="Escribe un modelo personalizado (ej. meta/llama-3.1-8b-instruct)",
            multiline=False,
            size_hint_y=None,
            height=50,
        )
        self.layout.add_widget(self.ti_modelo_personalizado)

        modelos_box = BoxLayout(orientation="vertical", spacing=5, size_hint_y=None)
        modelos_box.bind(minimum_height=modelos_box.setter('height'))
        modelos_box.add_widget(Label(text="Modelos rápidos:", size_hint_y=None, height=30))
        for m in MODELOS_SUGERIDOS:
            btn = Button(text=m, size_hint_y=None, height=40)
            btn.bind(on_press=lambda x, m=m: self._seleccionar_modelo(m))
            modelos_box.add_widget(btn)
        self.layout.add_widget(modelos_box)

        # ---- Botones ----
        btns = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_guardar = Button(text="Guardar todo")
        btn_volver = Button(text="Volver al chat")
        btns.add_widget(btn_guardar)
        btns.add_widget(btn_volver)
        self.layout.add_widget(btns)

        btn_guardar.bind(on_press=self._guardar)
        btn_volver.bind(on_press=lambda x: setattr(self.manager, 'current', 'chat'))

    def _seleccionar_modelo(self, modelo):
        self.ti_modelo_personalizado.text = modelo

    def on_pre_enter(self):
        app = self.app_ref
        if not app:
            return
        p = app.mundo
        self.ti_nombre.text = p.get("nombre", "")
        self.ti_personalidad.text = p.get("personalidad", "")
        self.ti_historia.text = p.get("historia", "")
        self.ti_saludo.text = p.get("saludo", "")
        self.ti_modelo_personalizado.text = app.config.get("modelo", "meta/llama-3.1-8b-instruct")

    def _guardar(self, instance):
        app = self.app_ref
        if not app:
            return
        app.mundo["nombre"] = self.ti_nombre.text.strip() or "Narrador de Night City"
        app.mundo["personalidad"] = self.ti_personalidad.text.strip()
        app.mundo["historia"] = self.ti_historia.text.strip()
        app.mundo["saludo"] = self.ti_saludo.text.strip() or "Bienvenido a Night City."

        modelo = self.ti_modelo_personalizado.text.strip() or "meta/llama-3.1-8b-instruct"
        app.config["modelo"] = modelo
        app._guardar_config()

        app.guardar_memoria()
        popup = Popup(title="Guardado", content=Label(text="Mundo y modelo actualizados."), size_hint=(0.7, 0.3))
        popup.open()



class ChatbotsScreen(Screen):
    """Lista de chatbots/worlds disponibles. Al pulsar uno se muestra su info y se puede seleccionar como activo."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.app_ref = None

        scroll = ScrollView()
        self.layout = BoxLayout(orientation="vertical", spacing=10, padding=10, size_hint_y=None)
        self.layout.bind(minimum_height=self.layout.setter('height'))
        scroll.add_widget(self.layout)
        self.add_widget(scroll)

        self.layout.add_widget(Label(text="Mundos / Chatbots disponibles", size_hint_y=None, height=40, font_size='20sp'))

        # Lista de worlds
        self.lista_worlds = GridLayout(cols=1, size_hint_y=None, spacing=5, padding=5)
        self.lista_worlds.bind(minimum_height=self.lista_worlds.setter('height'))
        self.layout.add_widget(self.lista_worlds)

        # Botón para crear nuevo world
        btn_nuevo = Button(text="+ Crear nuevo mundo", size_hint_y=None, height=50)
        btn_nuevo.bind(on_press=self._abrir_crear_mundo)
        self.layout.add_widget(btn_nuevo)

        # Botón volver
        btn_volver = Button(text="Volver al chat", size_hint_y=None, height=50)
        btn_volver.bind(on_press=lambda x: setattr(self.manager, 'current', 'chat'))
        self.layout.add_widget(btn_volver)

    def on_pre_enter(self):
        self._refrescar_lista()

    def _refrescar_lista(self):
        self.lista_worlds.clear_widgets()
        app = self.app_ref
        if not app:
            return
        for w in app.worlds:
            es_activo = w["nombre"] == app.mundo_activo_nombre
            btn = Button(
                text=f"{w['nombre']} {'(ACTIVO)' if es_activo else ''}",
                size_hint_y=None,
                height=50,
                background_color=(0.2, 0.6, 1, 1) if es_activo else (1, 1, 1, 1),
                color=(1, 1, 1, 1) if es_activo else (0, 0, 0, 1),
            )
            btn.bind(on_press=lambda x, nombre=w["nombre"]: self._seleccionar_world(nombre))
            self.lista_worlds.add_widget(btn)

    def _abrir_crear_mundo(self, instance):
        app = self.app_ref
        if not app:
            return
        box = BoxLayout(orientation="vertical", spacing=10, padding=10)
        box.add_widget(Label(text="Crear nuevo mundo/chatbot", size_hint_y=None, height=30, font_size='18sp'))
        box.add_widget(Label(text="Nombre del mundo:", size_hint_y=None, height=25))
        ti_nombre = TextInput(multiline=False, hint_text="Ej. Mundo Postapocalíptico", size_hint_y=None, height=45)
        box.add_widget(ti_nombre)
        box.add_widget(Label(text="JSON con idea/descripción (opcional):", size_hint_y=None, height=25))
        ti_json = TextInput(multiline=True, hint_text='{"ambientacion": "...", "tono": "..."}', size_hint_y=None, height=140)
        box.add_widget(ti_json)

        btns = BoxLayout(size_hint_y=None, height=50, spacing=10)
        btn_crear = Button(text="Crear mundo")
        btn_cancelar = Button(text="Cancelar")
        btns.add_widget(btn_crear)
        btns.add_widget(btn_cancelar)
        box.add_widget(btns)

        popup = Popup(title="Nuevo Mundo", content=box, size_hint=(0.9, 0.75))

        def crear(instance):
            nombre = ti_nombre.text.strip()
            if not nombre:
                Popup(title="Error", content=Label(text="Debes poner un nombre al mundo."), size_hint=(0.7, 0.3)).open()
                return
            texto_json = ti_json.text.strip()
            popup.dismiss()
            self._generar_mundo_con_ia(nombre, texto_json)

        btn_crear.bind(on_press=crear)
        btn_cancelar.bind(on_press=lambda x: popup.dismiss())
        popup.open()

    def _generar_mundo_con_ia(self, nombre, texto_json):
        app = self.app_ref
        if not app or not app.api_key:
            # Sin API key: crear mundo básico sin IA
            nuevo = {
                "nombre": nombre,
                "personalidad": "neutral, descriptivo, inmersivo",
                "historia": f"Mundo llamado {nombre}. Sin descripción adicional.",
                "saludo": f"Bienvenido a {nombre}. ¿Qué haces aquí?",
            }
            app.worlds.append(nuevo)
            app.mundo = dict(nuevo)
            app.mundo_activo_nombre = nombre
            app.guardar_memoria()
            self._refrescar_lista()
            Popup(title="Creado", content=Label(text=f"Mundo '{nombre}' creado (sin IA)."), size_hint=(0.7, 0.3)).open()
            return

        self._iniciar_spinner()
        self.lbl_cargando.text = "Creando mundo con IA..."
        threading.Thread(target=self._ejecutar_generacion_mundo, args=(nombre, texto_json), daemon=True).start()

    def _ejecutar_generacion_mundo(self, nombre, texto_json):
        app = self.app_ref
        try:
            system = f"""
Eres un escritor creativo de guiones para anime/cyberpunk. El usuario quiere crear un nuevo mundo/chatbot llamado "{nombre}" para un roleplay.

El usuario proporcionó esta idea opcional (JSON o texto): {texto_json if texto_json else "ninguna"}

Genera un mundo completo con:
1. Personalidad del narrador/mundo (2-3 adjetivos y estilo)
2. Historia del mundo (ambientación, qué ocurre, en qué se basa)
3. Saludo inicial (frase de bienvenida al usuario al entrar a este mundo)

Devuelve SOLO un objeto JSON válido con los campos: "nombre", "personalidad", "historia", "saludo". Sin explicaciones extra, sin markdown, sin texto antes o después del JSON.
"""

            headers = {
                "Authorization": f"Bearer {app.api_key}",
                "Content-Type": "application/json",
            }
            payload = {
                "model": app.config.get("modelo", "meta/llama-3.1-8b-instruct"),
                "messages": [{"role": "system", "content": system}],
                "temperature": 0.8,
                "max_tokens": 800,
            }

            r = requests.post(API_URL, headers=headers, json=payload, timeout=60)
            r.raise_for_status()
            data = r.json()
            texto = data["choices"][0]["message"]["content"]

            # Intentar parsear JSON
            try:
                import re
                match = re.search(r'\{.*\}', texto, re.DOTALL)
                if match:
                    datos = json.loads(match.group(0))
                else:
                    datos = json.loads(texto)
            except Exception:
                datos = {
                    "nombre": nombre,
                    "personalidad": "neutral, descriptivo, inmersivo",
                    "historia": f"Mundo llamado {nombre}. La IA no pudo generar detalles.",
                    "saludo": f"Bienvenido a {nombre}. ¿Qué haces aquí?",
                }

            datos["nombre"] = datos.get("nombre", nombre)

            nuevo = {
                "nombre": datos["nombre"],
                "personalidad": datos.get("personalidad", "neutral, descriptivo"),
                "historia": datos.get("historia", f"Mundo llamado {nombre}."),
                "saludo": datos.get("saludo", f"Bienvenido a {nombre}."),
            }

            Clock.schedule_once(lambda dt: self._fin_crear_mundo(nuevo), 0)

        except Exception as e:
            Clock.schedule_once(lambda dt, err=e: self._fin_crear_mundo_error(str(err)), 0)

    def _fin_crear_mundo(self, nuevo):
        self._detener_spinner()
        app = self.app_ref
        if not app:
            return
        app.worlds.append(nuevo)
        app.mundo = dict(nuevo)
        app.mundo_activo_nombre = nuevo["nombre"]
        app.guardar_memoria()
        self._refrescar_lista()
        Popup(title="Mundo creado", content=Label(text=f"Ahora usas el mundo: {nuevo['nombre']}"), size_hint=(0.85, 0.35)).open()
        setattr(self.manager, 'current', 'chat')

    def _fin_crear_mundo_error(self, error):
        self._detener_spinner()
        Popup(title="Error", content=Label(text=f"No se pudo crear el mundo: {error}"), size_hint=(0.85, 0.35)).open()

    def _seleccionar_world(self, nombre):
        app = self.app_ref
        if not app:
            return
        app.mundo_activo_nombre = nombre
        for w in app.worlds:
            if w["nombre"] == nombre:
                app.mundo = dict(w)
                break
        app.guardar_memoria()
        self._refrescar_lista()
        popup = Popup(title="Seleccionado", content=Label(text=f"Ahora usas el mundo: {nombre}."), size_hint=(0.7, 0.3))
        popup.open()


if __name__ == "__main__":
    WaifuApp().run()