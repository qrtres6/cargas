/**
 * Gana en Casa - Sistema de Gestión - Frontend JavaScript
 */

// ============== CONFIGURACIÓN ==============
const API_BASE = '';
const REFRESH_INTERVAL = 5000; // 5 segundos

// ============== ESTADO DE LA APLICACIÓN ==============
let currentPage = 1;
const itemsPerPage = 10;

// ============== INICIALIZACIÓN ==============
document.addEventListener('DOMContentLoaded', () => {
    initForms();
    initFilters();
    loadData();
    startAutoRefresh();
});

// ============== FORMULARIOS ==============
function initForms() {
    // Formulario de Carga
    document.getElementById('cargaForm').addEventListener('submit', handleCargaSubmit);

    // Formulario de Descarga
    document.getElementById('descargaForm').addEventListener('submit', handleDescargaSubmit);

    // Formulario de Crear Usuario
    document.getElementById('crearUsuarioForm').addEventListener('submit', handleCrearUsuarioSubmit);

    // Botón generar contraseña
    document.getElementById('btnGenerarPass').addEventListener('click', generarPassword);

    // Formulario de Buscar Retiros
    document.getElementById('buscarRetirosForm').addEventListener('submit', handleBuscarRetiros);
}

// ============== CARGAR FICHAS ==============
async function handleCargaSubmit(e) {
    e.preventDefault();

    const btn = document.getElementById('btnCargar');
    const messageDiv = document.getElementById('cargaMessage');

    setButtonLoading(btn, true);
    messageDiv.style.display = 'none';

    const formData = {
        usuario: document.getElementById('usuarioCarga').value.trim(),
        monto: parseFloat(document.getElementById('montoCarga').value)
    };

    try {
        const response = await fetch(`${API_BASE}/api/cargar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            showMessage(messageDiv, 'success', `Carga agregada! ID: ${data.operacion_id}`);
            document.getElementById('usuarioCarga').value = '';
            document.getElementById('montoCarga').value = '';
            loadData();
        } else {
            showMessage(messageDiv, 'error', data.error || 'Error al procesar');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage(messageDiv, 'error', 'Error de conexión');
    } finally {
        setButtonLoading(btn, false);
    }
}

// ============== DESCARGAR FICHAS ==============
async function handleDescargaSubmit(e) {
    e.preventDefault();

    const btn = document.getElementById('btnDescargar');
    const messageDiv = document.getElementById('descargaMessage');

    setButtonLoading(btn, true);
    messageDiv.style.display = 'none';

    const formData = {
        usuario: document.getElementById('usuarioDescarga').value.trim(),
        monto: parseFloat(document.getElementById('montoDescarga').value)
    };

    try {
        const response = await fetch(`${API_BASE}/api/descargar`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            showMessage(messageDiv, 'success', `Descarga agregada! ID: ${data.operacion_id}`);
            document.getElementById('usuarioDescarga').value = '';
            document.getElementById('montoDescarga').value = '';
            loadData();
        } else {
            showMessage(messageDiv, 'error', data.error || 'Error al procesar');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage(messageDiv, 'error', 'Error de conexión');
    } finally {
        setButtonLoading(btn, false);
    }
}

// ============== CREAR USUARIO ==============
async function handleCrearUsuarioSubmit(e) {
    e.preventDefault();

    const btn = document.getElementById('btnCrearUsuario');
    const messageDiv = document.getElementById('crearUsuarioMessage');

    setButtonLoading(btn, true);
    messageDiv.style.display = 'none';

    const formData = {
        alias: document.getElementById('aliasUsuario').value.trim(),
        password: document.getElementById('passwordUsuario').value.trim()
    };

    try {
        const response = await fetch(`${API_BASE}/api/crear-usuario`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(formData)
        });

        const data = await response.json();

        if (data.success) {
            showMessage(messageDiv, 'success', `Usuario agregado a cola! ID: ${data.operacion_id}`);
            document.getElementById('aliasUsuario').value = '';
            document.getElementById('passwordUsuario').value = '';
            loadData();
        } else {
            showMessage(messageDiv, 'error', data.error || 'Error al procesar');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage(messageDiv, 'error', 'Error de conexión');
    } finally {
        setButtonLoading(btn, false);
    }
}

// ============== GENERAR CONTRASEÑA ==============
function generarPassword() {
    const chars = '0123456789';
    let password = '';
    for (let i = 0; i < 6; i++) {
        password += chars.charAt(Math.floor(Math.random() * chars.length));
    }
    document.getElementById('passwordUsuario').value = password;
}

// ============== BUSCAR RETIROS ==============
async function handleBuscarRetiros(e) {
    e.preventDefault();

    const btn = document.getElementById('btnBuscarRetiros');
    const messageDiv = document.getElementById('buscarRetirosMessage');

    setButtonLoading(btn, true);
    messageDiv.style.display = 'none';

    const usuario = document.getElementById('usuarioBuscar').value.trim();

    // Filtrar operaciones por tipo descarga y usuario
    try {
        let url = `${API_BASE}/api/operaciones?limite=50`;

        const response = await fetch(url);
        const data = await response.json();

        if (data.success) {
            // Filtrar solo descargas del usuario
            const retiros = data.operaciones.filter(op =>
                op.tipo === 'descarga' &&
                (!usuario || op.usuario_destino.toLowerCase().includes(usuario.toLowerCase()))
            );

            if (retiros.length > 0) {
                showMessage(messageDiv, 'success', `Se encontraron ${retiros.length} retiros`);
            } else {
                showMessage(messageDiv, 'info', 'No se encontraron retiros');
            }
        } else {
            showMessage(messageDiv, 'error', data.error || 'Error al buscar');
        }
    } catch (error) {
        console.error('Error:', error);
        showMessage(messageDiv, 'error', 'Error de conexión');
    } finally {
        setButtonLoading(btn, false);
    }
}

// ============== UTILIDADES DE UI ==============
function setButtonLoading(btn, loading) {
    const btnText = btn.querySelector('.btn-text');
    const btnLoading = btn.querySelector('.btn-loading');

    btn.disabled = loading;
    btnText.style.display = loading ? 'none' : 'inline';
    btnLoading.style.display = loading ? 'inline' : 'none';
}

function showMessage(element, type, message) {
    element.className = `message ${type}`;
    element.textContent = message;
    element.style.display = 'block';

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
            document.getElementById('statTotalCargado').textContent = '$ ' + formatNumber(stats.total_cargado);
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

            if (data.estado_procesamiento.procesando) {
                queueStatus.classList.add('active');
                queueStatusText.textContent = 'Procesando tarea...';
            } else if (data.cola.length > 0) {
                queueStatus.classList.add('active');
                queueStatusText.textContent = `${data.cola.length} tarea(s) en cola`;
            } else {
                queueStatus.classList.remove('active');
                queueStatusText.textContent = 'Sin tareas en proceso';
            }

            if (data.cola.length === 0) {
                queueList.innerHTML = '<div class="empty-queue">No hay tareas pendientes</div>';
            } else {
                queueList.innerHTML = data.cola.map(op => `
                    <div class="queue-item ${op.estado === 'en_proceso' ? 'processing' : ''}">
                        <div class="queue-item-info">
                            <span class="queue-item-type ${op.tipo || 'carga'}">${formatTipo(op.tipo || 'carga')}</span>
                            <span class="queue-item-user">${escapeHtml(op.usuario_destino)}</span>
                            <span class="queue-item-amount">${op.monto ? formatNumber(op.monto) + ' fichas' : ''}</span>
                        </div>
                        <span class="queue-item-status">
                            ${op.estado === 'en_proceso' ? 'Procesando' : 'En cola'}
                        </span>
                    </div>
                `).join('');
            }
        }
    } catch (error) {
        console.error('Error cargando cola:', error);
    }
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
            <td><span class="type-badge ${op.tipo || 'carga'}">${formatTipo(op.tipo || 'carga')}</span></td>
            <td>${escapeHtml(op.usuario_destino)}</td>
            <td><strong>${op.monto ? '$ ' + formatNumber(op.monto) : '-'}</strong></td>
            <td><span class="status-badge ${op.estado}">${formatStatus(op.estado)}</span></td>
            <td>${formatDate(op.fecha_creacion)}</td>
            <td title="${escapeHtml(op.mensaje || '')}">${truncate(op.mensaje || '-', 30)}</td>
        </tr>
    `).join('');
}

function renderPagination(total, page, limit) {
    const pagination = document.getElementById('pagination');
    const totalPages = Math.ceil(total / limit);

    if (totalPages <= 1) {
        pagination.innerHTML = '';
        return;
    }

    let html = '';

    if (page > 1) {
        html += `<button onclick="goToPage(${page - 1})">Anterior</button>`;
    }

    for (let i = 1; i <= totalPages; i++) {
        if (i === page) {
            html += `<button class="active">${i}</button>`;
        } else if (Math.abs(i - page) <= 2 || i === 1 || i === totalPages) {
            html += `<button onclick="goToPage(${i})">${i}</button>`;
        } else if (Math.abs(i - page) === 3) {
            html += `<button disabled>...</button>`;
        }
    }

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

function formatTipo(tipo) {
    const tipoMap = {
        'carga': 'CARGA',
        'descarga': 'DESCARGA',
        'crear_usuario': 'CREAR'
    };
    return tipoMap[tipo] || tipo.toUpperCase();
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
