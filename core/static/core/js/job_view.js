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

// ============================================================
// Review Popup (client only, COMPLETED jobs without review)
// ============================================================
if (config.showReview) {
    const reviewModal = document.getElementById('reviewModal');
    if (reviewModal) {
        // Auto-show the review modal
        openModal('reviewModal');

        // Star rating
        const stars = document.querySelectorAll('#starRating i');
        const ratingInput = document.getElementById('reviewRating');
        stars.forEach(function (star) {
            star.addEventListener('click', function () {
                const val = parseInt(this.dataset.rating);
                ratingInput.value = val;
                stars.forEach(function (s, i) {
                    s.classList.toggle('active', i < val);
                });
            });
            star.addEventListener('mouseenter', function () {
                const val = parseInt(this.dataset.rating);
                stars.forEach(function (s, i) {
                    s.style.color = i < val ? '#fbbf24' : '';
                });
            });
            star.addEventListener('mouseleave', function () {
                stars.forEach(function (s) { s.style.color = ''; });
            });
        });

        // Submit review
        document.getElementById('submitReviewBtn').addEventListener('click', function () {
            const rating = ratingInput.value;
            const comment = document.getElementById('reviewComment').value.trim();
            const alertEl = document.getElementById('reviewAlert');

            if (!rating || parseInt(rating) < 1) {
                alertEl.className = 'modal-alert error';
                alertEl.textContent = 'Please select a rating.';
                alertEl.style.display = 'block';
                return;
            }

            const fd = new FormData();
            fd.append('rating', rating);
            if (comment) fd.append('comment', comment);

            fetch('/job/' + config.jobId + '/submit-review/', {
                method: 'POST',
                headers: { 'X-CSRFToken': (window.chatConfig && window.chatConfig.csrfToken) || getCsrf() },
                body: fd
            })
                .then(function (r) { return r.json(); })
                .then(function (data) {
                    if (data.success) {
                        alertEl.className = 'modal-alert success';
                        alertEl.textContent = 'Review submitted! Thank you.';
                        alertEl.style.display = 'block';
                        setTimeout(function () { location.reload(); }, 1500);
                    } else {
                        alertEl.className = 'modal-alert error';
                        alertEl.textContent = data.error || 'Failed to submit.';
                        alertEl.style.display = 'block';
                    }
                })
                .catch(function () {
                    alertEl.className = 'modal-alert error';
                    alertEl.textContent = 'Network error. Try again.';
                    alertEl.style.display = 'block';
                });
        });

        // Skip / Close
        var skipBtn = document.getElementById('skipReviewBtn');
        var closeBtn = document.getElementById('closeReviewModal');
        if (skipBtn) skipBtn.addEventListener('click', function () { closeModal('reviewModal'); });
        if (closeBtn) closeBtn.addEventListener('click', function () { closeModal('reviewModal'); });
    }
}

// ============================================================
// Download helpers (cross-origin Cloudinary files)
// ============================================================
window.downloadSingle = function (url, filename) {
    fetch(url)
        .then(r => r.blob())
        .then(blob => {
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(a.href);
        })
        .catch(() => {
            // Fallback: open in new tab if fetch fails (e.g. CORS)
            window.open(url, '_blank');
        });
};

window.downloadAllFiles = function () {
    const btn = document.getElementById('downloadAllBtn');
    if (!btn) return;
    let files;
    try { files = JSON.parse(btn.dataset.files); } catch (e) { return; }
    if (!files || files.length === 0) return;

    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Downloading...';

    let delay = 0;
    files.forEach(function (file) {
        setTimeout(function () {
            window.downloadSingle(file.url, file.name);
        }, delay);
        delay += 400;
    });

    setTimeout(function () {
        btn.disabled = false;
        btn.innerHTML = '<i class="fas fa-check"></i> Downloaded! <span class="download-count-badge">' + files.length + '</span>';
        setTimeout(function () {
            btn.innerHTML = '<i class="fas fa-download"></i> Download All Files <span class="download-count-badge">' + files.length + '</span>';
        }, 2000);
    }, delay + 200);
};

// ============================================================
// Submit Work (freelancer)
// ============================================================
window.submitWork = function () {
    const message = document.getElementById('submitMessage');
    const files = document.getElementById('submitFiles');
    const alertEl = document.getElementById('submitAlert');
    const btn = document.getElementById('submitWorkBtn');

    if (!message || !alertEl || !btn) return;

    const msgText = message.value.trim();
    const fileList = files ? files.files : [];

    if (!msgText && fileList.length === 0) {
        alertEl.className = 'modal-alert error';
        alertEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> Please provide a message or attach files.';
        alertEl.style.display = 'block';
        return;
    }

    btn.disabled = true;
    const hasFiles = fileList.length > 0;
    btn.innerHTML = hasFiles
        ? '<i class="fas fa-cloud-upload-alt fa-spin"></i> Uploading ' + fileList.length + ' file(s) to cloud...'
        : '<i class="fas fa-spinner fa-spin"></i> Submitting...';
    alertEl.style.display = 'none';

    const formData = new FormData();
    formData.append('message', msgText);
    for (let i = 0; i < fileList.length; i++) {
        formData.append('files', fileList[i]);
    }

    fetch('/job/' + config.jobId + '/submit-work/', {
        method: 'POST',
        headers: { 'X-CSRFToken': (window.chatConfig && window.chatConfig.csrfToken) || getCsrf() },
        body: formData
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                alertEl.className = 'modal-alert success';
                alertEl.innerHTML = '<i class="fas fa-check-circle"></i> ' + data.message;
                alertEl.style.display = 'block';
                btn.innerHTML = '<i class="fas fa-check"></i> Submitted!';
                setTimeout(() => location.reload(), 1500);
            } else {
                alertEl.className = 'modal-alert error';
                alertEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> ' + data.error;
                alertEl.style.display = 'block';
                btn.disabled = false;
                btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Work';
            }
        })
        .catch(() => {
            alertEl.className = 'modal-alert error';
            alertEl.innerHTML = '<i class="fas fa-exclamation-circle"></i> Network error.';
            alertEl.style.display = 'block';
            btn.disabled = false;
            btn.innerHTML = '<i class="fas fa-paper-plane"></i> Submit Work';
        });
};

// ============================================================
// Review Submission (client: accept/request changes)
// ============================================================
window.reviewSubmission = function (action) {
    const btn = action === 'accept'
        ? document.getElementById('acceptWorkBtn')
        : document.getElementById('requestChangesBtn');

    if (btn) {
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    }

    const formData = new FormData();
    formData.append('action', action);

    fetch('/job/' + config.jobId + '/review-submission/', {
        method: 'POST',
        headers: { 'X-CSRFToken': (window.chatConfig && window.chatConfig.csrfToken) || getCsrf() },
        body: formData
    })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                // Clear review shown flag so popup triggers on reload
                if (action === 'accept') {
                    sessionStorage.removeItem('fh_review_shown');
                }
                setTimeout(() => location.reload(), 800);
            } else {
                alert(data.error || 'Error processing request.');
                if (btn) {
                    btn.disabled = false;
                    btn.innerHTML = action === 'accept'
                        ? '<i class="fas fa-check-circle"></i> Accept Work'
                        : '<i class="fas fa-undo"></i> Request Changes';
                }
            }
        })
        .catch(() => {
            alert('Network error.');
            if (btn) btn.disabled = false;
        });
};

// ============================================================
// Full-Width Chat (job_view page)
// ============================================================
(function () {
    if (!config.canChat || !config.jobId) return;

    const messagesEl = document.getElementById('fullChatMessages');
    const inputEl = document.getElementById('fullChatInput');
    const sendBtn = document.getElementById('fullSendBtn');
    const attachBtn = document.getElementById('fullAttachBtn');
    const fileInput = document.getElementById('fullFileInput');
    const filePreview = document.getElementById('fullFilePreview');
    const fileNameEl = document.getElementById('fullFileName');
    const fileRemoveBtn = document.getElementById('fullFileRemove');
    const typingEl = document.getElementById('fullTypingIndicator');
    const typingTextEl = document.getElementById('fullTypingText');

    if (!messagesEl) return;

    let lastMsgId = 0;
    let selectedFile = null;
    let msgTimer = null;
    let typTimer = null;
    let typDebounce = null;

    function escHtml(s) {
        if (!s) return '';
        const d = document.createElement('div');
        d.textContent = s;
        return d.innerHTML;
    }

    function fmtTime(iso) {
        if (!iso) return '';
        const d = new Date(iso);
        return d.toLocaleTimeString('en-US', { hour: '2-digit', minute: '2-digit', hour12: true });
    }

    function appendMsg(msg) {
        // Skip if already rendered (race condition between send response and polling)
        if (messagesEl.querySelector('[data-msg-id="' + msg.id + '"]')) return;

        const isSent = msg.sender_id === window.chatConfig.userId;
        const div = document.createElement('div');
        div.className = 'chat-msg ' + (isSent ? 'sent' : 'received');
        div.dataset.msgId = msg.id;

        let html = '';
        if (msg.file_url) {
            if (msg.file_type === 'image') {
                html += '<div class="chat-msg-file"><img class="chat-msg-image" src="' + escHtml(msg.file_url) + '" alt="' + escHtml(msg.file_name) + '" onclick="window.openMediaViewer(\'' + escHtml(msg.file_url) + '\',\'' + escHtml(msg.file_name) + '\',\'image\')"></div>';
            } else if (msg.file_type === 'video') {
                html += '<div class="chat-msg-file"><div style="font-size:0.78rem;color:#c084fc;cursor:pointer;" onclick="window.openMediaViewer(\'' + escHtml(msg.file_url) + '\',\'' + escHtml(msg.file_name) + '\',\'video\')"><i class="fas fa-play-circle"></i> ' + escHtml(msg.file_name) + '</div></div>';
            } else {
                // For non-image/video files, use Django download proxy endpoint
                const downloadUrl = '/api/chat-file/' + msg.id + '/download/';
                html += '<div class="chat-msg-file"><a href="' + downloadUrl + '" class="chat-msg-file-link"><i class="fas fa-file-download"></i> ' + escHtml(msg.file_name) + '</a></div>';
            }
        }
        if (msg.text) html += '<div class="chat-msg-text">' + escHtml(msg.text) + '</div>';

        let tick = '';
        if (isSent) {
            tick = msg.is_seen
                ? '<span class="chat-msg-tick seen"><i class="fa-solid fa-check-double"></i></span>'
                : '<span class="chat-msg-tick"><i class="fa-solid fa-check"></i></span>';
        }
        html += '<div class="chat-msg-meta">' + fmtTime(msg.created_at) + ' ' + tick + '</div>';

        div.innerHTML = html;
        messagesEl.appendChild(div);
    }

    function scrollBottom() {
        messagesEl.scrollTop = messagesEl.scrollHeight;
    }

    function fetchMsgs(initial) {
        fetch('/job/' + config.jobId + '/chat/messages/?after=' + lastMsgId, {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(r => r.json())
            .then(data => {
                if (!data.success) return;
                if (initial && data.messages.length === 0) {
                    messagesEl.innerHTML = '<div class="chat-list-empty" style="padding:40px 10px;"><i class="fas fa-comments"></i><p>Start the conversation!</p></div>';
                    return;
                }
                if (data.messages.length > 0 && lastMsgId === 0) {
                    messagesEl.innerHTML = '';
                }
                data.messages.forEach(m => {
                    appendMsg(m);
                    lastMsgId = Math.max(lastMsgId, m.id);
                });
                scrollBottom();
                if (!initial && data.messages.some(m => m.sender_id !== window.chatConfig.userId)) {
                    markSeen();
                }
            })
            .catch(() => { });
    }

    function markSeen() {
        fetch('/job/' + config.jobId + '/chat/mark-seen/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': (window.chatConfig && window.chatConfig.csrfToken) || getCsrf(),
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).catch(() => { });
    }

    function sendMsg() {
        const text = inputEl.value.trim();
        if (!text && !selectedFile) return;

        const fd = new FormData();
        if (text) fd.append('message', text);
        if (selectedFile) fd.append('file', selectedFile);

        const emptyState = messagesEl.querySelector('.chat-list-empty');
        if (emptyState) emptyState.remove();

        inputEl.value = '';
        clearFile();

        fetch('/job/' + config.jobId + '/chat/send/', {
            method: 'POST',
            headers: { 'X-CSRFToken': (window.chatConfig && window.chatConfig.csrfToken) || getCsrf() },
            body: fd
        })
            .then(r => {
                if (!r.ok) throw new Error('HTTP ' + r.status);
                return r.json();
            })
            .then(data => {
                if (data.success) {
                    appendMsg(data.message);
                    lastMsgId = Math.max(lastMsgId, data.message.id);
                    scrollBottom();
                } else {
                    console.error('Send failed:', data.error);
                }
            })
            .catch(err => { console.error('Chat send error:', err); });
    }

    function clearFile() {
        selectedFile = null;
        if (fileInput) fileInput.value = '';
        if (filePreview) filePreview.style.display = 'none';
    }

    function pollTyping() {
        fetch('/job/' + config.jobId + '/chat/typing-status/', {
            headers: { 'X-Requested-With': 'XMLHttpRequest' }
        })
            .then(r => r.json())
            .then(data => {
                if (data.success && data.typing_users.length > 0) {
                    if (typingTextEl) typingTextEl.textContent = data.typing_users[0] + ' is typing...';
                    if (typingEl) typingEl.style.display = 'flex';
                } else {
                    if (typingEl) typingEl.style.display = 'none';
                }
            })
            .catch(() => { if (typingEl) typingEl.style.display = 'none'; });
    }

    // Event listeners
    if (sendBtn) sendBtn.addEventListener('click', sendMsg);
    if (inputEl) {
        inputEl.addEventListener('keydown', function (e) {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMsg(); }
        });
        inputEl.addEventListener('input', function () {
            const fd = new FormData();
            fd.append('is_typing', 'true');
            fetch('/job/' + config.jobId + '/chat/typing/', {
                method: 'POST',
                headers: { 'X-CSRFToken': (window.chatConfig && window.chatConfig.csrfToken) || getCsrf() },
                body: fd
            }).catch(() => { });
            clearTimeout(typDebounce);
            typDebounce = setTimeout(() => {
                const fd2 = new FormData();
                fd2.append('is_typing', 'false');
                fetch('/job/' + config.jobId + '/chat/typing/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': (window.chatConfig && window.chatConfig.csrfToken) || getCsrf() },
                    body: fd2
                }).catch(() => { });
            }, 2000);
        });
    }

    if (attachBtn) attachBtn.addEventListener('click', () => fileInput.click());
    if (fileInput) fileInput.addEventListener('change', function () {
        if (this.files && this.files[0]) {
            selectedFile = this.files[0];
            if (fileNameEl) fileNameEl.textContent = selectedFile.name;
            if (filePreview) filePreview.style.display = 'flex';
        }
    });
    if (fileRemoveBtn) fileRemoveBtn.addEventListener('click', clearFile);

    // Initialize
    fetchMsgs(true);
    markSeen();
    msgTimer = setInterval(() => fetchMsgs(false), 3000);
    typTimer = setInterval(pollTyping, 2000);
})();
