#!/bin/bash
# Script de compilación Android con Buildozer dentro de Docker kivy/buildozer
#
# Problema: p4a (python-for-android) crea venvs internos y ejecuta
# `pip install -U pip` dentro de cada uno, forzando pip 26.3, que esta roto
# (ImportError: cannot import name 'capture_logging' from pip._internal.utils.logging).
# Solucion: ejecutar buildozer dos veces. La primera clona p4a (falla).
# Entre medio, parcheamos build.py y pythonpackage.py del p4a clonado para forzar pip<26.
# La segunda ejecucion reusa p4a clonado (parcheado) y compila.

set -euo pipefail

cd /home/user/hostcwd

# --- 0. Instalar pip 25.3 en el sistema (get-pip.py evita usar pip 26.3 roto) ---
echo "Instalando pip 25.3 en el sistema..."
python3 -c "import urllib.request; urllib.request.urlretrieve('https://bootstrap.pypa.io/pip/25.3/get-pip.py', '/tmp/get-pip.py')"
python3 /tmp/get-pip.py

# --- 1. Primera ejecucion: clona p4a (fallara por capture_logging con pip 26.3 del venv) ---
buildozer android debug || true

# --- 2. Parchear p4a ya clonado: forzar pip<26 en lugar de pip install -U pip ---
P4A_DIR="/home/user/hostcwd/.buildozer/android/platform/python-for-android"
export P4A_DIR
if [ -d "$P4A_DIR" ]; then
  echo "Parcheando p4a en $P4A_DIR ..."
  python3 << 'PYEOF'
import re, os

p4a_dir = os.environ["P4A_DIR"]

# Parchear build.py
build_py = os.path.join(p4a_dir, "pythonforandroid/build.py")
if os.path.exists(build_py):
    content = open(build_py).read()
    content = re.sub(r"pip install\s+(-U|--upgrade)\s+pip", "pip install 'pip<26'", content)
    open(build_py, "w").write(content)
    print("build.py parcheado")

# Parchear pythonpackage.py
pkg_py = os.path.join(p4a_dir, "pythonforandroid/pythonpackage.py")
if os.path.exists(pkg_py):
    content = open(pkg_py).read()
    content = content.replace('"-U", "pip"', "'==pip<26'")
    content = content.replace('"pip", "wheel"', "'pip<26', 'wheel'")
    open(pkg_py, "w").write(content)
    print("pythonpackage.py parcheado")
PYEOF
  echo "p4a parcheado con pip<26"
else
  echo "ADVERTENCIA: no se encontro $P4A_DIR"
fi

# --- 3. Segunda ejecucion: reusa p4a clonado (parcheado) y compila ---
buildozer android debug
