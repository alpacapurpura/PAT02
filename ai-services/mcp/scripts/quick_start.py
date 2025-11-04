#!/usr/bin/env python3
"""
Script de inicio rápido para el servidor MCP
Facilita el despliegue, configuración y prueba del servidor MCP

Autor: PATCO - Automatización Industrial
Fecha: Enero 2025
Versión: 1.0
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

import click

# Configuración de colores para la consola
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def print_header(text: str):
    """Imprimir encabezado con formato"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(60)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")

def print_success(text: str):
    """Imprimir mensaje de éxito"""
    print(f"{Colors.OKGREEN}✅ {text}{Colors.ENDC}")

def print_warning(text: str):
    """Imprimir mensaje de advertencia"""
    print(f"{Colors.WARNING}⚠️  {text}{Colors.ENDC}")

def print_error(text: str):
    """Imprimir mensaje de error"""
    print(f"{Colors.FAIL}❌ {text}{Colors.ENDC}")

def print_info(text: str):
    """Imprimir mensaje informativo"""
    print(f"{Colors.OKBLUE}ℹ️  {text}{Colors.ENDC}")

def run_command(command: str, cwd: Optional[str] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Ejecutar comando del sistema"""
    print_info(f"Ejecutando: {command}")
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            check=check
        )
        if result.stdout:
            print(result.stdout)
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Error ejecutando comando: {e}")
        if e.stderr:
            print(e.stderr)
        raise

class MCPQuickStart:
    """Clase para gestionar el inicio rápido del servidor MCP"""
    
    def __init__(self):
        self.project_root = Path.cwd()
        self.mcp_dir = self.project_root / "ai-services" / "mcp"
        self.docker_compose_file = self.project_root / "docker-compose.yml"
    
    def check_prerequisites(self) -> bool:
        """Verificar prerrequisitos del sistema"""
        print_header("VERIFICANDO PRERREQUISITOS")
        
        prerequisites = [
            ("docker", "Docker"),
            ("docker-compose", "Docker Compose"),
            ("python", "Python 3.8+")
        ]
        
        all_ok = True
        for cmd, name in prerequisites:
            try:
                result = run_command(f"{cmd} --version", check=False)
                if result.returncode == 0:
                    print_success(f"{name} está disponible")
                else:
                    print_error(f"{name} no está disponible")
                    all_ok = False
            except Exception:
                print_error(f"{name} no está disponible")
                all_ok = False
        
        # Verificar archivos del proyecto
        required_files = [
            self.docker_compose_file,
            self.mcp_dir / "Dockerfile",
            self.mcp_dir / "requirements.txt"
        ]
        
        for file_path in required_files:
            if file_path.exists():
                print_success(f"Archivo encontrado: {file_path.name}")
            else:
                print_error(f"Archivo faltante: {file_path}")
                all_ok = False
        
        return all_ok
    
    def setup_environment(self):
        """Configurar variables de entorno"""
        print_header("CONFIGURANDO ENTORNO")
        
        env_file = self.project_root / ".env"
        env_example = self.mcp_dir / ".env.example"
        
        if not env_file.exists() and env_example.exists():
            print_info("Creando archivo .env desde .env.example")
            with open(env_example, 'r') as src, open(env_file, 'w') as dst:
                content = src.read()
                # Generar JWT secret key
                import secrets
                jwt_secret = secrets.token_urlsafe(32)
                content = content.replace(
                    "JWT_SECRET_KEY=patco-mcp-secret-key-2025",
                    f"JWT_SECRET_KEY={jwt_secret}"
                )
                dst.write(content)
            print_success("Archivo .env creado")
        elif env_file.exists():
            print_success("Archivo .env ya existe")
        else:
            print_warning("No se pudo crear archivo .env")
    
    def build_services(self):
        """Construir servicios Docker"""
        print_header("CONSTRUYENDO SERVICIOS")
        
        # Construir servicio MCP
        run_command(
            "docker-compose build mcp-server",
            cwd=self.project_root
        )
        print_success("Servicio MCP construido")
    
    def start_dependencies(self):
        """Iniciar servicios de dependencias"""
        print_header("INICIANDO DEPENDENCIAS")
        
        # Iniciar PostgreSQL y Odoo
        run_command(
            "docker-compose up -d db odoo",
            cwd=self.project_root
        )
        
        print_info("Esperando que los servicios estén listos...")
        time.sleep(30)  # Esperar a que los servicios se inicialicen
        
        # Verificar estado de los servicios
        result = run_command(
            "docker-compose ps",
            cwd=self.project_root,
            check=False
        )
        
        if "Up" in result.stdout:
            print_success("Servicios de dependencias iniciados")
        else:
            print_warning("Algunos servicios pueden no estar listos")
    
    def start_mcp_server(self):
        """Iniciar servidor MCP"""
        print_header("INICIANDO SERVIDOR MCP")
        
        run_command(
            "docker-compose --profile ai-services up -d mcp-server",
            cwd=self.project_root
        )
        
        print_info("Esperando que el servidor MCP esté listo...")
        time.sleep(15)
        
        print_success("Servidor MCP iniciado")
    
    def validate_deployment(self):
        """Validar el despliegue"""
        print_header("VALIDANDO DESPLIEGUE")
        
        # Ejecutar script de validación
        validation_script = self.mcp_dir / "scripts" / "validate_mcp_server.py"
        
        if validation_script.exists():
            try:
                # Instalar dependencias de validación
                run_command(
                    "pip install aiohttp psycopg2-binary",
                    check=False
                )
                
                # Ejecutar validación
                env = os.environ.copy()
                env.update({
                    'MCP_BASE_URL': 'http://localhost:8080',
                    'DB_HOST': 'localhost',
                    'DB_PORT': '5432',
                    'DB_NAME': 'odoo_patco',
                    'DB_USER': 'odoo',
                    'DB_PASSWORD': 'P4tc0_2',
                    'ODOO_URL': 'http://localhost:8069'
                })
                
                result = subprocess.run(
                    [sys.executable, str(validation_script)],
                    env=env,
                    cwd=self.project_root
                )
                
                if result.returncode == 0:
                    print_success("Validación completada exitosamente")
                else:
                    print_warning("Validación completada con advertencias")
                    
            except Exception as e:
                print_error(f"Error durante la validación: {e}")
        else:
            print_warning("Script de validación no encontrado")
    
    def show_status(self):
        """Mostrar estado de los servicios"""
        print_header("ESTADO DE SERVICIOS")
        
        run_command(
            "docker-compose ps",
            cwd=self.project_root,
            check=False
        )
        
        print("\n📍 URLs de acceso:")
        print(f"   🌐 Odoo: http://localhost:8069")
        print(f"   🤖 Servidor MCP: http://localhost:8080")
        print(f"   ❤️  Health Check: http://localhost:8080/health")
        
        print("\n📋 Comandos útiles:")
        print(f"   Ver logs MCP: docker-compose logs -f mcp-server")
        print(f"   Reiniciar MCP: docker-compose restart mcp-server")
        print(f"   Detener todo: docker-compose down")
    
    def show_examples(self):
        """Mostrar ejemplos de uso"""
        print_header("EJEMPLOS DE USO")
        
        examples = {
            "Health Check": {
                "method": "GET",
                "url": "http://localhost:8080/health",
                "description": "Verificar estado del servidor"
            },
            "Listar herramientas": {
                "method": "POST",
                "url": "http://localhost:8080/mcp",
                "payload": {
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "tools/list",
                    "params": {}
                },
                "description": "Obtener lista de herramientas disponibles"
            },
            "Obtener orden FSM": {
                "method": "POST",
                "url": "http://localhost:8080/mcp",
                "payload": {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {
                        "name": "get_fsm_order",
                        "arguments": {
                            "order_id": 1
                        }
                    }
                },
                "description": "Obtener información de una orden FSM"
            }
        }
        
        for name, example in examples.items():
            print(f"\n🔧 {name}:")
            print(f"   {example['description']}")
            print(f"   {example['method']} {example['url']}")
            
            if 'payload' in example:
                print(f"   Payload:")
                print(f"   {json.dumps(example['payload'], indent=6)}")

@click.group()
def cli():
    """Servidor MCP - Herramienta de inicio rápido"""
    pass

@cli.command()
def setup():
    """Configuración completa del servidor MCP"""
    quick_start = MCPQuickStart()
    
    try:
        if not quick_start.check_prerequisites():
            print_error("Prerrequisitos no cumplidos. Abortando.")
            sys.exit(1)
        
        quick_start.setup_environment()
        quick_start.build_services()
        quick_start.start_dependencies()
        quick_start.start_mcp_server()
        quick_start.validate_deployment()
        quick_start.show_status()
        
        print_header("🎉 DESPLIEGUE COMPLETADO")
        print_success("El servidor MCP está listo para usar")
        
    except Exception as e:
        print_error(f"Error durante el setup: {e}")
        sys.exit(1)

@cli.command()
def start():
    """Iniciar solo el servidor MCP (asume dependencias ya iniciadas)"""
    quick_start = MCPQuickStart()
    quick_start.start_mcp_server()
    quick_start.show_status()

@cli.command()
def stop():
    """Detener todos los servicios"""
    quick_start = MCPQuickStart()
    run_command(
        "docker-compose down",
        cwd=quick_start.project_root
    )
    print_success("Servicios detenidos")

@cli.command()
def status():
    """Mostrar estado de los servicios"""
    quick_start = MCPQuickStart()
    quick_start.show_status()

@cli.command()
def validate():
    """Validar el servidor MCP"""
    quick_start = MCPQuickStart()
    quick_start.validate_deployment()

@cli.command()
def examples():
    """Mostrar ejemplos de uso"""
    quick_start = MCPQuickStart()
    quick_start.show_examples()

@cli.command()
def logs():
    """Mostrar logs del servidor MCP"""
    quick_start = MCPQuickStart()
    run_command(
        "docker-compose logs -f mcp-server",
        cwd=quick_start.project_root
    )

if __name__ == "__main__":
    cli()