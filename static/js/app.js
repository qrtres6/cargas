/**
 * Sistema de Carga de Fichas - Frontend JavaScript
 */

// ============== CONFIGURACIÓN ==============
const API_BASE = '';
const REFRESH_INTERVAL = 5000; // 5 segundos
const ESTIMATED_PROCESS_TIME = 15; // Tiempo estimado de carga en segundos (optimizado)

// ============== ESTADO DE LA APLICACIÓN ==============
let currentPage = 1;
const itemsPerPage = 10;
let processStartTimes = {}; // Almacena tiempos de inicio de procesos
let countdownInterval = null;

// ============== INICIALIZACIÓN ==============
document.addEventListener('DOMContentLoaded', () => {
    initForm();
    initFilters();
    loadData();
    startAutoRefresh();
});

// ============== FORMULARIOS ==============
function initForm() {
    // Formulario de Carga
    const cargaForm = document.getElementById('cargaForm');
    cargaForm.addEventListener('submit', (e) => handleFormSubmit(e, 'carga'));

    // Formulario de Descarga
    const descargaForm = document.getElementById('descargaForm');
    descargaForm.addEventListener('submit', (e) => handleFormSubmit(e, 'descarga'));
}

async function handleFormSubmit(e, tipo) {
    e.preventDefault();

    const isCarga = tipo === 'carga';
    const btn = document.getElementById(isCarga ? 'btnCarga' : 'btnDescarga');
    const btnText = btn.querySelector('.btn-text');
    const btnLoading = btn.querySelector('.btn-loading');
    const messageDiv = document.getElementById(isCarga ? 'cargaMessage' : 'descargaMessage');
    const usuarioField = document.getElementById(isCarga ? 'usuarioCarga' : 'usuarioDescarga');
    const montoField = document.getElementById(isCarga ? 'montoCarga' : 'montoDescarga');

    // Estado de carga
    btn.disabled = true;
    btnText.style.display = 'none';
    btnLoading.style.display = 'inline';
    messageDiv.style.display = 'none';

    // Obtener datos del formulario
    const formData = {
        usuario: usuarioField.value.trim(),
        monto: parseFloat(montoField.value),
        tipo: tipo
    };

    try {
        const response = await fetch(`${API_BASE}/api/cargar`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            const accion = isCarga ? 'Carga' : 'Descarga';
            showMessage(messageDiv, 'success',
                `${accion} agregada! ID: ${data.operacion_id}. Posición: ${data.posicion_cola}`);

            // Limpiar campos
            usuarioField.value = '';
            montoField.value = '';

            // Actualizar datos
            loadData();
        } else {
            showMessage(messageDiv, 'error', data.error || 'Error al procesar la solicitud');
        }

    } catch (error) {
        console.error('Error:', error);
        showMessage(messageDiv, 'error', 'Error de conexión con el servidor');
    } finally {
        // Restaurar botón
        btn.disabled = false;
        btnText.style.display = 'inline';
        btnLoading.style.display = 'none';
    }
}

function showMessage(element, type, message) {
    element.className = `message ${type}`;
    element.textContent = message;
    element.style.display = 'block';

    // Ocultar después de 5 segundos
    setTimeout(() => {
        element.style.display = 'none';
    }, 5000);
}

// ============== FILTROS ==============
function initFilters() {
    document.getElementById('filterEstado').addEventListener('change', () => {
        currentPage = 1;
        loadOperations();
    });

    document.getElementById('btnRefresh').addEventListener('click', loadData);
}

// ============== CARGA DE DATOS ==============
async function loadData() {
    await Promise.all([
        loadStats(),
        loadQueue(),
        loadOperations()
    ]);
}

async function loadStats() {
    try {
        const response = await fetch(`${API_BASE}/api/estadisticas`);
        const data = await response.json();

        if (data.success) {
            const stats = data.estadisticas;
            document.getElementById('statTotal').textContent = stats.total;
            document.getElementById('statCompletadas').textContent = stats.completadas;
            document.getElementById('statPendientes').textContent = stats.pendientes;
            document.getElementById('statEnProceso').textContent = stats.en_proceso;
            document.getElementById('statErrores').textContent = stats.errores;
            document.getElementById('statTotalFichas').textContent = formatNumber(stats.total_fichas_cargadas);
        }
    } catch (error) {
        console.error('Error cargando estadísticas:', error);
    }
}

async function loadQueue() {
    try {
        const response = await fetch(`${API_BASE}/api/cola`);
        const data = await response.json();

        if (data.success) {
            const queueList = document.getElementById('queueList');
            const queueStatus = document.querySelector('.queue-status');
            const queueStatusText = document.getElementById('queueStatusText');

            // Actualizar estado de la cola
            if (data.estado_procesamiento.procesando) {
                queueStatus.classList.add('active');
                queueStatusText.textContent = 'Procesando tarea...';
            } else if (data.cola.length > 0) {
                queueStatus.classList.add('active');
                queueStatusText.textContent = `${data.cola.length} tarea(s) en cola`;
            } else {
                queueStatus.classList.remove('active');
                queueStatusText.textContent = 'Sin tareas en proceso';
                // Limpiar tiempos de proceso
                processStartTimes = {};
            }

            // Renderizar cola
            if (data.cola.length === 0) {
                queueList.innerHTML = '<div class="empty-queue">No hay tareas pendientes</div>';
            } else {
                queueList.innerHTML = data.cola.map((op, index) => {
                    // Registrar tiempo de inicio si está en proceso (usar tiempo local)
                    if (op.estado === 'en_proceso' && !processStartTimes[op.id]) {
                        processStartTimes[op.id] = Date.now(); // Usar timestamp actual
                    }

                    // Calcular tiempo restante para la tarea actual
                    let tiempoInfo = '';
                    if (op.estado === 'en_proceso') {
                        tiempoInfo = `<span class="queue-item-countdown" data-id="${op.id}">Calculando...</span>`;
                    } else {
                        // Estimar tiempo de espera basado en posición en cola
                        const waitTime = index * ESTIMATED_PROCESS_TIME;
                        tiempoInfo = `<span class="queue-item-wait">~${waitTime}s de espera</span>`;
                    }

                    const tipoLabel = op.tipo === 'descarga' ? 'Descarga' : 'Carga';
                    return `
                        <div class="queue-item ${op.estado === 'en_proceso' ? 'processing' : ''}">
                            <div class="queue-item-info">
                                <span class="queue-item-user">${escapeHtml(op.usuario_destino)}</span>
                                <span class="queue-item-amount">${tipoLabel}: ${formatNumber(op.monto)} fichas</span>
                            </div>
                            <div class="queue-item-time">
                                ${tiempoInfo}
                                <span class="queue-item-status">
                                    ${op.estado === 'en_proceso' ? 'Procesando' : 'En cola'}
                                </span>
                            </div>
                        </div>
                    `;
                }).join('');

                // Iniciar contador
                startCountdown();
            }
        }
    } catch (error) {
        console.error('Error cargando cola:', error);
    }
}

function startCountdown() {
    // Limpiar intervalo anterior
    if (countdownInterval) {
        clearInterval(countdownInterval);
    }

    // Actualizar countdown cada segundo
    countdownInterval = setInterval(updateCountdowns, 1000);
    updateCountdowns(); // Actualizar inmediatamente
}

function updateCountdowns() {
    const countdowns = document.querySelectorAll('.queue-item-countdown');

    countdowns.forEach(el => {
        const id = el.dataset.id;
        const startTime = processStartTimes[id];

        if (startTime) {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            const remaining = Math.max(0, ESTIMATED_PROCESS_TIME - elapsed);

            if (remaining > 0) {
                el.textContent = `~${remaining}s restantes`;
                el.style.color = remaining < 5 ? '#4caf50' : '#ff9800';
            } else {
                el.textContent = 'Finalizando...';
                el.style.color = '#4caf50';
            }
        }
    });
}

async function loadOperations() {
    try {
        const estado = document.getElementById('filterEstado').value;
        let url = `${API_BASE}/api/operaciones?limite=${itemsPerPage}&pagina=${currentPage}`;
        if (estado) {
            url += `&estado=${estado}`;
        }

        const response = await fetch(url);
        const data = await response.json();

        if (data.success) {
            renderOperations(data.operaciones);
            renderPagination(data.total, data.pagina, data.limite);
        }
    } catch (error) {
        console.error('Error cargando operaciones:', error);
    }
}

function renderOperations(operations) {
    const tbody = document.getElementById('operationsBody');

    if (operations.length === 0) {
        tbody.innerHTML = `
            <tr>
                <td colspan="7" style="text-align: center; padding: 40px; color: var(--text-muted);">
                    No hay operaciones registradas
                </td>
            </tr>
        `;
        return;
    }

    tbody.innerHTML = operations.map(op => `
        <tr>
            <td><strong>#${op.id}</strong></td>
            <td><span class="tipo-badge ${op.tipo || 'carga'}">${formatTipo(op.tipo)}</span></td>
            <td>${escapeHtml(op.usuario_destino)}</td>
            <td><strong>${formatNumber(op.monto)}</strong></td>
            <td><span class="status-badge ${op.estado}">${formatStatus(op.estado)}</span></td>
            <td>${formatDate(op.fecha_creacion)}</td>
            <td title="${escapeHtml(op.mensaje || '')}">${truncate(op.mensaje || '-', 30)}</td>
        </tr>
    `).join('');
}

function formatTipo(tipo) {
    const tipoMap = {
        'carga': 'Carga',
        'descarga': 'Descarga'
    };
    return tipoMap[tipo] || 'Carga';
}

function renderPagination(total, page, limit) {
    const pagination = document.getElementById('pagination');
    const totalPages = Math.ceil(total / limit);

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';

    // Botón anterior
    if (page > 1) {
        html += `<button onclick="goToPage(${page - 1})">Anterior</button>`;
    }

    // Páginas
    for (let i = 1; i <= totalPages; i++) {
        if (i === page) {
            html += `<button class="active">${i}</button>`;
        } else if (Math.abs(i - page) <= 2 || i === 1 || i === totalPages) {
            html += `<button onclick="goToPage(${i})">${i}</button>`;
        } else if (Math.abs(i - page) === 3) {
            html += `<button disabled>...</button>`;
        }
    }

    // Botón siguiente
    if (page < totalPages) {
        html += `<button onclick="goToPage(${page + 1})">Siguiente</button>`;
    }

    pagination.innerHTML = html;
}

function goToPage(page) {
    currentPage = page;
    loadOperations();
}

// ============== AUTO REFRESH ==============
function startAutoRefresh() {
    setInterval(loadData, REFRESH_INTERVAL);
}

// ============== UTILIDADES ==============
function formatNumber(num) {
    return new Intl.NumberFormat('es-AR').format(num);
}

function formatDate(dateStr) {
    if (!dateStr) return '-';
    const date = new Date(dateStr);
    return date.toLocaleString('es-AR', {
        timeZone: 'America/Argentina/Buenos_Aires',
        day: '2-digit',
        month: '2-digit',
        year: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function formatStatus(status) {
    const statusMap = {
        'pendiente': 'Pendiente',
        'en_proceso': 'En Proceso',
        'completada': 'Completada',
        'error': 'Error'
    };
    return statusMap[status] || status;
}

function escapeHtml(text) {
    if (!text) return '';
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function truncate(text, length) {
    if (!text || text.length <= length) return text;
    return text.substring(0, length) + '...';
}
