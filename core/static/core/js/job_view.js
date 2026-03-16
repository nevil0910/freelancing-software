// ============================================================
// Utility: Indian currency format
// ============================================================
function formatINR(amount) {
    const num = parseFloat(amount);
    if (num < 1000) return `₹${num.toFixed(0)}`;
    if (num < 100000) {
        const t = num / 1000;
        return `₹${t % 1 === 0 ? t.toFixed(0) : t.toFixed(1)}k`;
    }
    if (num < 10000000) {
        const l = num / 100000;
        return `₹${l % 1 === 0 ? l.toFixed(0) : l.toFixed(2)} L`;
    }
    const c = num / 10000000;
    return `₹${c % 1 === 0 ? c.toFixed(0) : c.toFixed(2)} Cr`;
}

document.querySelectorAll('.budget[data-amount]').forEach(function (el) {
    el.textContent = formatINR(el.getAttribute('data-amount'));
});

const config = window.jobViewConfig || {
    userType: '',
    canApply: false,
    isClient: false,
    applyUrl: '',
};

// ============================================================
// Utility: Get CSRF token
// ============================================================
function getCsrf() {
    const el = document.querySelector('#csrfForm [name=csrfmiddlewaretoken]');
    return el ? el.value : '';
}

// ============================================================
// Modal helpers
// ============================================================
function openModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}
function closeModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.remove('active');
    document.body.style.overflow = '';
}

// Close on overlay click
document.querySelectorAll('.modal-overlay').forEach(function (overlay) {
    overlay.addEventListener('click', function (e) {
        if (e.target === overlay) closeModal(overlay.id);
    });
});

// Close on Escape key
document.addEventListener('keydown', function (e) {
    if (e.key === 'Escape') {
        document.querySelectorAll('.modal-overlay.active').forEach(function (m) {
            closeModal(m.id);
        });
    }
});

// ============================================================
// Apply modal (freelancer)
// ============================================================
if (config.canApply) {
    const openApplyBtn = document.getElementById('openApplyModal');
    if (openApplyBtn) {
        openApplyBtn.addEventListener('click', function () {
            openModal('applyModal');
        });
    }

    const closeApplyBtn = document.getElementById('closeApplyModal');
    if (closeApplyBtn) {
        closeApplyBtn.addEventListener('click', function () {
            closeModal('applyModal');
        });
    }

    const cancelApplyBtn = document.getElementById('cancelApplyBtn');
    if (cancelApplyBtn) {
        cancelApplyBtn.addEventListener('click', function () {
            closeModal('applyModal');
        });
    }

    const submitApplyBtn = document.getElementById('submitApplyBtn');
    if (submitApplyBtn) {
        submitApplyBtn.addEventListener('click', function () {
            const messageInput = document.getElementById('applyMessage');
            const alertEl = document.getElementById('applyAlert');
            const submitBtn = document.getElementById('submitApplyBtn');
            if (!messageInput || !alertEl || !submitBtn || !config.applyUrl) return;

            const message = messageInput.value.trim();

            if (!message) {
                alertEl.className = 'modal-alert error';
                alertEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> Please write a cover message before submitting.';
                return;
            }

            submitBtn.disabled = true;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Submitting...';
            alertEl.className = 'modal-alert';
            alertEl.innerHTML = '';

            fetch(config.applyUrl, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': getCsrf(),
                },
                body: 'message=' + encodeURIComponent(message),
            })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.success) {
                        alertEl.className = 'modal-alert success';
                        alertEl.innerHTML = '<i class="fas fa-check-circle"></i> ' + data.message;
                        submitBtn.innerHTML = '<i class="fas fa-check"></i> Submitted!';
                        // Reload after short delay to show updated state
                        setTimeout(function () { location.reload(); }, 1400);
                    } else {
                        alertEl.className = 'modal-alert error';
                        alertEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + data.error;
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Application';
                    }
                })
                .catch(function () {
                    alertEl.className = 'modal-alert error';
                    alertEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> Something went wrong. Please try again.';
                    submitBtn.disabled = false;
                    submitBtn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Application';
                });
        });
    }
}

// ============================================================
// Applications modal (client)
// ============================================================
if (config.isClient) {
    const openApplicationsBtn = document.getElementById('openApplicationsModal');
    if (openApplicationsBtn) {
        openApplicationsBtn.addEventListener('click', function () {
            openModal('applicationsModal');
        });
    }

    const closeApplicationsBtn = document.getElementById('closeApplicationsModal');
    if (closeApplicationsBtn) {
        closeApplicationsBtn.addEventListener('click', function () {
            closeModal('applicationsModal');
        });
    }

    window.handleApplication = function (appId, action) {
        const url = action === 'accept'
            ? '/application/' + appId + '/accept/'
            : '/application/' + appId + '/reject/';

        const acceptBtn = document.getElementById('acceptBtn' + appId);
        const rejectBtn = document.getElementById('rejectBtn' + appId);
        const alertEl = document.getElementById('appActionAlert');
        if (!alertEl) return;

        if (acceptBtn) acceptBtn.disabled = true;
        if (rejectBtn) rejectBtn.disabled = true;

        fetch(url, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCsrf(),
            },
        })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                if (data.success) {
                    const item = document.getElementById('appItem' + appId);
                    const statusBadge = document.getElementById('appStatus' + appId);
                    if (!item || !statusBadge) return;

                    // Update status badge
                    statusBadge.className = 'app-status-badge app-status-' + data.status.toLowerCase();
                    statusBadge.textContent = data.status.charAt(0) + data.status.slice(1).toLowerCase();

                    // Update item class
                    item.classList.remove('pending');
                    item.classList.add(data.status.toLowerCase());

                    // Remove action buttons
                    if (acceptBtn) acceptBtn.remove();
                    if (rejectBtn) rejectBtn.remove();

                    // Show success
                    alertEl.className = 'modal-alert success';
                    alertEl.innerHTML = '<i class="fas fa-check-circle"></i> ' + data.message;
                    setTimeout(function () {
                        alertEl.className = 'modal-alert';
                        alertEl.innerHTML = '';
                    }, 3000);
                } else {
                    alertEl.className = 'modal-alert error';
                    alertEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + data.error;
                    if (acceptBtn) acceptBtn.disabled = false;
                    if (rejectBtn) rejectBtn.disabled = false;
                }
            })
            .catch(function () {
                alertEl.className = 'modal-alert error';
                alertEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> Something went wrong. Please try again.';
                if (acceptBtn) acceptBtn.disabled = false;
                if (rejectBtn) rejectBtn.disabled = false;
            });
    };
}

// ============================================================
// Set min date on deadline input (client edit form)
// ============================================================
const deadlineInput = document.querySelector('input[name="deadline"]');
if (deadlineInput) {
    const today = new Date().toISOString().split('T')[0];
    deadlineInput.setAttribute('min', today);
}