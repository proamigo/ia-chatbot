#!/bin/bash
# Script de compilación Android con Buildozer dentro de Docker kivy/buildozer
#
# Problema: p4a (python-for-android) crea venvs internos y ejecuta
# `pip install -U pip` dentro de cada uno, forzando pip 26.3, que esta roto
# (ImportError: cannot import name 'capture_logging' from pip._internal.utils.logging).
# Solucion: ejecutar buildozer dos veces. La primera clona p4a (falla por pip 26.3).
# Entre medio, parcheamos build.py del p4a clonado para forzar pip<26.
# La segunda ejecucion reusa p4a clonado y ya no falla.

set -euo pipefail

cd /home/user/hostcwd

# --- 1. Primera ejecucion: clona p4a (fallara por capture_logging con pip 26.3) ---
buildozer android debug || true

# --- 2. Parchear p4a ya clonado: forzar pip<26 en lugar de pip install -U pip ---
P4A_BUILD="/home/user/hostcwd/.buildozer/android/platform/python-for-android/pythonforandroid/build.py"
if [ -f "$P4A_BUILD" ]; then
  sed -i "s|pip install -U pip|pip install 'pip<26'|g" "$P4A_BUILD"
  echo "p4a build.py parcheado con pip<26"
else
  echo "ADVERTENCIA: no se encontro $P4A_BUILD"
fi

# --- 3. Segunda ejecucion: reusa p4a clonado (ya parcheado) y compila ---
buildozer android debug
