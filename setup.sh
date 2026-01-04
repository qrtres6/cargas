#!/bin/bash

# Script de instalación del Sistema de Carga de Fichas

echo "========================================"
echo "  Sistema de Carga de Fichas - Setup"
echo "========================================"

# Verificar Python
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 no está instalado"
    exit 1
fi

echo "[1/4] Creando entorno virtual..."
python3 -m venv venv

echo "[2/4] Activando entorno virtual..."
source venv/bin/activate

echo "[3/4] Instalando dependencias..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[4/4] Instalando Playwright browsers..."
playwright install chromium

echo ""
echo "========================================"
echo "  Instalación completada!"
echo "========================================"
echo ""
echo "Para iniciar el servidor ejecuta:"
echo "  ./run.sh"
echo ""
echo "O manualmente:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
