# Cómo generar el APK de Android

## 1. Sube el código a GitHub
```powershell
cd C:\Users\aleja\Desktop\workspace\chatbot
git init
git add .
git commit -m "Initial commit: Kivy chatbot Cyberpunk NVIDIA API"
git remote add origin https://github.com/TU_USUARIO/TU_REPO.git
git push -u origin main
```
El workflow `.github/workflows/android.yml` se ejecuta automáticamente al hacer push a `main` (o con `workflow_dispatch` desde la pestaña Actions).

## 2. Descarga el APK
- Ve a la pestaña **Actions** de tu repositorio
- Selecciona el workflow "Build Android APK"
- En el run exitoso, baja el artefacto `waifuchat-apk` → `Chatbots-0.1-armeabi-v7a-debug.apk`

## 3. Instala en tu celular
- Pasa el APK al celular (USB, Bluetooth, Drive, etc.)
- En Android: **Ajustes > Seguridad > Instalar apps desconocidas** → activa para tu navegador o gestor de archivos
- Abre el APK y pulsa **Instalar**

## 4. Primera ejecución
- Abre la app "Chatbots"
- Ingresa tu **API Key de NVIDIA** (de `integrate.api.nvidia.com`)
- Elige uno de los 2 trasfondos generados por la IA (o escribe el tuyo)
- Empieza a narrar en Night City

## Notas
- El APK es **debug, sin firmar**: solo para uso personal, no para Google Play
- Requiere permiso de Internet (para llamar a la API de NVIDIA)
- Los JSON (`cyberpunk_lore.json`, `objetos_usuario.json`, `worlds.json`) van incluidos en el APK
- Si no tienes repositorio GitHub, créalo gratis en github.com y sube la carpeta `chatbot` completa
