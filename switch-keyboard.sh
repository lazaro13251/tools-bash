#!/bin/bash

# Menú interactivo para cambiar distribución de teclado
echo "Selecciona una distribución de teclado:"
echo "1) Español (España)"
echo "2) Español (Latinoamérica)"
echo "3) Inglés (EE.UU.)"
echo "4) Salir"

read -p "Opción (1-4): " choice

case $choice in
    1)
        setxkbmap es
        echo "Teclado configurado: Español (España)"
        ;;
    2)
        setxkbmap latam
        echo "Teclado configurado: Español (Latinoamérica)"
        ;;
    3)
        setxkbmap us
        echo "Teclado configurado: Inglés (EE.UU.)"
        ;;
    4)
        echo "Saliendo..."
        exit 0
        ;;
    *)
        echo "Opción inválida. Saliendo."
        exit 1
        ;;
esac