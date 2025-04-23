import bz2
import os
import sys
import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

# Configuración de colores para la salida
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'

# Variables globales para estadísticas y control
global_stats = {
    'total_files': 0,
    'matches': 0,
    'errors': 0,
    'processed_files': 0
}
print_lock = Lock()
active_threads = 0
max_active_threads = os.cpu_count() * 2  # Ajuste dinámico basado en CPU

def buscar_en_bz2(archivo, cadena, contexto=0, ignorar_mayusculas=False, mostrar_nombre_archivo=True):
    """
    Busca una cadena en un archivo .bz2 de manera eficiente.
    """
    coincidencias = 0
    try:
        with bz2.open(archivo, 'rt', encoding='utf-8', errors='ignore') as f:
            buffer_contexto = []
            num_linea = 0
            
            if ignorar_mayusculas:
                cadena_buscar = cadena.lower()
            
            for linea in f:
                num_linea += 1
                linea_original = linea
                
                if ignorar_mayusculas:
                    linea = linea.lower()
                
                if cadena in linea:
                    coincidencias += 1
                    with print_lock:
                        if mostrar_nombre_archivo and coincidencias == 1:
                            print(f"\n{Colors.BLUE}Archivo: {archivo}{Colors.END}")
                        
                        # Mostrar contexto anterior
                        if contexto > 0 and buffer_contexto:
                            print(f"{Colors.YELLOW}Contexto anterior:{Colors.END}")
                            for ctx_linea, ctx_num in buffer_contexto[-contexto:]:
                                print(f"{ctx_num}: {ctx_linea.rstrip()}")
                        
                        # Resaltar coincidencia
                        linea_resaltada = linea_original.replace(
                            cadena, f"{Colors.RED}{cadena}{Colors.END}")
                        print(f"{Colors.GREEN}{num_linea}:{Colors.END} {linea_resaltada.rstrip()}")
                        
                        # Mostrar líneas posteriores (sin seek)
                        if contexto > 0:
                            print(f"{Colors.YELLOW}Contexto posterior:{Colors.END}")
                            for _ in range(contexto):
                                try:
                                    post_linea = next(f)
                                    num_linea += 1
                                    print(f"{num_linea}: {post_linea.rstrip()}")
                                except StopIteration:
                                    break
                
                # Mantener buffer de contexto
                if contexto > 0:
                    buffer_contexto.append((linea_original, num_linea))
                    if len(buffer_contexto) > contexto:
                        buffer_contexto.pop(0)
    
    except Exception as e:
        with print_lock:
            print(f"{Colors.RED}Error procesando {archivo}: {str(e)}{Colors.END}")
        return 0
    
    return coincidencias

def procesar_archivo(archivo, cadena, opts):
    """
    Función wrapper para procesar un archivo y actualizar estadísticas.
    """
    global active_threads, global_stats
    
    active_threads += 1
    try:
        coincidencias = buscar_en_bz2(
            archivo, 
            cadena,
            contexto=opts['contexto'],
            ignorar_mayusculas=opts['ignorar_mayusculas'],
            mostrar_nombre_archivo=opts['mostrar_nombre_archivo']
        )
        
        with print_lock:
            global_stats['processed_files'] += 1
            global_stats['matches'] += coincidencias
            if global_stats['processed_files'] % 10 == 0:
                mostrar_progreso(global_stats)
            
    finally:
        active_threads -= 1
    
    return coincidencias

def mostrar_progreso(stats):
    """
    Muestra una barra de progreso y estadísticas.
    """
    progress = (stats['processed_files'] / stats['total_files']) * 100
    bar_length = 30
    filled_length = int(bar_length * progress / 100)
    bar = '█' * filled_length + '-' * (bar_length - filled_length)
    
    sys.stdout.write(
        f"\rProgreso: |{bar}| {progress:.1f}% "
        f"| Archivos: {stats['processed_files']}/{stats['total_files']} "
        f"| Coincidencias: {stats['matches']} "
        f"| Errores: {stats['errors']}     "
    )
    sys.stdout.flush()

def buscar_en_directorio(directorio, cadena, opts):
    """
    Busca recursivamente en un directorio usando procesamiento paralelo.
    """
    inicio = datetime.now()
    archivos_a_procesar = []
    exclusiones = opts.get('excluir_dirs', [])
    max_profundidad = opts.get('max_profundidad', float('inf'))
    
    # Recopilar archivos manteniendo control de profundidad
    for root, dirs, files in os.walk(directorio):
        # Control de profundidad
        profundidad = root[len(directorio):].count(os.sep)
        if profundidad > max_profundidad:
            del dirs[:]  # Evita recorrer subdirectorios
            continue
        
        # Excluir directorios
        dirs[:] = [d for d in dirs if d not in exclusiones]
        
        for file in files:
            if file.endswith(opts['extension']):
                archivo_completo = os.path.join(root, file)
                archivos_a_procesar.append(archivo_completo)
    
    global_stats['total_files'] = len(archivos_a_procesar)
    
    print(f"\nIniciando búsqueda de '{cadena}' en {directorio}...")
    print(f"Archivos a procesar: {len(archivos_a_procesar)}")
    print(f"Usando hasta {opts['max_hilos']} hilos paralelos\n")
    
    # Procesamiento paralelo con control de recursos
    with ThreadPoolExecutor(max_workers=opts['max_hilos']) as executor:
        futures = []
        for archivo in archivos_a_procesar:
            futures.append(executor.submit(
                procesar_archivo, 
                archivo=archivo,
                cadena=cadena,
                opts=opts
            ))
        
        try:
            for future in as_completed(futures):
                pass  # Los resultados se manejan en procesar_archivo
        except KeyboardInterrupt:
            print("\n\nBúsqueda interrumpida por el usuario. Finalizando...")
            executor.shutdown(wait=False)
            sys.exit(1)
    
    # Mostrar resumen final
    tiempo_transcurrido = datetime.now() - inicio
    print("\n\n" + "="*60)
    print(f"{Colors.BOLD}Resumen de búsqueda:{Colors.END}")
    print(f"- Cadena buscada: '{cadena}'")
    print(f"- Directorio: {directorio}")
    print(f"- Archivos procesados: {global_stats['processed_files']}")
    print(f"- Coincidencias totales: {global_stats['matches']}")
    print(f"- Errores: {global_stats['errors']}")
    print(f"- Tiempo transcurrido: {tiempo_transcurrido}")
    print("="*60)

def parsear_argumentos():
    """
    Parsea los argumentos de línea de comandos.
    """
    if len(sys.argv) < 3:
        print(f"{Colors.BOLD}Uso:{Colors.END} python buscador_bz2.py <directorio/archivo> <cadena> [opciones]")
        print(f"\n{Colors.BOLD}Opciones:{Colors.END}")
        print("  --contexto N       Muestra N líneas de contexto alrededor de cada coincidencia")
        print("  --ignore-case      Ignora mayúsculas/minúsculas en la búsqueda")
        print("  --excluir dir1,dir2  Excluye directorios específicos")
        print("  --profundidad N    Limita la profundidad de búsqueda a N niveles")
        print("  --hilos N          Usa N hilos paralelos (por defecto: CPU×2)")
        print("  --no-progress      Desactiva la barra de progreso")
        print(f"\n{Colors.BOLD}Ejemplos:{Colors.END}")
        print("  python buscador_bz2.py /var/log/ error --contexto 2")
        print("  python buscador_bz2.py /logs/ 'failed' --ignore-case --excluir cache,temp")
        print("  python buscador_bz2.py archivo.bz2 'excepción'")
        sys.exit(1)
    
    ruta = sys.argv[1]
    cadena_busqueda = sys.argv[2]
    
    opts = {
        'extension': '.bz2',
        'contexto': 0,
        'ignorar_mayusculas': False,
        'excluir_dirs': [],
        'max_profundidad': float('inf'),
        'max_hilos': os.cpu_count() * 2,
        'mostrar_progreso': True,
        'mostrar_nombre_archivo': True
    }
    
    i = 3
    while i < len(sys.argv):
        arg = sys.argv[i]
        if arg == "--contexto" and i+1 < len(sys.argv):
            opts['contexto'] = int(sys.argv[i+1])
            i += 2
        elif arg == "--ignore-case":
            opts['ignorar_mayusculas'] = True
            i += 1
        elif arg == "--excluir" and i+1 < len(sys.argv):
            opts['excluir_dirs'] = [d.strip() for d in sys.argv[i+1].split(",")]
            i += 2
        elif arg == "--profundidad" and i+1 < len(sys.argv):
            opts['max_profundidad'] = int(sys.argv[i+1])
            i += 2
        elif arg == "--hilos" and i+1 < len(sys.argv):
            opts['max_hilos'] = int(sys.argv[i+1])
            i += 2
        elif arg == "--no-progress":
            opts['mostrar_progreso'] = False
            i += 1
        else:
            print(f"{Colors.RED}Argumento desconocido: {arg}{Colors.END}")
            i += 1
    
    return ruta, cadena_busqueda, opts

if __name__ == "__main__":
    ruta, cadena_busqueda, opts = parsear_argumentos()
    
    if os.path.isfile(ruta):
        # Modo archivo único
        coincidencias = buscar_en_bz2(ruta, cadena_busqueda, 
                                    opts['contexto'], opts['ignorar_mayusculas'])
        print(f"\nCoincidencias encontradas: {coincidencias}")
    elif os.path.isdir(ruta):
        # Modo directorio con procesamiento paralelo
        buscar_en_directorio(ruta, cadena_busqueda, opts)
    else:
        print(f"{Colors.RED}Error: {ruta} no es un archivo ni directorio válido{Colors.END}")
        sys.exit(1)
