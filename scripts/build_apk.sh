#!/bin/bash
# Script de compilación Android con Buildozer dentro de Docker kivy/buildozer
#
# Problema: p4a (python-for-android) crea venvs internos y ejecuta
# `pip install -U pip` dentro de cada uno, forzando pip 26.3, que esta roto
# (ImportError: cannot import name 'capture_logging' from pip._internal.utils.logging).
# Solucion: clonar p4a master localmente, parchear build.py para forzar pip<26,
# y usar p4a.source_dir para que buildozer use la copia parcheada.

set -euo pipefail

cd /home/user/hostcwd

# --- 1. Clonar p4a master localmente ---
if [ ! -d /tmp/p4a-master ]; then
  git clone -b master --depth 1 https://github.com/kivy/python-for-android.git /tmp/p4a-master
fi

# --- 2. Parchear p4a: forzar pip<26 en lugar de pip install -U pip ---
sed -i "s|pip install -U pip|pip install 'pip<26'|g" /tmp/p4a-master/pythonforandroid/build.py

# --- 3. Configurar buildozer.spec para usar p4a parcheado ---
sed -i "/^p4a.source_dir =/d" buildozer.spec
echo "p4a.source_dir = /tmp/p4a-master" >> buildozer.spec

# --- 4. Ejecutar buildozer ---
buildozer android debug
