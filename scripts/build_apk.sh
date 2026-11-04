#!/bin/bash
# Script de compilación Android con Buildozer dentro de Docker kivy/buildozer
#
# Problema: p4a (python-for-android) crea venvs internos y ejecuta
# `pip install -U pip` dentro de cada uno, forzando pip 26.3, que esta roto
# (ImportError: cannot import name 'capture_logging' from pip._internal.utils.logging).
# Solucion: wrapper de pip que intercepta cualquier `install -U pip` / `--upgrade pip`
# y lo convierte en `install 'pip<26'`.

set -euo pipefail

# --- Wrapper de pip para forzar pip<26 en todos los venvs ---
if [ -f /usr/local/bin/pip ] && [ ! -f /usr/local/bin/pip.real ]; then
  mv /usr/local/bin/pip /usr/local/bin/pip.real
fi
if [ -f /usr/local/bin/pip.real ]; then
  cat > /usr/local/bin/pip << 'PIPEOF'
#!/bin/bash
if echo "$@" | grep -qE '(--upgrade|-U).*pip|pip.*(--upgrade|-U)'; then
  set -- "${@//-U pip/==pip<26}"
  set -- "${@//--upgrade pip/==pip<26}"
fi
exec /usr/local/bin/pip.real "$@"
PIPEOF
  chmod +x /usr/local/bin/pip
fi

if [ -f /usr/local/bin/pip3 ] && [ ! -f /usr/local/bin/pip3.real ]; then
  mv /usr/local/bin/pip3 /usr/local/bin/pip3.real
fi
if [ -f /usr/local/bin/pip3.real ]; then
  cat > /usr/local/bin/pip3 << 'PIPEOF3'
#!/bin/bash
if echo "$@" | grep -qE '(--upgrade|-U).*pip|pip.*(--upgrade|-U)'; then
  set -- "${@//-U pip/==pip<26}"
  set -- "${@//--upgrade pip/==pip<26}"
fi
exec /usr/local/bin/pip3.real "$@"
PIPEOF3
  chmod +x /usr/local/bin/pip3
fi

# Instalar pip<26 en el entorno del contenedor
pip install --upgrade 'pip<26'

# Ejecutar buildozer
buildozer android debug
