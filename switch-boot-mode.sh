#!/bin/bash

# Función para cambiar al modo terminal (sin GUI)
text_mode() {
    echo "Cambiando a modo terminal (multi-user.target)..."
    sudo systemctl set-default multi-user.target
    echo "¡Listo! Reinicia para aplicar los cambios:"
    echo "Ejecuta: sudo reboot"
}

# Función para volver al modo gráfico 
graphic_mode() {
    echo "Restaurando modo gráfico (graphical.target)..."
    sudo systemctl set-default graphical.target
    echo "¡Listo! Reinicia para aplicar los cambios:"
    echo "Ejecuta: sudo reboot"
}

# Menú interactivo
while true; do
    clear
    echo "===================================="
    echo "  CAMBIAR MODO DE ARRANQUE EN KALI  "
    echo "===================================="
    echo "1) Modo Terminal (sin GUI)"
    echo "2) Modo Gráfico (con GUI)"
    echo "3) Salir"
    echo "===================================="
    read -p "Elige una opción (1-3): " opcion

    case $opcion in
        1) text_mode ;;
        2) graphic_mode ;;
        3) echo "Saliendo..."; exit 0 ;;
        *) echo "Opción no válida. Intenta de nuevo." ;;
    esac

    read -p "Presiona Enter para continuar..."
done
