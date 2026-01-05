#!/bin/bash

# Script de Migración del Sistema de Carga de Fichas
# Para copiar el proyecto a un nuevo VPS con nuevas credenciales

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Sistema de Carga de Fichas - Migración${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Función para mostrar mensajes
info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

success() {
    echo -e "${GREEN}[OK]${NC} $1"
}

warning() {
    echo -e "${YELLOW}[AVISO]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Verificar que estamos en el directorio correcto
if [ ! -f "app.py" ] || [ ! -f "bot.py" ]; then
    error "Este script debe ejecutarse desde el directorio del proyecto"
    error "Asegúrate de estar en la carpeta que contiene app.py y bot.py"
    exit 1
fi

# ============================================
# PASO 1: Solicitar credenciales
# ============================================
echo -e "${YELLOW}PASO 1: Configuración de Credenciales BET${NC}"
echo "----------------------------------------"
echo ""

# Usuario
read -p "Ingresa el USUARIO de AgentesNet: " BET_USER
if [ -z "$BET_USER" ]; then
    error "El usuario no puede estar vacío"
    exit 1
fi

# Contraseña (oculta)
read -s -p "Ingresa la CONTRASEÑA de AgentesNet: " BET_PASSWORD
echo ""
if [ -z "$BET_PASSWORD" ]; then
    error "La contraseña no puede estar vacía"
    exit 1
fi

# Confirmar contraseña
read -s -p "Confirma la CONTRASEÑA: " BET_PASSWORD_CONFIRM
echo ""
if [ "$BET_PASSWORD" != "$BET_PASSWORD_CONFIRM" ]; then
    error "Las contraseñas no coinciden"
    exit 1
fi

# URL (opcional, usar default)
echo ""
read -p "URL de AgentesNet [https://www.agentesbet.net/agents]: " BET_URL
BET_URL=${BET_URL:-"https://www.agentesbet.net/agents"}

# Puerto del servidor
read -p "Puerto del servidor Flask [5000]: " FLASK_PORT
FLASK_PORT=${FLASK_PORT:-5000}

echo ""
success "Credenciales capturadas correctamente"

# ============================================
# PASO 2: Crear archivo .env
# ============================================
echo ""
echo -e "${YELLOW}PASO 2: Creando archivo de configuración .env${NC}"
echo "----------------------------------------------"

# Generar SECRET_KEY aleatorio
SECRET_KEY=$(python3 -c "import secrets; print(secrets.token_hex(32))" 2>/dev/null || echo "clave-secreta-$(date +%s)")

# Backup del .env existente si existe
if [ -f ".env" ]; then
    warning "Archivo .env existente encontrado"
    BACKUP_NAME=".env.backup.$(date +%Y%m%d_%H%M%S)"
    cp .env "$BACKUP_NAME"
    success "Backup creado: $BACKUP_NAME"
fi

# Crear nuevo .env
cat > .env << EOF
# Credenciales de AgentesNet
# Configurado el: $(date '+%Y-%m-%d %H:%M:%S')
AGENTES_URL=$BET_URL
AGENTES_USER=$BET_USER
AGENTES_PASSWORD=$BET_PASSWORD

# Configuración del servidor
FLASK_HOST=0.0.0.0
FLASK_PORT=$FLASK_PORT
FLASK_DEBUG=False
SECRET_KEY=$SECRET_KEY

# Base de datos
DATABASE_URL=sqlite:///cargas.db

# Configuración del bot
HEADLESS=True
TIMEOUT=30000
EOF

success "Archivo .env creado correctamente"

# ============================================
# PASO 3: Verificar Python
# ============================================
echo ""
echo -e "${YELLOW}PASO 3: Verificando requisitos del sistema${NC}"
echo "-------------------------------------------"

if ! command -v python3 &> /dev/null; then
    error "Python 3 no está instalado"
    echo "Instálalo con: sudo apt install python3 python3-pip python3-venv"
    exit 1
fi
success "Python 3 encontrado: $(python3 --version)"

# ============================================
# PASO 4: Crear entorno virtual
# ============================================
echo ""
echo -e "${YELLOW}PASO 4: Configurando entorno virtual${NC}"
echo "-------------------------------------"

if [ -d "venv" ]; then
    warning "Entorno virtual existente encontrado"
    read -p "¿Deseas recrearlo? (s/N): " RECREATE_VENV
    if [ "$RECREATE_VENV" = "s" ] || [ "$RECREATE_VENV" = "S" ]; then
        rm -rf venv
        info "Entorno anterior eliminado"
    fi
fi

if [ ! -d "venv" ]; then
    info "Creando entorno virtual..."
    python3 -m venv venv
    success "Entorno virtual creado"
else
    success "Usando entorno virtual existente"
fi

# ============================================
# PASO 5: Instalar dependencias
# ============================================
echo ""
echo -e "${YELLOW}PASO 5: Instalando dependencias${NC}"
echo "--------------------------------"

source venv/bin/activate

info "Actualizando pip..."
pip install --upgrade pip -q

info "Instalando dependencias de Python..."
pip install -r requirements.txt -q
success "Dependencias instaladas"

info "Instalando navegador Chromium para Playwright..."
playwright install chromium
success "Chromium instalado"

# ============================================
# PASO 6: Verificar credenciales
# ============================================
echo ""
echo -e "${YELLOW}PASO 6: Verificando credenciales de AgentesNet${NC}"
echo "-----------------------------------------------"
echo ""
read -p "¿Deseas verificar las credenciales ahora? (S/n): " VERIFY_CREDS
VERIFY_CREDS=${VERIFY_CREDS:-"s"}

if [ "$VERIFY_CREDS" = "s" ] || [ "$VERIFY_CREDS" = "S" ]; then
    info "Ejecutando prueba de conexión..."
    python3 verify_credentials.py
    VERIFY_RESULT=$?

    if [ $VERIFY_RESULT -eq 0 ]; then
        success "Credenciales verificadas correctamente"
    else
        warning "No se pudo verificar las credenciales"
        warning "Puedes verificarlas manualmente después con: python3 verify_credentials.py"
    fi
else
    info "Puedes verificar las credenciales después con: python3 verify_credentials.py"
fi

# ============================================
# RESUMEN FINAL
# ============================================
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  Migración Completada Exitosamente!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo "Configuración aplicada:"
echo "  - Usuario: $BET_USER"
echo "  - URL: $BET_URL"
echo "  - Puerto: $FLASK_PORT"
echo ""
echo "Para iniciar el servidor:"
echo -e "  ${BLUE}./run.sh${NC}"
echo ""
echo "O manualmente:"
echo -e "  ${BLUE}source venv/bin/activate${NC}"
echo -e "  ${BLUE}python app.py${NC}"
echo ""
echo "Accede a la interfaz web en:"
echo -e "  ${BLUE}http://localhost:$FLASK_PORT${NC}"
echo ""
