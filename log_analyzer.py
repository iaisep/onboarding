#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Script de análisis de logs para el sistema BNP
Permite analizar y filtrar logs de AWS y Django
"""

import os
import sys
import argparse
import datetime
from pathlib import Path

def get_log_files():
    """Obtiene la lista de archivos de logs disponibles"""
    logs_dir = Path('logs')
    if not logs_dir.exists():
        print("❌ Directorio de logs no encontrado")
        return []
    
    log_files = list(logs_dir.glob('*.log'))
    return log_files

def tail_logs(file_path, lines=50):
    """Lee las últimas N líneas de un archivo de log"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            all_lines = f.readlines()
            return all_lines[-lines:]
    except FileNotFoundError:
        print(f"❌ Archivo no encontrado: {file_path}")
        return []
    except Exception as e:
        print(f"❌ Error leyendo archivo: {e}")
        return []

def filter_logs(lines, level=None, keyword=None):
    """Filtra líneas de logs por nivel y/o palabra clave"""
    filtered = []
    
    for line in lines:
        line_upper = line.upper()
        
        # Filtrar por nivel si se especifica
        if level:
            level_upper = level.upper()
            if level_upper not in line_upper:
                continue
        
        # Filtrar por palabra clave si se especifica
        if keyword:
            keyword_upper = keyword.upper()
            if keyword_upper not in line_upper:
                continue
        
        filtered.append(line)
    
    return filtered

def print_logs(lines, show_timestamp=True):
    """Imprime las líneas de logs con formato"""
    if not lines:
        print("📝 No se encontraron logs que coincidan con los criterios")
        return
    
    print(f"📊 Mostrando {len(lines)} líneas de log:")
    print("=" * 80)
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Colorear según el nivel
        if 'ERROR' in line.upper():
            print(f"🔴 {line}")
        elif 'WARNING' in line.upper():
            print(f"🟡 {line}")
        elif 'INFO' in line.upper():
            print(f"🔵 {line}")
        elif 'DEBUG' in line.upper():
            print(f"🟣 {line}")
        else:
            print(f"⚪ {line}")

def get_error_summary():
    """Obtiene un resumen de errores encontrados"""
    logs_dir = Path('logs')
    if not logs_dir.exists():
        return
    
    print("🔍 RESUMEN DE ERRORES ENCONTRADOS")
    print("=" * 50)
    
    error_count = 0
    warning_count = 0
    
    for log_file in logs_dir.glob('*.log'):
        try:
            with open(log_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            file_errors = 0
            file_warnings = 0
            
            for line in lines:
                if 'ERROR' in line.upper():
                    file_errors += 1
                    error_count += 1
                elif 'WARNING' in line.upper():
                    file_warnings += 1
                    warning_count += 1
            
            if file_errors > 0 or file_warnings > 0:
                print(f"📄 {log_file.name}: {file_errors} errores, {file_warnings} warnings")
                
        except Exception as e:
            print(f"❌ Error leyendo {log_file.name}: {e}")
    
    print("-" * 50)
    print(f"📈 TOTAL: {error_count} errores, {warning_count} warnings")

def main():
    parser = argparse.ArgumentParser(
        description='Analizador de logs para el sistema BNP',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  python log_analyzer.py                          # Resumen de errores
  python log_analyzer.py --tail 100               # Últimas 100 líneas
  python log_analyzer.py --level ERROR            # Solo errores
  python log_analyzer.py --keyword "S3"           # Líneas que contienen "S3"
  python log_analyzer.py --file aws_errors.log    # Solo archivo específico
        """
    )
    
    parser.add_argument('--file', '-f', 
                       help='Archivo específico de logs a analizar')
    parser.add_argument('--tail', '-t', type=int, default=50,
                       help='Número de líneas a mostrar (default: 50)')
    parser.add_argument('--level', '-l', 
                       choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       help='Filtrar por nivel de log')
    parser.add_argument('--keyword', '-k', 
                       help='Filtrar por palabra clave')
    parser.add_argument('--summary', '-s', action='store_true',
                       help='Mostrar solo resumen de errores')
    
    args = parser.parse_args()
    
    if args.summary:
        get_error_summary()
        return
    
    # Obtener archivos de logs
    if args.file:
        log_files = [Path('logs') / args.file]
        if not log_files[0].exists():
            print(f"❌ Archivo no encontrado: {log_files[0]}")
            return
    else:
        log_files = get_log_files()
        if not log_files:
            print("❌ No se encontraron archivos de logs")
            return
    
    # Procesar cada archivo
    for log_file in log_files:
        print(f"\n📁 ARCHIVO: {log_file.name}")
        print("=" * 60)
        
        lines = tail_logs(log_file, args.tail)
        filtered_lines = filter_logs(lines, args.level, args.keyword)
        print_logs(filtered_lines)

if __name__ == '__main__':
    main()
