/**
 * Smart Inventory Management System - Main JavaScript
 * Handles sidebar toggling, alerts, and UI interactions
 */

document.addEventListener('DOMContentLoaded', function () {

    // ============================================================
    // SIDEBAR TOGGLE
    // ============================================================
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.getElementById('sidebar');
    const mainContent = document.querySelector('.main-content');

    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function () {
            if (window.innerWidth <= 768) {
                // Mobile: show/hide sidebar with overlay
                sidebar.classList.toggle('mobile-open');
                // Create/toggle overlay
                let overlay = document.getElementById('sidebarOverlay');
                if (!overlay) {
                    overlay = document.createElement('div');
                    overlay.id = 'sidebarOverlay';
                    overlay.style.cssText = `
                        position: fixed; top: 0; left: 0; width: 100%; height: 100%;
                        background: rgba(0,0,0,0.5); z-index: 999;
                    `;
                    overlay.addEventListener('click', () => {
                        sidebar.classList.remove('mobile-open');
                        overlay.remove();
                    });
                    document.body.appendChild(overlay);
                } else {
                    overlay.remove();
                }
            } else {
                // Desktop: collapse/expand
                sidebar.classList.toggle('collapsed');
                if (mainContent) {
                    mainContent.style.marginLeft = sidebar.classList.contains('collapsed') ? '70px' : '260px';
                }
                // Save preference
                localStorage.setItem('sidebarCollapsed', sidebar.classList.contains('collapsed'));
            }
        });

        // Restore sidebar state from localStorage
        const wasCollapsed = localStorage.getItem('sidebarCollapsed') === 'true';
        if (wasCollapsed && window.innerWidth > 768) {
            sidebar.classList.add('collapsed');
            if (mainContent) mainContent.style.marginLeft = '70px';
        }
    }

    // ============================================================
    // AUTO-DISMISS ALERTS
    // ============================================================
    const alerts = document.querySelectorAll('.alert.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) bsAlert.close();
        }, 5000); // Auto-dismiss after 5 seconds
    });

    // ============================================================
    // CONFIRM DELETE DIALOGS
    // ============================================================
    document.querySelectorAll('[data-confirm]').forEach(el => {
        el.addEventListener('click', function (e) {
            const msg = this.dataset.confirm || 'Are you sure?';
            if (!confirm(msg)) e.preventDefault();
        });
    });

    // ============================================================
    // ACTIVE NAV ITEM HIGHLIGHTING
    // ============================================================
    const currentPath = window.location.pathname;
    document.querySelectorAll('.sidebar .nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href && href !== '/' && currentPath.startsWith(href)) {
            link.closest('.nav-item')?.classList.add('active');
        }
    });

    // ============================================================
    // FORM VALIDATION FEEDBACK
    // ============================================================
    const forms = document.querySelectorAll('form[novalidate]');
    forms.forEach(form => {
        form.addEventListener('submit', function (e) {
            if (!form.checkValidity()) {
                e.preventDefault();
                e.stopPropagation();
            }
            form.classList.add('was-validated');
        });
    });

    // ============================================================
    // NUMBER INPUT FORMATTING (prevent negative in quantity fields)
    // ============================================================
    document.querySelectorAll('input[type="number"][min="0"]').forEach(input => {
        input.addEventListener('change', function () {
            if (this.value < 0) this.value = 0;
        });
    });

    // ============================================================
    // TABLE ROW CLICK (navigate to detail on row click)
    // ============================================================
    document.querySelectorAll('tr[data-href]').forEach(row => {
        row.style.cursor = 'pointer';
        row.addEventListener('click', function () {
            window.location.href = this.dataset.href;
        });
    });

    // ============================================================
    // TOOLTIP INITIALIZATION
    // ============================================================
    const tooltipElements = document.querySelectorAll('[data-bs-toggle="tooltip"]');
    tooltipElements.forEach(el => new bootstrap.Tooltip(el));

    // ============================================================
    // RESPONSIVE TABLE: Horizontal scroll hint
    // ============================================================
    document.querySelectorAll('.table-responsive').forEach(wrapper => {
        if (wrapper.scrollWidth > wrapper.clientWidth) {
            wrapper.style.position = 'relative';
        }
    });

    // ============================================================
    // SEARCH: Clear button functionality
    // ============================================================
    const searchInput = document.getElementById('search-input');
    if (searchInput && searchInput.value) {
        const clearBtn = document.createElement('button');
        clearBtn.type = 'button';
        clearBtn.className = 'btn btn-sm btn-link position-absolute end-0 top-50 translate-middle-y me-2 text-muted';
        clearBtn.innerHTML = '<i class="bi bi-x-lg"></i>';
        clearBtn.addEventListener('click', () => {
            searchInput.value = '';
            searchInput.form.submit();
        });
        if (searchInput.parentElement) {
            searchInput.parentElement.style.position = 'relative';
            searchInput.parentElement.appendChild(clearBtn);
        }
    }

    // ============================================================
    // PRINT RECEIPT SHORTCUT
    // ============================================================
    document.addEventListener('keydown', function (e) {
        if ((e.ctrlKey || e.metaKey) && e.key === 'p') {
            // Let browser handle print normally
        }
    });

    console.log('%cSmartInventory Loaded ✓', 'color: #0d6efd; font-weight: bold; font-size: 14px;');
});

// ============================================================
// GLOBAL UTILITIES
// ============================================================

/**
 * Format a number as currency
 * @param {number} amount
 * @returns {string}
 */
function formatCurrency(amount) {
    return '$' + parseFloat(amount).toFixed(2).replace(/\B(?=(\d{3})+(?!\d))/g, ',');
}

/**
 * Show a toast notification
 * @param {string} message
 * @param {string} type - 'success', 'danger', 'warning', 'info'
 */
function showToast(message, type = 'info') {
    const container = document.querySelector('.messages-container') || document.querySelector('.page-content');
    if (!container) return;

    const alert = document.createElement('div');
    alert.className = `alert alert-${type} alert-dismissible fade show`;
    alert.innerHTML = `${message}<button type="button" class="btn-close" data-bs-dismiss="alert"></button>`;
    container.insertBefore(alert, container.firstChild);

    setTimeout(() => {
        const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
        if (bsAlert) bsAlert.close();
    }, 4000);
}
