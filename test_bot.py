"""
Script de prueba para el bot de AgentesNet
Solo hace login y búsqueda, NO carga fichas
"""

from bot import AgentesNetBot
import sys

def test_login_y_busqueda(usuario_prueba):
    print("=" * 50)
    print("TEST: Login y búsqueda de usuario")
    print(f"Usuario de prueba: {usuario_prueba}")
    print("=" * 50)

    bot = AgentesNetBot(headless=True)

    try:
        # Iniciar navegador
        print("\n[1/4] Iniciando navegador...")
        bot.iniciar_navegador()
        print("✓ Navegador iniciado")

        # Login
        print("\n[2/4] Realizando login...")
        resultado_login = bot.login()
        if resultado_login['success']:
            print(f"✓ Login exitoso: {resultado_login['message']}")
        else:
            print(f"✗ Login falló: {resultado_login['message']}")
            return False

        # Buscar usuario
        print(f"\n[3/4] Buscando usuario '{usuario_prueba}'...")
        resultado_busqueda = bot.buscar_usuario(usuario_prueba)
        if resultado_busqueda['success']:
            print(f"✓ Búsqueda exitosa: {resultado_busqueda['message']}")
        else:
            print(f"✗ Búsqueda falló: {resultado_busqueda['message']}")
            return False

        # Encontrar usuario en lista
        print(f"\n[4/4] Buscando '{usuario_prueba}' en resultados...")
        resultado_seleccion = bot.encontrar_usuario_en_lista(usuario_prueba)
        if resultado_seleccion['success']:
            print(f"✓ Usuario encontrado: {resultado_seleccion['message']}")
        else:
            print(f"✗ Usuario no encontrado: {resultado_seleccion['message']}")
            return False

        print("\n" + "=" * 50)
        print("TEST COMPLETADO EXITOSAMENTE")
        print("El bot puede hacer login y encontrar usuarios")
        print("=" * 50)
        return True

    except Exception as e:
        print(f"\n✗ Error durante test: {e}")
        return False

    finally:
        print("\nCerrando navegador...")
        bot.cerrar_navegador()

if __name__ == "__main__":
    usuario = sys.argv[1] if len(sys.argv) > 1 else "carmenbarbieri"
    test_login_y_busqueda(usuario)
