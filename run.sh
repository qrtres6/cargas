#!/bin/bash

# Script para iniciar el Sistema de Carga de Fichas

echo "========================================"
echo "  Sistema de Carga de Fichas"
echo "========================================"

# Verificar que existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "Error: Entorno virtual no encontrado."
    echo "Ejecuta primero: ./setup.sh"
    exit 1
fi

# Activar entorno virtual
source venv/bin/activate

# Verificar archivo .env
if [ ! -f ".env" ]; then
    echo "Advertencia: Archivo .env no encontrado."
    echo "Usando configuración por defecto."
fi

echo ""
echo "Iniciando servidor en http://localhost:5000"
echo "Presiona Ctrl+C para detener"
echo ""

# Iniciar servidor
python app.py
