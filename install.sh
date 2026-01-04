#!/bin/bash
# Script de instalación automática para el Bot de Cargas AgentesNet
# Ejecutar en VPS Ubuntu: bash install.sh

set -e

echo "=========================================="
echo "  Instalador Bot Cargas AgentesNet"
echo "=========================================="

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# 1. Actualizar sistema
echo -e "${YELLOW}[1/6] Actualizando sistema...${NC}"
sudo apt-get update -y
sudo apt-get upgrade -y

# 2. Instalar Python y dependencias del sistema
echo -e "${YELLOW}[2/6] Instalando Python y dependencias...${NC}"
sudo apt-get install -y python3 python3-pip python3-venv git
sudo apt-get install -y libgtk-3-0 libdbus-glib-1-2 libasound2t64 \
    libxcomposite1 libxrandr2 libxdamage1 libxfixes3 libxcursor1 \
    libpango-1.0-0 libcairo2 libgdk-pixbuf2.0-0 libatk1.0-0 \
    libatk-bridge2.0-0 libcups2 libdrm2 libgbm1 libxkbcommon0 \
    fonts-liberation libnss3 libnspr4 xvfb

# 3. Crear entorno virtual
echo -e "${YELLOW}[3/6] Creando entorno virtual...${NC}"
python3 -m venv venv
source venv/bin/activate

# 4. Instalar paquetes Python
echo -e "${YELLOW}[4/6] Instalando paquetes Python...${NC}"
pip install --upgrade pip
pip install playwright python-dotenv flask flask-sqlalchemy

# 5. Instalar Firefox para Playwright
echo -e "${YELLOW}[5/6] Instalando Firefox para automatización...${NC}"
python -m playwright install firefox
python -m playwright install-deps firefox || true

# 6. Crear archivo .env si no existe
echo -e "${YELLOW}[6/6] Configurando archivo .env...${NC}"
if [ ! -f .env ]; then
    cat > .env << 'EOF'
# Credenciales de AgentesNet
AGENTES_URL=https://www.agentesbet.net/
AGENTES_USER=martinbet2
AGENTES_PASSWORD=Xv2T4KGb!

# Configuración del servidor
FLASK_HOST=0.0.0.0
FLASK_PORT=5000
FLASK_DEBUG=False

# Base de datos
DATABASE_URL=sqlite:///cargas.db

# Configuración del bot
HEADLESS=True
TIMEOUT=30000
EOF
    echo -e "${GREEN}Archivo .env creado${NC}"
else
    echo -e "${YELLOW}Archivo .env ya existe, no se modificó${NC}"
fi

echo ""
echo -e "${GREEN}=========================================="
echo "  Instalación completada!"
echo "==========================================${NC}"
echo ""
echo "Para probar el bot:"
echo "  source venv/bin/activate"
echo "  python test_bot.py carmenbarbieri"
echo ""
echo "Para iniciar el servidor web:"
echo "  source venv/bin/activate"
echo "  python app.py"
echo ""
