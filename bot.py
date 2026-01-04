"""
Bot de automatización para carga de fichas en AgentesNet
Utiliza Playwright para automatizar el navegador
Selectores actualizados para Vuetify (Vue.js)
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from config import Config
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentesNetBot:
    """Bot para automatizar carga de fichas en agentesbet.net"""

    def __init__(self, headless=None):
        self.headless = headless if headless is not None else Config.HEADLESS
        self.timeout = Config.TIMEOUT
        self.browser = None
        self.page = None
        self.logged_in = False

    def iniciar_navegador(self):
        """Inicia el navegador Playwright"""
        logger.info("Iniciando navegador...")
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.firefox.launch(
            headless=self.headless
        )
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            ignore_https_errors=True
        )
        self.page = self.context.new_page()
        self.page.set_default_timeout(self.timeout)
        logger.info("Navegador iniciado correctamente")

    def cerrar_navegador(self):
        """Cierra el navegador"""
        if self.browser:
            self.browser.close()
            self.playwright.stop()
            self.logged_in = False
            logger.info("Navegador cerrado")

    def login(self):
        """Realiza el login en AgentesNet usando selectores Vuetify"""
        try:
            logger.info(f"Navegando a {Config.AGENTES_URL}")
            self.page.goto(Config.AGENTES_URL, wait_until='domcontentloaded', timeout=60000)

            # Esperar a que cargue la página de login
            time.sleep(2)

            # Campo de Alias (usuario)
            logger.info("Buscando campo de Alias...")
            alias_input = self.page.locator('input[placeholder="Alias"]')
            alias_input.wait_for(state='visible', timeout=10000)
            alias_input.fill(Config.AGENTES_USER)
            logger.info(f"Alias ingresado: {Config.AGENTES_USER}")

            time.sleep(0.5)

            # Campo de Contraseña
            logger.info("Buscando campo de Contraseña...")
            password_input = self.page.locator('input[placeholder="Contraseña"]')
            password_input.wait_for(state='visible', timeout=10000)
            password_input.fill(Config.AGENTES_PASSWORD)
            logger.info("Contraseña ingresada")

            time.sleep(0.5)

            # Botón Iniciar sesión
            logger.info("Buscando botón de Iniciar sesión...")
            login_btn = self.page.locator('button:has-text("Iniciar sesión")')
            login_btn.wait_for(state='visible', timeout=10000)
            login_btn.click()
            logger.info("Click en botón Iniciar sesión")

            # Esperar a que complete el login
            time.sleep(3)
            self.page.wait_for_load_state('networkidle')

            # Verificar si el login fue exitoso buscando el campo de búsqueda
            try:
                search_field = self.page.locator('input[placeholder="Buscar usuario"]')
                search_field.wait_for(state='visible', timeout=10000)
                self.logged_in = True
                logger.info("Login exitoso - Campo de búsqueda visible")
                return {'success': True, 'message': 'Login exitoso'}
            except:
                # Verificar si hay mensaje de error
                error_msg = self.page.locator('.v-alert, .error-message, [role="alert"]')
                if error_msg.count() > 0:
                    error_text = error_msg.first.text_content()
                    return {'success': False, 'message': f'Login falló: {error_text}'}
                return {'success': False, 'message': 'Login falló - No se encontró campo de búsqueda'}

        except PlaywrightTimeout as e:
            logger.error(f"Timeout durante login: {e}")
            return {'success': False, 'message': f'Timeout: {str(e)}'}
        except Exception as e:
            logger.error(f"Error durante login: {e}")
            return {'success': False, 'message': str(e)}

    def buscar_usuario(self, nombre_usuario):
        """Busca un usuario en el sistema usando selectores Vuetify"""
        try:
            logger.info(f"Buscando usuario: {nombre_usuario}")

            # Campo de búsqueda
            search_input = self.page.locator('input[placeholder="Buscar usuario"]')
            search_input.wait_for(state='visible', timeout=10000)
            search_input.clear()
            search_input.fill(nombre_usuario)
            logger.info(f"Usuario ingresado en búsqueda: {nombre_usuario}")

            time.sleep(1)

            # Click en la lupa (icono mdi-magnify)
            logger.info("Buscando botón de lupa...")
            lupa_btn = self.page.locator('button:has(i.mdi-magnify)')
            lupa_btn.wait_for(state='visible', timeout=10000)
            lupa_btn.click()
            logger.info("Click en lupa")

            time.sleep(1)

            # Esperar a que aparezca el menú y seleccionar "Todos los jugadores"
            logger.info("Buscando opción 'Todos los jugadores'...")
            todos_jugadores = self.page.locator('text="Todos los jugadores"')
            todos_jugadores.wait_for(state='visible', timeout=10000)
            todos_jugadores.click()
            logger.info("Click en 'Todos los jugadores'")

            time.sleep(2)
            self.page.wait_for_load_state('networkidle')

            logger.info(f"Búsqueda de usuario {nombre_usuario} completada")
            return {'success': True, 'message': f'Usuario {nombre_usuario} buscado'}

        except PlaywrightTimeout as e:
            logger.error(f"Timeout buscando usuario: {e}")
            return {'success': False, 'message': f'Timeout: {str(e)}'}
        except Exception as e:
            logger.error(f"Error buscando usuario: {e}")
            return {'success': False, 'message': str(e)}

    def encontrar_usuario_en_lista(self, nombre_usuario):
        """Encuentra y selecciona al usuario en la lista de resultados"""
        try:
            logger.info(f"Buscando {nombre_usuario} en la lista de resultados...")
            time.sleep(2)

            # Buscar el usuario en la tabla de resultados
            # Intentar diferentes selectores para encontrar la fila del usuario
            usuario_selectors = [
                f'tr:has-text("{nombre_usuario}")',
                f'td:has-text("{nombre_usuario}")',
                f'.v-data-table tr:has-text("{nombre_usuario}")',
                f'text="{nombre_usuario}"'
            ]

            usuario_fila = None
            for selector in usuario_selectors:
                try:
                    elemento = self.page.locator(selector).first
                    if elemento.is_visible(timeout=2000):
                        usuario_fila = elemento
                        logger.info(f"Usuario encontrado con selector: {selector}")
                        break
                except:
                    continue

            if usuario_fila:
                # Click en la fila para seleccionar el usuario
                usuario_fila.click()
                time.sleep(1)
                logger.info(f"Usuario {nombre_usuario} seleccionado")
                return {'success': True, 'message': f'Usuario {nombre_usuario} encontrado y seleccionado'}
            else:
                logger.warning(f"Usuario {nombre_usuario} no encontrado en la lista")
                return {'success': False, 'message': f'Usuario {nombre_usuario} no encontrado en la lista'}

        except Exception as e:
            logger.error(f"Error encontrando usuario en lista: {e}")
            return {'success': False, 'message': str(e)}

    def cargar_fichas(self, monto):
        """Carga fichas al usuario seleccionado usando selectores Vuetify"""
        try:
            logger.info(f"Iniciando carga de {monto} fichas...")

            # Buscar botón de cargar fichas (icono mdi-cash-plus)
            logger.info("Buscando botón de cargar fichas...")
            cargar_btn = self.page.locator('button:has(i.mdi-cash-plus)')
            cargar_btn.wait_for(state='visible', timeout=10000)
            cargar_btn.first.click()
            logger.info("Click en botón de cargar fichas")

            time.sleep(2)

            # Esperar a que aparezca el modal
            # Buscar el campo de cantidad en el modal
            logger.info("Buscando campo de cantidad en el modal...")

            # Buscar el campo de monto que NO esté deshabilitado
            # El modal tiene un campo de saldo (disabled) y uno de monto (enabled)
            logger.info("Buscando campo de monto habilitado en el modal...")

            # Esperar a que el modal esté visible
            time.sleep(1)

            # Buscar inputs en el dialog que no estén deshabilitados
            monto_input = None

            # Primero intentar con placeholder="10" que es el campo de monto
            try:
                elemento = self.page.locator('.v-dialog input[placeholder="10"]:not([disabled])')
                if elemento.count() > 0 and elemento.first.is_visible(timeout=3000):
                    monto_input = elemento.first
                    logger.info("Campo de monto encontrado con placeholder='10'")
            except:
                pass

            # Si no, buscar cualquier input habilitado en el dialog
            if not monto_input:
                try:
                    inputs = self.page.locator('.v-dialog input.v-field__input:not([disabled])')
                    for i in range(inputs.count()):
                        inp = inputs.nth(i)
                        if inp.is_visible(timeout=1000) and inp.is_enabled(timeout=1000):
                            monto_input = inp
                            logger.info(f"Campo de monto encontrado (input habilitado #{i})")
                            break
                except:
                    pass

            if not monto_input:
                raise Exception("No se encontró el campo para ingresar el monto (todos están deshabilitados)")

            # Limpiar e ingresar el monto
            monto_input.clear()
            monto_input.fill(str(monto))
            logger.info(f"Monto ingresado: {monto}")

            time.sleep(0.5)

            # Buscar y hacer click en botón Enviar
            logger.info("Buscando botón Enviar...")
            enviar_btn = self.page.locator('button:has-text("Enviar")')
            enviar_btn.wait_for(state='visible', timeout=10000)
            enviar_btn.click()
            logger.info("Click en botón Enviar")

            time.sleep(3)
            self.page.wait_for_load_state('networkidle')

            # Verificar si la carga fue exitosa
            # Buscar mensaje de éxito o que el modal se haya cerrado
            try:
                success_msg = self.page.locator('.v-snackbar:has-text("éxito"), .v-alert--success, [role="alert"]:has-text("éxito")')
                if success_msg.count() > 0:
                    logger.info("Mensaje de éxito detectado")
            except:
                pass

            logger.info(f"Carga de {monto} fichas completada")
            return {'success': True, 'message': f'Carga de {monto} fichas completada exitosamente'}

        except PlaywrightTimeout as e:
            logger.error(f"Timeout cargando fichas: {e}")
            return {'success': False, 'message': f'Timeout: {str(e)}'}
        except Exception as e:
            logger.error(f"Error cargando fichas: {e}")
            return {'success': False, 'message': str(e)}

    def ejecutar_carga_completa(self, nombre_usuario, monto):
        """Ejecuta el proceso completo de carga de fichas"""
        resultados = {
            'login': None,
            'busqueda': None,
            'seleccion': None,
            'carga': None,
            'success': False,
            'message': ''
        }

        try:
            self.iniciar_navegador()

            # Login
            resultados['login'] = self.login()
            if not resultados['login']['success']:
                resultados['message'] = f"Error en login: {resultados['login']['message']}"
                return resultados

            # Buscar usuario
            resultados['busqueda'] = self.buscar_usuario(nombre_usuario)
            if not resultados['busqueda']['success']:
                resultados['message'] = f"Error en búsqueda: {resultados['busqueda']['message']}"
                return resultados

            # Encontrar usuario en lista
            resultados['seleccion'] = self.encontrar_usuario_en_lista(nombre_usuario)
            if not resultados['seleccion']['success']:
                resultados['message'] = f"Error en selección: {resultados['seleccion']['message']}"
                return resultados

            # Cargar fichas
            resultados['carga'] = self.cargar_fichas(monto)
            if not resultados['carga']['success']:
                resultados['message'] = f"Error en carga: {resultados['carga']['message']}"
                return resultados

            resultados['success'] = True
            resultados['message'] = f"Carga exitosa: {monto} fichas a {nombre_usuario}"
            return resultados

        except Exception as e:
            resultados['message'] = f"Error general: {str(e)}"
            return resultados

        finally:
            self.cerrar_navegador()


# Para pruebas directas
if __name__ == "__main__":
    bot = AgentesNetBot(headless=False)
    resultado = bot.ejecutar_carga_completa("usuario_test", 100)
    print(resultado)
