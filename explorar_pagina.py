"""
Script para explorar la página de AgentesNet y capturar screenshots
"""

from playwright.sync_api import sync_playwright
from config import Config
import time
import os

def explorar():
    print("Iniciando exploración de AgentesNet...")
    print(f"URL: {Config.AGENTES_URL}")
    print(f"Usuario: {Config.AGENTES_USER}")

    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        page = context.new_page()

        # Paso 1: Ir a la página de login
        print("\n=== PASO 1: Navegando a la página de login ===")
        page.goto(Config.AGENTES_URL, wait_until='networkidle')
        time.sleep(3)

        # Capturar screenshot de login
        page.screenshot(path='screenshots/01_login_page.png', full_page=True)
        print("Screenshot guardado: screenshots/01_login_page.png")

        # Analizar elementos del formulario de login
        print("\n=== Analizando formulario de login ===")

        # Buscar todos los inputs
        inputs = page.query_selector_all('input')
        print(f"\nInputs encontrados: {len(inputs)}")
        for i, inp in enumerate(inputs):
            tipo = inp.get_attribute('type') or 'text'
            name = inp.get_attribute('name') or ''
            placeholder = inp.get_attribute('placeholder') or ''
            clase = inp.get_attribute('class') or ''
            print(f"  Input {i}: type={tipo}, name={name}, placeholder={placeholder}, class={clase}")

        # Buscar botones
        buttons = page.query_selector_all('button')
        print(f"\nBotones encontrados: {len(buttons)}")
        for i, btn in enumerate(buttons):
            texto = btn.text_content().strip()
            tipo = btn.get_attribute('type') or ''
            clase = btn.get_attribute('class') or ''
            print(f"  Button {i}: texto='{texto}', type={tipo}, class={clase}")

        # Intentar login
        print("\n=== PASO 2: Intentando login ===")

        # Buscar campo de usuario/alias
        user_input = page.query_selector('input[type="text"], input[name*="user"], input[name*="alias"]')
        if user_input:
            user_input.fill(Config.AGENTES_USER)
            print(f"Usuario ingresado: {Config.AGENTES_USER}")

        # Buscar campo de contraseña
        pass_input = page.query_selector('input[type="password"]')
        if pass_input:
            pass_input.fill(Config.AGENTES_PASSWORD)
            print("Contraseña ingresada")

        time.sleep(1)
        page.screenshot(path='screenshots/02_login_filled.png', full_page=True)
        print("Screenshot guardado: screenshots/02_login_filled.png")

        # Buscar y clickear botón de login
        login_btn = page.query_selector('button[type="submit"], button:has-text("Ingresar"), button:has-text("Login"), button:has-text("Entrar")')
        if login_btn:
            print(f"Botón encontrado: {login_btn.text_content().strip()}")
            login_btn.click()
            print("Click en botón de login")
        else:
            # Intentar con Enter
            if pass_input:
                pass_input.press('Enter')
                print("Presionando Enter para login")

        # Esperar que cargue
        time.sleep(5)
        page.wait_for_load_state('networkidle')

        page.screenshot(path='screenshots/03_after_login.png', full_page=True)
        print("Screenshot guardado: screenshots/03_after_login.png")
        print(f"URL actual: {page.url}")

        # Analizar página después de login
        print("\n=== PASO 3: Analizando página post-login ===")

        # Buscar campo de búsqueda de usuario
        search_inputs = page.query_selector_all('input[type="text"], input[type="search"]')
        print(f"\nCampos de texto encontrados: {len(search_inputs)}")
        for i, inp in enumerate(search_inputs):
            placeholder = inp.get_attribute('placeholder') or ''
            name = inp.get_attribute('name') or ''
            clase = inp.get_attribute('class') or ''
            print(f"  Input {i}: placeholder='{placeholder}', name={name}, class={clase}")

        # Buscar iconos de lupa o botones de búsqueda
        print("\n=== Buscando elementos de búsqueda ===")
        search_icons = page.query_selector_all('i[class*="search"], svg, .fa-search, button[class*="search"]')
        print(f"Iconos/botones de búsqueda: {len(search_icons)}")

        print("\n=== Exploración completada ===")
        browser.close()

if __name__ == "__main__":
    # Crear directorio de screenshots
    os.makedirs('screenshots', exist_ok=True)
    explorar()
