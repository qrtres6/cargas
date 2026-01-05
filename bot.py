"""
Bot de automatización para carga de fichas en AgentesNet
Utiliza Playwright para automatizar el navegador
Selectores actualizados para Vuetify (Vue.js)
OPTIMIZADO: Tiempos reducidos y sesión persistente
"""

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
from config import Config
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentesNetBot:
    """Bot para automatizar carga de fichas en agentesbet.net"""

    # Instancia compartida para reutilizar sesión
    _instance = None
    _browser = None
    _page = None
    _logged_in = False
    _last_activity = None  # Timestamp de última actividad

    def __init__(self, headless=None):
        self.headless = headless if headless is not None else Config.HEADLESS
        self.timeout = Config.TIMEOUT

    def iniciar_navegador(self):
        """Inicia el navegador Playwright (reutiliza si ya existe)"""
        if AgentesNetBot._browser and AgentesNetBot._page:
            logger.info("Reutilizando navegador existente")
            self.browser = AgentesNetBot._browser
            self.page = AgentesNetBot._page
            return

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

        # Guardar referencia global
        AgentesNetBot._browser = self.browser
        AgentesNetBot._page = self.page
        AgentesNetBot._playwright = self.playwright

        logger.info("Navegador iniciado correctamente")

    def cerrar_navegador(self):
        """Cierra el navegador (solo si hay error, sino mantiene sesión)"""
        pass  # No cerrar para reutilizar

    def forzar_cierre_navegador(self):
        """Fuerza el cierre del navegador (maneja errores de threading)"""
        if AgentesNetBot._browser:
            try:
                AgentesNetBot._browser.close()
            except Exception as e:
                logger.warning(f"Error cerrando browser (puede ser de otro thread): {e}")
            try:
                AgentesNetBot._playwright.stop()
            except Exception as e:
                logger.warning(f"Error deteniendo playwright: {e}")
            # Siempre limpiar las referencias
            AgentesNetBot._browser = None
            AgentesNetBot._page = None
            AgentesNetBot._logged_in = False
            AgentesNetBot._last_activity = None
            AgentesNetBot._playwright = None
            logger.info("Referencias del navegador limpiadas")

    @classmethod
    def is_logged_in(cls):
        """Verifica si está logueado actualmente"""
        return cls._logged_in and cls._browser is not None

    @classmethod
    def force_logout(cls):
        """Fuerza el cierre de sesión (maneja errores de threading)"""
        if cls._browser:
            try:
                cls._browser.close()
            except Exception as e:
                logger.warning(f"Error cerrando browser en logout: {e}")
            try:
                if cls._playwright:
                    cls._playwright.stop()
            except Exception as e:
                logger.warning(f"Error deteniendo playwright en logout: {e}")
        # Siempre limpiar referencias
        cls._browser = None
        cls._page = None
        cls._logged_in = False
        cls._last_activity = None
        cls._playwright = None
        logger.info("Sesión cerrada forzadamente")
        return {'success': True, 'message': 'Sesión cerrada'}

    def force_login(self):
        """Fuerza un nuevo login"""
        # Primero cerrar sesión existente
        AgentesNetBot.force_logout()
        # Iniciar navegador y hacer login
        self.iniciar_navegador()
        return self.login()

    def verificar_sesion(self):
        """Verifica si la sesión sigue activa y hace refresh si es necesario"""
        try:
            # Si pasaron más de 60 segundos desde la última actividad, verificar sesión
            if AgentesNetBot._last_activity:
                tiempo_inactivo = time.time() - AgentesNetBot._last_activity
                if tiempo_inactivo > 60:
                    logger.info(f"Verificando sesión después de {int(tiempo_inactivo)}s de inactividad")
                    # Refrescar la página para mantener sesión
                    self.page.reload(wait_until='domcontentloaded', timeout=15000)
                    time.sleep(1)

            # Verificar que seguimos logueados
            search_field = self.page.locator('input[placeholder="Buscar usuario"]')
            if search_field.is_visible(timeout=3000):
                AgentesNetBot._last_activity = time.time()
                return True
            return False
        except Exception as e:
            logger.warning(f"Error verificando sesión: {e}")
            return False

    def login(self):
        """Realiza el login en AgentesNet (salta si ya está logueado)"""
        # Verificar si ya está logueado
        if AgentesNetBot._logged_in:
            try:
                # Verificar y refrescar sesión si es necesario
                if self.verificar_sesion():
                    logger.info("Sesión activa verificada")
                    return {'success': True, 'message': 'Sesión existente'}
                else:
                    logger.info("Sesión expirada, relogueando...")
                    AgentesNetBot._logged_in = False
            except:
                AgentesNetBot._logged_in = False

        try:
            logger.info(f"Navegando a {Config.AGENTES_URL}")
            self.page.goto(Config.AGENTES_URL, wait_until='domcontentloaded', timeout=30000)

            # Esperar mínimo a que cargue
            time.sleep(0.5)

            # Campo de Alias (usuario)
            alias_input = self.page.locator('input[placeholder="Alias"]')
            alias_input.wait_for(state='visible', timeout=10000)
            alias_input.fill(Config.AGENTES_USER)

            # Campo de Contraseña
            password_input = self.page.locator('input[placeholder="Contraseña"]')
            password_input.wait_for(state='visible', timeout=5000)
            password_input.fill(Config.AGENTES_PASSWORD)

            # Botón Iniciar sesión
            login_btn = self.page.locator('button:has-text("Iniciar sesión")')
            login_btn.wait_for(state='visible', timeout=5000)
            login_btn.click()
            logger.info("Click en botón Iniciar sesión")

            # Esperar a que complete el login
            time.sleep(1)

            # Verificar si el login fue exitoso
            search_field = self.page.locator('input[placeholder="Buscar usuario"]')
            search_field.wait_for(state='visible', timeout=15000)
            AgentesNetBot._logged_in = True
            AgentesNetBot._last_activity = time.time()
            logger.info("Login exitoso")
            return {'success': True, 'message': 'Login exitoso'}

        except PlaywrightTimeout as e:
            logger.error(f"Timeout durante login: {e}")
            return {'success': False, 'message': f'Timeout: {str(e)}'}
        except Exception as e:
            logger.error(f"Error durante login: {e}")
            return {'success': False, 'message': str(e)}

    def buscar_usuario(self, nombre_usuario):
        """Busca un usuario en el sistema (optimizado)"""
        try:
            logger.info(f"Buscando usuario: {nombre_usuario}")

            # Campo de búsqueda
            search_input = self.page.locator('input[placeholder="Buscar usuario"]')
            search_input.wait_for(state='visible', timeout=5000)
            search_input.clear()
            search_input.fill(nombre_usuario)

            time.sleep(0.3)

            # Click en la lupa
            lupa_btn = self.page.locator('button:has(i.mdi-magnify)')
            lupa_btn.wait_for(state='visible', timeout=5000)
            lupa_btn.click()

            time.sleep(0.3)

            # Seleccionar "Todos los jugadores"
            todos_jugadores = self.page.locator('text="Todos los jugadores"')
            todos_jugadores.wait_for(state='visible', timeout=5000)
            todos_jugadores.click()

            time.sleep(0.5)

            logger.info(f"Búsqueda de usuario {nombre_usuario} completada")
            return {'success': True, 'message': f'Usuario {nombre_usuario} buscado'}

        except PlaywrightTimeout as e:
            logger.error(f"Timeout buscando usuario: {e}")
            return {'success': False, 'message': f'Timeout: {str(e)}'}
        except Exception as e:
            logger.error(f"Error buscando usuario: {e}")
            return {'success': False, 'message': str(e)}

    def encontrar_usuario_en_lista(self, nombre_usuario):
        """Encuentra y selecciona al usuario en la lista (optimizado)"""
        try:
            logger.info(f"Buscando {nombre_usuario} en resultados...")
            time.sleep(0.5)

            # Buscar directamente por texto
            usuario_elemento = self.page.locator(f'text="{nombre_usuario}"').first
            usuario_elemento.wait_for(state='visible', timeout=5000)
            usuario_elemento.click()

            time.sleep(0.3)
            logger.info(f"Usuario {nombre_usuario} seleccionado")
            return {'success': True, 'message': f'Usuario {nombre_usuario} encontrado'}

        except Exception as e:
            logger.error(f"Error encontrando usuario: {e}")
            return {'success': False, 'message': str(e)}

    def cargar_fichas(self, monto):
        """Carga fichas al usuario seleccionado (optimizado)"""
        try:
            logger.info(f"Cargando {monto} fichas...")

            # Click en botón de cargar
            cargar_btn = self.page.locator('button:has(i.mdi-cash-plus)')
            cargar_btn.wait_for(state='visible', timeout=5000)
            cargar_btn.first.click()

            time.sleep(1)

            # Buscar campo de monto
            monto_input = self.page.locator('input[placeholder="10"]')
            monto_input.wait_for(state='visible', timeout=5000)

            # Triple click y escribir
            monto_input.click(click_count=3)
            time.sleep(0.1)
            monto_input.type(str(int(monto)))

            time.sleep(0.2)

            # Click en Enviar
            enviar_btn = self.page.locator('button:has-text("Enviar")')
            enviar_btn.wait_for(state='visible', timeout=5000)
            enviar_btn.click()

            time.sleep(1)

            logger.info(f"Carga de {monto} fichas completada")
            return {'success': True, 'message': f'Carga de {monto} fichas completada'}

        except PlaywrightTimeout as e:
            logger.error(f"Timeout cargando fichas: {e}")
            return {'success': False, 'message': f'Timeout: {str(e)}'}
        except Exception as e:
            logger.error(f"Error cargando fichas: {e}")
            return {'success': False, 'message': str(e)}

    def descargar_fichas(self, monto):
        """Descarga fichas del usuario seleccionado"""
        try:
            logger.info(f"Descargando {monto} fichas...")

            # Click en botón de descargar (mdi-cash-minus)
            descargar_btn = self.page.locator('button:has(i.mdi-cash-minus)')
            descargar_btn.wait_for(state='visible', timeout=5000)
            descargar_btn.first.click()

            time.sleep(1)

            # Buscar campo de monto
            monto_input = self.page.locator('input[placeholder="10"]')
            monto_input.wait_for(state='visible', timeout=5000)

            # Triple click y escribir
            monto_input.click(click_count=3)
            time.sleep(0.1)
            monto_input.type(str(int(monto)))

            time.sleep(0.2)

            # Click en Enviar
            enviar_btn = self.page.locator('button:has-text("Enviar")')
            enviar_btn.wait_for(state='visible', timeout=5000)
            enviar_btn.click()

            time.sleep(1)

            logger.info(f"Descarga de {monto} fichas completada")
            return {'success': True, 'message': f'Descarga de {monto} fichas completada'}

        except PlaywrightTimeout as e:
            logger.error(f"Timeout descargando fichas: {e}")
            return {'success': False, 'message': f'Timeout: {str(e)}'}
        except Exception as e:
            logger.error(f"Error descargando fichas: {e}")
            return {'success': False, 'message': str(e)}

    def crear_jugador(self, alias, password):
        """Crea un nuevo jugador en AgentesNet"""
        try:
            logger.info(f"Creando jugador: {alias}")

            # Click en botón "Crear jugador"
            crear_btn = self.page.locator('button.bg-secondary:has-text("Crear jugador")')
            crear_btn.wait_for(state='visible', timeout=5000)
            crear_btn.click()

            time.sleep(0.5)

            # Esperar modal y llenar campos
            alias_input = self.page.locator('input[placeholder="Alias"]').last
            alias_input.wait_for(state='visible', timeout=5000)
            alias_input.fill(alias)

            password_input = self.page.locator('input[placeholder="password_placeholder"]')
            password_input.wait_for(state='visible', timeout=3000)
            password_input.fill(password)

            time.sleep(0.3)

            # Click en Guardar
            guardar_btn = self.page.locator('button.bg-primary:has-text("Guardar")')
            guardar_btn.wait_for(state='visible', timeout=3000)
            guardar_btn.click()

            time.sleep(1)

            # Verificar si hay error de alias duplicado
            try:
                error_msg = self.page.locator('.v-snackbar__content:has-text("Duplicated alias")')
                if error_msg.is_visible(timeout=2000):
                    logger.warning(f"Alias {alias} ya existe")
                    # Cerrar modal si sigue abierto
                    try:
                        close_btn = self.page.locator('button:has(i.mdi-close)').first
                        if close_btn.is_visible(timeout=1000):
                            close_btn.click()
                    except:
                        pass
                    return {'success': False, 'message': 'Alias duplicado', 'duplicado': True}
            except:
                pass

            # Verificar éxito - el modal debe desaparecer
            try:
                modal_cerrado = self.page.locator('input[placeholder="password_placeholder"]')
                modal_cerrado.wait_for(state='hidden', timeout=3000)
                logger.info(f"Jugador {alias} creado exitosamente")
                return {'success': True, 'message': f'Jugador {alias} creado exitosamente'}
            except:
                # Si el modal sigue visible, hubo algún error
                return {'success': False, 'message': 'Error desconocido al crear jugador', 'duplicado': False}

        except PlaywrightTimeout as e:
            logger.error(f"Timeout creando jugador: {e}")
            return {'success': False, 'message': f'Timeout: {str(e)}', 'duplicado': False}
        except Exception as e:
            logger.error(f"Error creando jugador: {e}")
            return {'success': False, 'message': str(e), 'duplicado': False}

    def ejecutar_creacion_usuario(self, alias, password):
        """Ejecuta el proceso completo de creación de usuario con reintentos"""
        resultados = {
            'login': None,
            'creacion': None,
            'success': False,
            'message': '',
            'alias_final': alias
        }

        # Siempre cerrar sesión previa para evitar problemas de threading
        self.forzar_cierre_navegador()

        try:
            self.iniciar_navegador()

            # Login
            resultados['login'] = self.login()
            if not resultados['login']['success']:
                resultados['message'] = f"Error en login: {resultados['login']['message']}"
                self.forzar_cierre_navegador()
                return resultados

            # Intentar crear usuario
            alias_actual = alias
            intentos = 0
            max_intentos = 10

            while intentos < max_intentos:
                resultados['creacion'] = self.crear_jugador(alias_actual, password)

                if resultados['creacion']['success']:
                    resultados['success'] = True
                    resultados['alias_final'] = alias_actual
                    resultados['message'] = f'Usuario {alias_actual} creado exitosamente'
                    if alias_actual != alias:
                        resultados['message'] += f' (alias original "{alias}" no disponible)'
                    AgentesNetBot._last_activity = time.time()
                    return resultados

                # Si el alias está duplicado, agregar número
                if resultados['creacion'].get('duplicado'):
                    intentos += 1
                    alias_actual = f"{alias}{intentos}"
                    logger.info(f"Intentando con alias alternativo: {alias_actual}")
                    time.sleep(0.5)
                else:
                    # Error no relacionado con duplicado
                    resultados['message'] = f"Error creando usuario: {resultados['creacion']['message']}"
                    return resultados

            resultados['message'] = f"No se pudo crear usuario después de {max_intentos} intentos"
            return resultados

        except Exception as e:
            resultados['message'] = f"Error general: {str(e)}"
            self.forzar_cierre_navegador()
            return resultados

    def ejecutar_carga_completa(self, nombre_usuario, monto, tipo='carga'):
        """Ejecuta el proceso completo de carga/descarga de fichas"""
        resultados = {
            'login': None,
            'busqueda': None,
            'seleccion': None,
            'operacion': None,
            'success': False,
            'message': ''
        }

        # Siempre cerrar sesión previa para evitar problemas de threading
        self.forzar_cierre_navegador()

        max_reintentos = 2
        for intento in range(max_reintentos):
            try:
                self.iniciar_navegador()

                # Login (siempre hacer login fresco)
                resultados['login'] = self.login()
                if not resultados['login']['success']:
                    resultados['message'] = f"Error en login: {resultados['login']['message']}"
                    self.forzar_cierre_navegador()
                    if intento < max_reintentos - 1:
                        logger.info(f"Reintentando... (intento {intento + 2}/{max_reintentos})")
                        time.sleep(2)
                        continue
                    return resultados

                # Buscar usuario
                resultados['busqueda'] = self.buscar_usuario(nombre_usuario)
                if not resultados['busqueda']['success']:
                    # Si falla búsqueda, probablemente sesión expirada
                    resultados['message'] = f"Error en búsqueda: {resultados['busqueda']['message']}"
                    if intento < max_reintentos - 1:
                        logger.info("Sesión posiblemente expirada, reiniciando...")
                        self.forzar_cierre_navegador()
                        time.sleep(2)
                        continue
                    return resultados

                # Encontrar usuario en lista
                resultados['seleccion'] = self.encontrar_usuario_en_lista(nombre_usuario)
                if not resultados['seleccion']['success']:
                    resultados['message'] = f"Usuario '{nombre_usuario}' no encontrado en AgentesNet"
                    return resultados

                # Cargar o descargar fichas según tipo
                if tipo == 'descarga':
                    resultados['operacion'] = self.descargar_fichas(monto)
                    accion = 'Descarga'
                else:
                    resultados['operacion'] = self.cargar_fichas(monto)
                    accion = 'Carga'

                if not resultados['operacion']['success']:
                    resultados['message'] = f"Error en {accion.lower()}: {resultados['operacion']['message']}"
                    return resultados

                resultados['success'] = True
                resultados['message'] = f"{accion} exitosa: {monto} fichas {'de' if tipo == 'descarga' else 'a'} {nombre_usuario}"
                AgentesNetBot._last_activity = time.time()
                return resultados

            except Exception as e:
                logger.error(f"Error en intento {intento + 1}: {str(e)}")
                self.forzar_cierre_navegador()
                if intento < max_reintentos - 1:
                    logger.info(f"Reintentando después de error... (intento {intento + 2}/{max_reintentos})")
                    time.sleep(2)
                    continue
                resultados['message'] = f"Error general: {str(e)}"
                return resultados

        return resultados


# Para pruebas directas
if __name__ == "__main__":
    bot = AgentesNetBot(headless=False)
    resultado = bot.ejecutar_carga_completa("usuario_test", 100)
    print(resultado)
