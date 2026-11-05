# chatbot (app aparte)

Chat de roleplay estilo anime usando la API de NVIDIA (compatível con OpenAI).

## Pantallas
- **Chat**: conversación con tu personaje. Guarda historial y memoria local en `waifu_memoria.json`.
- **Personalizar personaje**: edita nombre, personalidad, historia y saludo. Los cambios se guardan al instante.

## Requisitos
- `kivy`
- `requests`

## Probar en PC
```bash
pip install kivy requests
python main.py
```

## Compilar para Android
Requiere buildozer con el toolchain de Android (JDK 17, Gradle, SDK android-35).
```bash
buildozer -v android debug
```

## Seguridad
No subas `config.json` ni `waifu_memoria.json` a repositorios públicos. Contienen tu API key de NVIDIA y tu historial de chat.
