#!/bin/bash

# Script de inicio para CryptoPump Bot con Docker
# Uso: ./docker-start.sh [start|stop|restart|logs|status|clean]

set -e

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Función para imprimir mensajes con colores
print_message() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}================================${NC}"
    echo -e "${BLUE}  CryptoPump Bot - Docker${NC}"
    echo -e "${BLUE}================================${NC}"
}

# Verificar que Docker esté instalado
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker no está instalado. Por favor instala Docker primero."
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        print_error "Docker Compose no está instalado. Por favor instala Docker Compose primero."
        exit 1
    fi
}

# Verificar archivo .env
check_env_file() {
    if [ ! -f ".env" ]; then
        print_error "Archivo .env no encontrado. Por favor crea el archivo .env basado en env_example.txt"
        exit 1
    fi
}

# Crear directorios necesarios
create_directories() {
    print_message "Creando directorios necesarios..."
    mkdir -p logs data models
    print_message "Directorios creados correctamente"
}

# Función para iniciar el bot
start_bot() {
    print_header
    print_message "Iniciando CryptoPump Bot con Docker..."
    
    check_docker
    check_env_file
    create_directories
    
    print_message "Construyendo imágenes de Docker..."
    docker-compose build
    
    print_message "Iniciando servicios..."
    docker-compose up -d
    
    print_message "Esperando que los servicios estén listos..."
    sleep 10
    
    print_message "Verificando estado de los servicios..."
    docker-compose ps
    
    print_message "CryptoPump Bot iniciado correctamente!"
    print_message "Accede a Flower (monitoreo): http://localhost:5555"
    print_message "Logs: docker-compose logs -f"
}

# Función para detener el bot
stop_bot() {
    print_header
    print_message "Deteniendo CryptoPump Bot..."
    docker-compose down
    print_message "Bot detenido correctamente"
}

# Función para reiniciar el bot
restart_bot() {
    print_header
    print_message "Reiniciando CryptoPump Bot..."
    docker-compose down
    docker-compose up -d
    print_message "Bot reiniciado correctamente"
}

# Función para mostrar logs
show_logs() {
    print_header
    print_message "Mostrando logs del bot..."
    docker-compose logs -f
}

# Función para mostrar estado
show_status() {
    print_header
    print_message "Estado de los servicios:"
    docker-compose ps
    
    echo ""
    print_message "Uso de recursos:"
    docker stats --no-stream
}

# Función para limpiar contenedores y volúmenes
clean_all() {
    print_header
    print_warning "Esta acción eliminará todos los contenedores, volúmenes y datos del bot."
    read -p "¿Estás seguro? (y/N): " -n 1 -r
    echo
    
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_message "Limpiando todo..."
        docker-compose down -v --remove-orphans
        docker system prune -f
        print_message "Limpieza completada"
    else
        print_message "Limpieza cancelada"
    fi
}

# Función para mostrar ayuda
show_help() {
    print_header
    echo "Uso: $0 [COMANDO]"
    echo ""
    echo "Comandos disponibles:"
    echo "  start     - Iniciar el bot"
    echo "  stop      - Detener el bot"
    echo "  restart   - Reiniciar el bot"
    echo "  logs      - Mostrar logs en tiempo real"
    echo "  status    - Mostrar estado de los servicios"
    echo "  clean     - Limpiar contenedores y volúmenes"
    echo "  help      - Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 start"
    echo "  $0 logs"
    echo "  $0 status"
}

# Función principal
main() {
    case "${1:-help}" in
        start)
            start_bot
            ;;
        stop)
            stop_bot
            ;;
        restart)
            restart_bot
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        clean)
            clean_all
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Comando desconocido: $1"
            show_help
            exit 1
            ;;
    esac
}

# Ejecutar función principal
main "$@"
