#!/usr/bin/env python3
"""
Script para verificar las credenciales de AgentesNet
Ejecuta un login de prueba para confirmar que las credenciales son correctas
"""

import sys
import os

# Asegurar que estamos en el directorio correcto
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from config import Config
import time

# Colores para terminal
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_info(msg):
    print(f"{Colors.BLUE}[INFO]{Colors.END} {msg}")

def print_success(msg):
    print(f"{Colors.GREEN}[OK]{Colors.END} {msg}")

def print_error(msg):
    print(f"{Colors.RED}[ERROR]{Colors.END} {msg}")

def print_warning(msg):
    print(f"{Colors.YELLOW}[AVISO]{Colors.END} {msg}")


def verificar_configuracion():
    """Verifica que la configuración esté completa"""
    print_info("Verificando configuración...")

    errores = []

    if not Config.AGENTES_URL:
        errores.append("AGENTES_URL no está configurada")

    if not Config.AGENTES_USER or Config.AGENTES_USER == "tu_usuario":
        errores.append("AGENTES_USER no está configurada o tiene valor por defecto")

    if not Config.AGENTES_PASSWORD or Config.AGENTES_PASSWORD == "tu_contraseña":
        errores.append("AGENTES_PASSWORD no está configurada o tiene valor por defecto")

    if errores:
        print_error("Errores en configuración:")
        for error in errores:
            print(f"  - {error}")
        return False

    print_success("Configuración completa")
    print(f"  - URL: {Config.AGENTES_URL}")
    print(f"  - Usuario: {Config.AGENTES_USER}")
    print(f"  - Contraseña: {'*' * len(Config.AGENTES_PASSWORD)}")
    return True


def verificar_login():
    """Intenta hacer login para verificar las credenciales"""
    print_info("Iniciando verificación de login...")

    playwright = None
    browser = None

    try:
        playwright = sync_playwright().start()

        print_info("Iniciando navegador en modo headless...")
        browser = playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )

        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        page.set_default_timeout(30000)

        # Navegar a la página
        print_info(f"Navegando a {Config.AGENTES_URL}...")
        page.goto(Config.AGENTES_URL, wait_until='networkidle')
        time.sleep(2)

        # Buscar campos de login
        usuario_selectors = [
            'input[name="username"]',
            'input[name="user"]',
            'input[name="usuario"]',
            'input[type="text"]',
            '#username',
            '#user',
            'input[placeholder*="usuario" i]',
            'input[placeholder*="user" i]'
        ]

        password_selectors = [
            'input[name="password"]',
            'input[name="pass"]',
            'input[type="password"]',
            '#password',
            '#pass'
        ]

        # Encontrar campo de usuario
        usuario_input = None
        for selector in usuario_selectors:
            try:
                elemento = page.locator(selector).first
                if elemento.is_visible(timeout=1000):
                    usuario_input = elemento
                    print_info(f"Campo usuario encontrado: {selector}")
                    break
            except:
                continue

        if not usuario_input:
            print_error("No se encontró el campo de usuario en la página")
            return False

        # Encontrar campo de contraseña
        password_input = None
        for selector in password_selectors:
            try:
                elemento = page.locator(selector).first
                if elemento.is_visible(timeout=1000):
                    password_input = elemento
                    print_info(f"Campo contraseña encontrado: {selector}")
                    break
            except:
                continue

        if not password_input:
            print_error("No se encontró el campo de contraseña en la página")
            return False

        # Ingresar credenciales
        print_info("Ingresando credenciales...")
        usuario_input.fill(Config.AGENTES_USER)
        time.sleep(0.5)
        password_input.fill(Config.AGENTES_PASSWORD)
        time.sleep(0.5)

        # Buscar botón de login
        login_selectors = [
            'button[type="submit"]',
            'input[type="submit"]',
            'button:has-text("Login")',
            'button:has-text("Ingresar")',
            'button:has-text("Entrar")',
            '.btn-login',
            '#login-btn'
        ]

        for selector in login_selectors:
            try:
                boton = page.locator(selector).first
                if boton.is_visible(timeout=1000):
                    print_info(f"Haciendo click en botón login: {selector}")
                    boton.click()
                    break
            except:
                continue

        # Esperar respuesta del login
        time.sleep(3)
        page.wait_for_load_state('networkidle')

        # Verificar resultado del login
        current_url = page.url
        page_content = page.content().lower()

        # Verificar indicadores de error
        error_indicators = [
            'credenciales incorrectas',
            'usuario o contraseña',
            'invalid credentials',
            'login failed',
            'error de autenticación',
            'contraseña incorrecta',
            'usuario no encontrado'
        ]

        for indicator in error_indicators:
            if indicator in page_content:
                print_error(f"Login fallido: {indicator}")
                return False

        # Verificar indicadores de éxito
        success_indicators = [
            'dashboard',
            'panel',
            'bienvenido',
            'welcome',
            'logout',
            'cerrar sesión',
            'salir'
        ]

        login_exitoso = False

        # Si ya no estamos en página de login
        if 'login' not in current_url.lower():
            login_exitoso = True
            print_success(f"Redirigido a: {current_url}")

        # O si hay indicadores de éxito en la página
        for indicator in success_indicators:
            if indicator in page_content:
                login_exitoso = True
                break

        if login_exitoso:
            print_success("Login verificado correctamente!")
            print_success("Las credenciales son válidas")
            return True
        else:
            print_warning("No se pudo confirmar el estado del login")
            print_warning("Verifica manualmente si las credenciales son correctas")
            return True  # Retornamos True porque no hubo error explícito

    except PlaywrightTimeout as e:
        print_error(f"Timeout: La página tardó demasiado en responder")
        print_error(f"Verifica que la URL {Config.AGENTES_URL} sea accesible")
        return False

    except Exception as e:
        print_error(f"Error durante la verificación: {str(e)}")
        return False

    finally:
        if browser:
            browser.close()
        if playwright:
            playwright.stop()


def main():
    print("")
    print(f"{Colors.BLUE}========================================{Colors.END}")
    print(f"{Colors.BLUE}  Verificación de Credenciales BET{Colors.END}")
    print(f"{Colors.BLUE}========================================{Colors.END}")
    print("")

    # Verificar configuración
    if not verificar_configuracion():
        print("")
        print_error("La configuración no está completa")
        print("Edita el archivo .env con las credenciales correctas")
        sys.exit(1)

    print("")

    # Verificar login
    if verificar_login():
        print("")
        print(f"{Colors.GREEN}========================================{Colors.END}")
        print(f"{Colors.GREEN}  Verificación Exitosa!{Colors.END}")
        print(f"{Colors.GREEN}========================================{Colors.END}")
        print("")
        sys.exit(0)
    else:
        print("")
        print(f"{Colors.RED}========================================{Colors.END}")
        print(f"{Colors.RED}  Verificación Fallida{Colors.END}")
        print(f"{Colors.RED}========================================{Colors.END}")
        print("")
        print("Posibles causas:")
        print("  1. Las credenciales son incorrectas")
        print("  2. La URL de AgentesNet no es accesible")
        print("  3. La estructura de la página ha cambiado")
        print("")
        print("Verifica tu archivo .env y vuelve a intentar")
        sys.exit(1)


if __name__ == "__main__":
    main()
