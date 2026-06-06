#!/bin/bash
# ─── RadioScript · instalar.sh ───────────────────────────────────────────────
# Instala RadioScript como aplicación del sistema en Ubuntu
# Uso: bash instalar.sh

set -e

VERDE='\033[0;32m'
AZUL='\033[0;34m'
AMARILLO='\033[1;33m'
ROJO='\033[0;31m'
NC='\033[0m'

echo -e "${AZUL}"
echo "╔══════════════════════════════════════╗"
echo "║     RadioScript — Instalador v1.0    ║"
echo "║    Sistema de Informes Radiológicos  ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"

# ── Detectar directorio del proyecto ──────────────────────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo -e "${AZUL}📁 Directorio del proyecto:${NC} $SCRIPT_DIR"

# Verificar que app.py existe
if [ ! -f "$SCRIPT_DIR/app.py" ]; then
    echo -e "${ROJO}❌ Error: No se encontró app.py en $SCRIPT_DIR${NC}"
    echo "   Ejecuta este script desde la carpeta del proyecto RadioScript."
    exit 1
fi

# ── Copiar icono ───────────────────────────────────────────────────────────────
echo -e "\n${AZUL}🖼  Instalando icono...${NC}"
mkdir -p ~/.local/share/icons/hicolor/256x256/apps
cp "$SCRIPT_DIR/icono.png" ~/.local/share/icons/hicolor/256x256/apps/radioscript.png
echo -e "${VERDE}   ✅ Icono instalado${NC}"

# ── Crear lanzador .desktop ───────────────────────────────────────────────────
echo -e "\n${AZUL}🚀 Creando acceso directo en el menú...${NC}"
mkdir -p ~/.local/share/applications

cat > ~/.local/share/applications/radioscript.desktop << EOF
[Desktop Entry]
Name=RadioScript
GenericName=Sistema de Informes Radiológicos
Comment=Transcribe audios médicos y genera informes radiológicos con IA
Exec=python3 $SCRIPT_DIR/app.py
Icon=radioscript
Terminal=false
Type=Application
Categories=Office;Medical;Science;
Keywords=radiología;informes;médico;transcripción;IA;
StartupWMClass=RadioScript
StartupNotify=true
EOF

chmod +x ~/.local/share/applications/radioscript.desktop
echo -e "${VERDE}   ✅ Acceso directo creado${NC}"

# ── Acceso directo en el escritorio ───────────────────────────────────────────
echo -e "\n${AZUL}🖥  Creando acceso directo en el escritorio...${NC}"
ESCRITORIO="$HOME/Escritorio"
if [ ! -d "$ESCRITORIO" ]; then
    ESCRITORIO="$HOME/Desktop"
fi

if [ -d "$ESCRITORIO" ]; then
    cp ~/.local/share/applications/radioscript.desktop "$ESCRITORIO/RadioScript.desktop"
    chmod +x "$ESCRITORIO/RadioScript.desktop"
    # Marcar como confiable (para GNOME)
    gio set "$ESCRITORIO/RadioScript.desktop" metadata::trusted true 2>/dev/null || true
    echo -e "${VERDE}   ✅ Acceso directo en el escritorio creado${NC}"
else
    echo -e "${AMARILLO}   ⚠ No se encontró carpeta Escritorio/Desktop${NC}"
fi

# ── Actualizar base de datos de aplicaciones ──────────────────────────────────
echo -e "\n${AZUL}🔄 Actualizando menú de aplicaciones...${NC}"
update-desktop-database ~/.local/share/applications/ 2>/dev/null || true
gtk-update-icon-cache ~/.local/share/icons/hicolor/ 2>/dev/null || true
echo -e "${VERDE}   ✅ Menú actualizado${NC}"

# ── Verificar dependencias ────────────────────────────────────────────────────
echo -e "\n${AZUL}🔍 Verificando dependencias...${NC}"

check_dep() {
    if python3 -c "import $1" 2>/dev/null; then
        echo -e "${VERDE}   ✅ $1${NC}"
    else
        echo -e "${AMARILLO}   ⚠ $1 no instalado — instala con: pip install $2 --break-system-packages${NC}"
    fi
}

check_dep "faster_whisper"   "faster-whisper"
check_dep "tkinterdnd2"      "tkinterdnd2"
check_dep "mysql.connector"  "mysql-connector-python"
check_dep "docx"             "python-docx"

if command -v ffplay &>/dev/null; then
    echo -e "${VERDE}   ✅ ffplay (audio)${NC}"
else
    echo -e "${AMARILLO}   ⚠ ffplay no encontrado — instala con: sudo apt install ffmpeg${NC}"
fi

if command -v ollama &>/dev/null; then
    echo -e "${VERDE}   ✅ ollama${NC}"
else
    echo -e "${AMARILLO}   ⚠ ollama no encontrado — instala desde: ollama.com${NC}"
fi

# ── Resumen ───────────────────────────────────────────────────────────────────
echo -e "\n${VERDE}"
echo "╔══════════════════════════════════════╗"
echo "║      ✅ Instalación completada       ║"
echo "╚══════════════════════════════════════╝"
echo -e "${NC}"
echo -e "RadioScript ahora aparece en:"
echo -e "  ${AZUL}•${NC} Menú de aplicaciones → Oficina o Ciencia"
echo -e "  ${AZUL}•${NC} Escritorio (doble clic para abrir)"
echo ""
echo -e "Para abrir desde terminal: ${AZUL}python3 $SCRIPT_DIR/app.py${NC}"
echo ""
echo -e "${AMARILLO}💡 Si el icono del escritorio no abre, clic derecho → Permitir lanzar${NC}"
