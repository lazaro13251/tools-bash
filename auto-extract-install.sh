#!/bin/bash

# Salir si algo falla
set -e

# Comprobamos que los comandos necesarios están disponibles
comprobar_dependencias() {
  for cmd in tar unzip dpkg apt-get; do
    if ! command -v $cmd &>/dev/null; then
      echo "❌ El comando '$cmd' no está disponible. Por favor, instálalo antes de continuar."
      exit 1
    fi
  done
}

# Función para descomprimir archivos .tar.gz, .tar y .zip
descomprimir_archivos() {
  echo "🔍 Buscando archivos comprimidos..."
  find . -maxdepth 1 -type f \( -iname "*.tar.gz" -o -iname "*.tgz" -o -iname "*.tar" -o -iname "*.zip" \) | while read -r archivo; do
    case "$archivo" in
    *.tar.gz | *.tgz)
      echo "📂 Descomprimiendo $archivo como tar.gz..."
      tar -xvzf "$archivo"
      ;;
    *.tar)
      echo "📂 Descomprimiendo $archivo como tar..."
      tar -xvf "$archivo"
      ;;
    *.zip)
      echo "📂 Descomprimiendo $archivo como zip..."
      unzip -o "$archivo"
      ;;
    *)
      echo "⚠️ Tipo de archivo no reconocido: $archivo"
      ;;
    esac
  done
}

# Función para instalar archivos .deb y resolver dependencias
instalar_debs() {
  echo "📦 Buscando archivos .deb para instalar..."
  archivos_deb=$(find . -type f -name "*.deb")

  if [[ -z "$archivos_deb" ]]; then
    echo "⚠️ No se encontraron archivos .deb."
    return
  fi

  echo "$archivos_deb" | while read -r deb; do
    echo "➡️ Instalando $deb"
    if ! sudo dpkg -i "$deb"; then
      echo "⚠️ Error al instalar $deb. Intentando resolver dependencias..."
    fi
  done

  echo "🔧 Corrigiendo dependencias..."
  sudo apt-get update
  sudo apt-get -f install -y
}

# Ejecutar funciones
comprobar_dependencias
descomprimir_archivos
instalar_debs

echo "✅ Instalación completada con éxito."
