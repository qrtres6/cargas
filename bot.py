"""
Bot de automatización para carga de fichas en AgentesNet
Utiliza Playwright para automatizar el navegador
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
        self.browser = self.playwright.chromium.launch(
            headless=self.headless,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.context = self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
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
        """Realiza el login en AgentesNet"""
        try:
            logger.info(f"Navegando a {Config.AGENTES_URL}")
            self.page.goto(Config.AGENTES_URL, wait_until='networkidle')

            # Esperar a que cargue la página de login
            time.sleep(2)

            # Buscar campos de usuario y contraseña
            # Intentar diferentes selectores comunes
            usuario_selectors = [
                'input[name="username"]',
                'input[name="user"]',
                'input[name="usuario"]',
                'input[type="text"]',
                '#username',
                '#user',
                '.username',
                'input[placeholder*="usuario" i]',
                'input[placeholder*="user" i]'
            ]

            password_selectors = [
                'input[name="password"]',
                'input[name="pass"]',
                'input[name="contraseña"]',
                'input[type="password"]',
                '#password',
                '#pass',
                '.password'
            ]

            # Encontrar campo de usuario
            usuario_input = None
            for selector in usuario_selectors:
                try:
                    elemento = self.page.locator(selector).first
                    if elemento.is_visible(timeout=1000):
                        usuario_input = elemento
                        logger.info(f"Campo usuario encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not usuario_input:
                raise Exception("No se encontró el campo de usuario")

            # Encontrar campo de contraseña
            password_input = None
            for selector in password_selectors:
                try:
                    elemento = self.page.locator(selector).first
                    if elemento.is_visible(timeout=1000):
                        password_input = elemento
                        logger.info(f"Campo password encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not password_input:
                raise Exception("No se encontró el campo de contraseña")

            # Ingresar credenciales
            logger.info("Ingresando credenciales...")
            usuario_input.fill(Config.AGENTES_USER)
            time.sleep(0.5)
            password_input.fill(Config.AGENTES_PASSWORD)
            time.sleep(0.5)

            # Buscar y hacer click en botón de login
            login_selectors = [
                'button[type="submit"]',
                'input[type="submit"]',
                'button:has-text("Login")',
                'button:has-text("Ingresar")',
                'button:has-text("Entrar")',
                '.btn-login',
                '#login-btn',
                'button.login'
            ]

            for selector in login_selectors:
                try:
                    boton = self.page.locator(selector).first
                    if boton.is_visible(timeout=1000):
                        boton.click()
                        logger.info(f"Click en botón login con selector: {selector}")
                        break
                except:
                    continue

            # Esperar a que complete el login
            time.sleep(3)
            self.page.wait_for_load_state('networkidle')

            # Verificar si el login fue exitoso (no estamos en página de login)
            current_url = self.page.url
            if 'login' not in current_url.lower() or 'dashboard' in current_url.lower():
                self.logged_in = True
                logger.info("Login exitoso!")
                return {'success': True, 'message': 'Login exitoso'}
            else:
                return {'success': False, 'message': 'Login falló - aún en página de login'}

        except PlaywrightTimeout as e:
            logger.error(f"Timeout durante login: {e}")
            return {'success': False, 'message': f'Timeout: {str(e)}'}
        except Exception as e:
            logger.error(f"Error durante login: {e}")
            return {'success': False, 'message': str(e)}

    def buscar_usuario(self, nombre_usuario):
        """Busca un usuario en el sistema"""
        try:
            logger.info(f"Buscando usuario: {nombre_usuario}")

            # Buscar el cuadro de búsqueda
            search_selectors = [
                'input[type="search"]',
                'input[name="search"]',
                'input[name="buscar"]',
                'input[placeholder*="buscar" i]',
                'input[placeholder*="search" i]',
                'input[placeholder*="usuario" i]',
                '.search-input',
                '#search',
                '.form-control[type="text"]'
            ]

            search_input = None
            for selector in search_selectors:
                try:
                    elemento = self.page.locator(selector).first
                    if elemento.is_visible(timeout=2000):
                        search_input = elemento
                        logger.info(f"Campo búsqueda encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not search_input:
                # Intentar buscar cualquier input visible que parezca de búsqueda
                inputs = self.page.locator('input[type="text"]:visible')
                if inputs.count() > 0:
                    search_input = inputs.first
                    logger.info("Usando primer input de texto visible")

            if not search_input:
                raise Exception("No se encontró el campo de búsqueda")

            # Limpiar y escribir el nombre de usuario
            search_input.clear()
            search_input.fill(nombre_usuario)
            time.sleep(1)

            # Buscar y hacer click en la lupa
            lupa_selectors = [
                'button:has(svg)',
                '.search-btn',
                '.btn-search',
                'button[type="submit"]',
                'i.fa-search',
                '.fa-search',
                'button:has-text("Buscar")',
                '[class*="search"] button',
                'button:has(i[class*="search"])',
                '.input-group-append button',
                '.search-icon'
            ]

            lupa_clicked = False
            for selector in lupa_selectors:
                try:
                    lupa = self.page.locator(selector).first
                    if lupa.is_visible(timeout=1000):
                        lupa.click()
                        logger.info(f"Click en lupa con selector: {selector}")
                        lupa_clicked = True
                        break
                except:
                    continue

            if not lupa_clicked:
                # Intentar presionar Enter
                search_input.press('Enter')
                logger.info("Presionando Enter para buscar")

            time.sleep(2)

            # Buscar opción "Todos los jugadores"
            jugadores_selectors = [
                'text=todos los jugadores',
                'text=Todos los Jugadores',
                'text=TODOS LOS JUGADORES',
                'a:has-text("jugadores")',
                'button:has-text("jugadores")',
                '.dropdown-item:has-text("jugadores")',
                '[class*="player"]',
                'li:has-text("jugadores")'
            ]

            for selector in jugadores_selectors:
                try:
                    opcion = self.page.locator(selector).first
                    if opcion.is_visible(timeout=2000):
                        opcion.click()
                        logger.info(f"Click en 'Todos los jugadores' con selector: {selector}")
                        break
                except:
                    continue

            time.sleep(2)
            self.page.wait_for_load_state('networkidle')

            logger.info(f"Búsqueda de usuario {nombre_usuario} completada")
            return {'success': True, 'message': f'Usuario {nombre_usuario} buscado'}

        except Exception as e:
            logger.error(f"Error buscando usuario: {e}")
            return {'success': False, 'message': str(e)}

    def encontrar_usuario_en_lista(self, nombre_usuario):
        """Encuentra y selecciona al usuario en la lista de resultados"""
        try:
            logger.info(f"Buscando {nombre_usuario} en la lista de resultados...")
            time.sleep(2)

            # Buscar el usuario en la tabla/lista de resultados
            usuario_selectors = [
                f'text="{nombre_usuario}"',
                f'td:has-text("{nombre_usuario}")',
                f'tr:has-text("{nombre_usuario}")',
                f'a:has-text("{nombre_usuario}")',
                f'.user-row:has-text("{nombre_usuario}")',
                f'[data-user="{nombre_usuario}"]'
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

            if not usuario_fila:
                # Intentar buscar en tabla
                tabla = self.page.locator('table tbody tr')
                for i in range(tabla.count()):
                    fila = tabla.nth(i)
                    texto = fila.text_content()
                    if nombre_usuario.lower() in texto.lower():
                        usuario_fila = fila
                        logger.info(f"Usuario encontrado en fila {i} de la tabla")
                        break

            if usuario_fila:
                usuario_fila.click()
                time.sleep(1)
                return {'success': True, 'message': f'Usuario {nombre_usuario} encontrado'}
            else:
                return {'success': False, 'message': f'Usuario {nombre_usuario} no encontrado en la lista'}

        except Exception as e:
            logger.error(f"Error encontrando usuario en lista: {e}")
            return {'success': False, 'message': str(e)}

    def cargar_fichas(self, monto):
        """Carga fichas al usuario seleccionado"""
        try:
            logger.info(f"Cargando {monto} fichas...")

            # Buscar botón de cargar fichas
            cargar_selectors = [
                'button:has-text("cargar")',
                'button:has-text("Cargar")',
                'button:has-text("depositar")',
                'button:has-text("Depositar")',
                'button:has-text("agregar")',
                'a:has-text("cargar")',
                '.btn-cargar',
                '.btn-deposit',
                '[class*="deposit"]',
                '[class*="cargar"]',
                'button:has-text("fichas")',
                'i.fa-plus',
                'button:has(i.fa-plus)'
            ]

            boton_cargar = None
            for selector in cargar_selectors:
                try:
                    elemento = self.page.locator(selector).first
                    if elemento.is_visible(timeout=2000):
                        boton_cargar = elemento
                        logger.info(f"Botón cargar encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not boton_cargar:
                raise Exception("No se encontró el botón de cargar fichas")

            boton_cargar.click()
            time.sleep(2)

            # Buscar campo para ingresar monto
            monto_selectors = [
                'input[name="amount"]',
                'input[name="monto"]',
                'input[name="cantidad"]',
                'input[type="number"]',
                'input[placeholder*="monto" i]',
                'input[placeholder*="amount" i]',
                'input[placeholder*="cantidad" i]',
                '.amount-input',
                '#amount',
                '#monto'
            ]

            monto_input = None
            for selector in monto_selectors:
                try:
                    elemento = self.page.locator(selector).first
                    if elemento.is_visible(timeout=2000):
                        monto_input = elemento
                        logger.info(f"Campo monto encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not monto_input:
                # Buscar en modal si existe
                modal = self.page.locator('.modal:visible, .dialog:visible, [role="dialog"]:visible')
                if modal.count() > 0:
                    monto_input = modal.locator('input[type="number"], input[type="text"]').first

            if not monto_input:
                raise Exception("No se encontró el campo para ingresar el monto")

            # Ingresar monto
            monto_input.clear()
            monto_input.fill(str(monto))
            time.sleep(0.5)

            # Confirmar la carga
            confirmar_selectors = [
                'button:has-text("confirmar")',
                'button:has-text("Confirmar")',
                'button:has-text("aceptar")',
                'button:has-text("Aceptar")',
                'button:has-text("guardar")',
                'button:has-text("enviar")',
                'button[type="submit"]',
                '.btn-confirm',
                '.btn-success',
                '.btn-primary'
            ]

            for selector in confirmar_selectors:
                try:
                    confirmar = self.page.locator(selector).first
                    if confirmar.is_visible(timeout=2000):
                        confirmar.click()
                        logger.info(f"Click en confirmar con selector: {selector}")
                        break
                except:
                    continue

            time.sleep(3)
            self.page.wait_for_load_state('networkidle')

            logger.info(f"Carga de {monto} fichas completada")
            return {'success': True, 'message': f'Carga de {monto} fichas completada exitosamente'}

        except Exception as e:
            logger.error(f"Error cargando fichas: {e}")
            return {'success': False, 'message': str(e)}

    def descargar_fichas(self, monto):
        """Descarga/retira fichas del usuario seleccionado"""
        try:
            logger.info(f"Descargando {monto} fichas...")

            # Buscar botón de descargar/retirar fichas
            descargar_selectors = [
                'button:has-text("descargar")',
                'button:has-text("Descargar")',
                'button:has-text("retirar")',
                'button:has-text("Retirar")',
                'button:has-text("withdraw")',
                'a:has-text("descargar")',
                'a:has-text("retirar")',
                '.btn-descargar',
                '.btn-withdraw',
                '.btn-retirar',
                '[class*="withdraw"]',
                '[class*="descargar"]',
                'i.fa-minus',
                'button:has(i.fa-minus)'
            ]

            boton_descargar = None
            for selector in descargar_selectors:
                try:
                    elemento = self.page.locator(selector).first
                    if elemento.is_visible(timeout=2000):
                        boton_descargar = elemento
                        logger.info(f"Botón descargar encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not boton_descargar:
                raise Exception("No se encontró el botón de descargar fichas")

            boton_descargar.click()
            time.sleep(2)

            # Buscar campo para ingresar monto
            monto_selectors = [
                'input[name="amount"]',
                'input[name="monto"]',
                'input[name="cantidad"]',
                'input[type="number"]',
                'input[placeholder*="monto" i]',
                'input[placeholder*="amount" i]',
                '.amount-input',
                '#amount',
                '#monto'
            ]

            monto_input = None
            for selector in monto_selectors:
                try:
                    elemento = self.page.locator(selector).first
                    if elemento.is_visible(timeout=2000):
                        monto_input = elemento
                        logger.info(f"Campo monto encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not monto_input:
                modal = self.page.locator('.modal:visible, .dialog:visible, [role="dialog"]:visible')
                if modal.count() > 0:
                    monto_input = modal.locator('input[type="number"], input[type="text"]').first

            if not monto_input:
                raise Exception("No se encontró el campo para ingresar el monto")

            monto_input.clear()
            monto_input.fill(str(monto))
            time.sleep(0.5)

            # Confirmar la descarga
            confirmar_selectors = [
                'button:has-text("confirmar")',
                'button:has-text("Confirmar")',
                'button:has-text("aceptar")',
                'button:has-text("Aceptar")',
                'button:has-text("guardar")',
                'button[type="submit"]',
                '.btn-confirm',
                '.btn-success',
                '.btn-primary',
                '.btn-danger'
            ]

            for selector in confirmar_selectors:
                try:
                    confirmar = self.page.locator(selector).first
                    if confirmar.is_visible(timeout=2000):
                        confirmar.click()
                        logger.info(f"Click en confirmar con selector: {selector}")
                        break
                except:
                    continue

            time.sleep(3)
            self.page.wait_for_load_state('networkidle')

            logger.info(f"Descarga de {monto} fichas completada")
            return {'success': True, 'message': f'Descarga de {monto} fichas completada exitosamente'}

        except Exception as e:
            logger.error(f"Error descargando fichas: {e}")
            return {'success': False, 'message': str(e)}

    def crear_usuario(self, alias, password):
        """Crea un nuevo usuario en la plataforma"""
        try:
            logger.info(f"Creando usuario: {alias}")

            # Buscar botón de crear usuario
            crear_selectors = [
                'button:has-text("crear")',
                'button:has-text("Crear")',
                'button:has-text("nuevo")',
                'button:has-text("Nuevo")',
                'button:has-text("agregar usuario")',
                'button:has-text("new user")',
                'a:has-text("crear")',
                'a:has-text("nuevo")',
                '.btn-crear',
                '.btn-new',
                '[class*="create"]',
                '[class*="new-user"]',
                'i.fa-user-plus',
                'button:has(i.fa-user-plus)'
            ]

            boton_crear = None
            for selector in crear_selectors:
                try:
                    elemento = self.page.locator(selector).first
                    if elemento.is_visible(timeout=2000):
                        boton_crear = elemento
                        logger.info(f"Botón crear encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not boton_crear:
                raise Exception("No se encontró el botón de crear usuario")

            boton_crear.click()
            time.sleep(2)

            # Buscar campo de alias/nombre de usuario
            alias_selectors = [
                'input[name="alias"]',
                'input[name="username"]',
                'input[name="usuario"]',
                'input[name="user"]',
                'input[placeholder*="alias" i]',
                'input[placeholder*="usuario" i]',
                'input[placeholder*="username" i]',
                '#alias',
                '#username',
                '#usuario'
            ]

            alias_input = None
            for selector in alias_selectors:
                try:
                    elemento = self.page.locator(selector).first
                    if elemento.is_visible(timeout=2000):
                        alias_input = elemento
                        logger.info(f"Campo alias encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not alias_input:
                # Buscar el primer input de texto en modal
                modal = self.page.locator('.modal:visible, .dialog:visible, [role="dialog"]:visible')
                if modal.count() > 0:
                    alias_input = modal.locator('input[type="text"]').first

            if not alias_input:
                raise Exception("No se encontró el campo de alias")

            alias_input.clear()
            alias_input.fill(alias)
            time.sleep(0.5)

            # Buscar campo de contraseña
            password_selectors = [
                'input[name="password"]',
                'input[name="pass"]',
                'input[name="contraseña"]',
                'input[type="password"]',
                'input[placeholder*="contraseña" i]',
                'input[placeholder*="password" i]',
                '#password',
                '#pass'
            ]

            password_input = None
            for selector in password_selectors:
                try:
                    elemento = self.page.locator(selector).first
                    if elemento.is_visible(timeout=2000):
                        password_input = elemento
                        logger.info(f"Campo password encontrado con selector: {selector}")
                        break
                except:
                    continue

            if not password_input:
                raise Exception("No se encontró el campo de contraseña")

            password_input.clear()
            password_input.fill(password)
            time.sleep(0.5)

            # Confirmar creación
            confirmar_selectors = [
                'button:has-text("crear")',
                'button:has-text("Crear")',
                'button:has-text("confirmar")',
                'button:has-text("guardar")',
                'button:has-text("aceptar")',
                'button[type="submit"]',
                '.btn-confirm',
                '.btn-success',
                '.btn-primary'
            ]

            for selector in confirmar_selectors:
                try:
                    confirmar = self.page.locator(selector).first
                    if confirmar.is_visible(timeout=2000):
                        confirmar.click()
                        logger.info(f"Click en confirmar con selector: {selector}")
                        break
                except:
                    continue

            time.sleep(3)
            self.page.wait_for_load_state('networkidle')

            logger.info(f"Usuario {alias} creado exitosamente")
            return {'success': True, 'message': f'Usuario {alias} creado exitosamente'}

        except Exception as e:
            logger.error(f"Error creando usuario: {e}")
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


    def ejecutar_descarga_completa(self, nombre_usuario, monto):
        """Ejecuta el proceso completo de descarga de fichas"""
        resultados = {
            'login': None,
            'busqueda': None,
            'seleccion': None,
            'descarga': None,
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

            # Descargar fichas
            resultados['descarga'] = self.descargar_fichas(monto)
            if not resultados['descarga']['success']:
                resultados['message'] = f"Error en descarga: {resultados['descarga']['message']}"
                return resultados

            resultados['success'] = True
            resultados['message'] = f"Descarga exitosa: {monto} fichas de {nombre_usuario}"
            return resultados

        except Exception as e:
            resultados['message'] = f"Error general: {str(e)}"
            return resultados

        finally:
            self.cerrar_navegador()

    def ejecutar_crear_usuario(self, alias, password):
        """Ejecuta el proceso completo de creación de usuario"""
        resultados = {
            'login': None,
            'creacion': None,
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

            # Crear usuario
            resultados['creacion'] = self.crear_usuario(alias, password)
            if not resultados['creacion']['success']:
                resultados['message'] = f"Error en creación: {resultados['creacion']['message']}"
                return resultados

            resultados['success'] = True
            resultados['message'] = f"Usuario {alias} creado exitosamente"
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
