#!/bin/bash
# Compilacion Android con Buildozer dentro de Docker kivy/buildozer
#
# METODO 1: PIP_CONSTRAINT
# Causa raiz: p4a crea venvs internos y corre `pip install -U pip`, metiendo
# pip 26.3. pip 26.3 removio `capture_logging` de pip._internal.utils.logging.
# p4a importa ese simbolo -> ImportError -> build falla.
#
# Fix: un archivo de constraints `pip<26` exportado por PIP_CONSTRAINT.
# pip respeta PIP_CONSTRAINT en TODA invocacion, incluido el `-U pip` interno
# de p4a. Sin parchear codigo de p4a. Una sola pasada de buildozer.
#
# Solucion previa (doble buildozer + parcheo de p4a) queda reemplazada.

set -euo pipefail

cd /home/user/hostcwd

# --- Constraints: forzar pip<26 en todos los entornos (sistema + venvs de p4a) ---
printf 'pip<26\n' > /home/user/pipconstraints.txt
export PIP_CONSTRAINT=/home/user/pipconstraints.txt
echo "PIP_CONSTRAINT=$PIP_CONSTRAINT"
cat "$PIP_CONSTRAINT"

# --- pip<26 tambien en el sistema (get-pip.py evita el pip 26.3 del contenedor) ---
echo "Instalando pip<26 en el sistema..."
python3 -c "import urllib.request; urllib.request.urlretrieve('https://bootstrap.pypa.io/get-pip.py', '/tmp/get-pip.py')"
python3 /tmp/get-pip.py 'pip<26'
python3 -m pip --version

# --- Compilar (una sola pasada) ---
buildozer android debug
