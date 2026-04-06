/**
 * FreelanceHub Global Chat Widget
 * Handles: chat list, conversations, polling, typing indicators, file uploads,
 * message ticks, media viewer, session persistence across pages, and review popups.
 */
(function () {
    'use strict';

    if (!window.chatConfig) return;

    const CFG = window.chatConfig;
    const POLL_MESSAGES = 3000;
    const POLL_TYPING = 2000;
    const POLL_UNREAD = 15000;  // Reduced frequency: 15s instead of 10s
    let msgPollTimer = null;
    let typingPollTimer = null;
    let unreadPollTimer = null;
    let typingDebounce = null;
    let currentJobId = null;
    let lastMsgId = 0;
    let selectedFile = null;

    // ─── DOM Refs ───
    const widget = document.getElementById('globalChatWidget');
    const chatBtn = document.querySelector('.chat-button');
    const listView = document.getElementById('chatListView');
    const convoView = document.getElementById('chatConvoView');
    const backBtn = document.getElementById('chatBackBtn');
    const minBtn = document.getElementById('chatMinimizeBtn');
    const titleEl = document.getElementById('chatWidgetTitle');
    const ongoingList = document.getElementById('chatListOngoing');
    const completedList = document.getElementById('chatListCompleted');
    const ongoingBadge = document.getElementById('ongoingBadge');
    const completedBadge = document.getElementById('completedBadge');
    const messagesEl = document.getElementById('chatMessages');
    const msgContainer = document.getElementById('chatMessagesContainer');
    const inputEl = document.getElementById('chatInput');
    const sendBtn = document.getElementById('chatSendBtn');
    const attachBtn = document.getElementById('chatAttachBtn');
    const fileInput = document.getElementById('chatFileInput');
    const filePreview = document.getElementById('chatFilePreview');
    const fileName = document.getElementById('chatFileName');
    const fileRemove = document.getElementById('chatFileRemove');
    const typingIndicator = document.getElementById('typingIndicator');
    const convoAvatar = document.getElementById('convoAvatar');
    const convoName = document.getElementById('convoName');
    const convoJob = document.getElementById('convoJob');
    const mediaViewer = document.getElementById('mediaViewer');
    const mediaContent = document.getElementById('mediaViewerContent');
    const mediaName = document.getElementById('mediaViewerName');
    const mediaClose = document.getElementById('mediaViewerClose');

    if (!widget || !chatBtn) return;

    // ─── Session Persistence ───
    function saveState() {
        const state = {
            open: widget.style.display !== 'none',
            jobId: currentJobId,
            view: convoView.style.display !== 'none' ? 'convo' : 'list',
            // Save conversation info for restoration
            convoInfo: convoView.style.display !== 'none' ? {
                name: convoName.textContent,
                initial: convoAvatar.textContent,
                jobTitle: convoJob.textContent
            } : null
        };
        sessionStorage.setItem('fh_chat_state', JSON.stringify(state));
    }

    function restoreState() {
        try {
            const raw = sessionStorage.getItem('fh_chat_state');
            if (!raw) return;
            const state = JSON.parse(raw);
            if (state.open) {
                showWidget();
                if (state.view === 'convo' && state.jobId) {
                    // Restore conversation with saved user info
                    const info = state.convoInfo || {};
                    // Don't pass "Loading..." as valid name
                    const name = info.name !== 'Loading...' ? info.name : null;
                    const initial = info.initial !== '?' ? info.initial : null;
                    setTimeout(() => openConversation(
                        state.jobId, 
                        name, 
                        initial, 
                        info.jobTitle
                    ), 100);
                } else if (state.view === 'list') {
                    // Defer chat list load to avoid blocking page render
                    setTimeout(loadChatList, 100);
                }
            }
        } catch (e) { /* ignore */ }
    }

    // ─── Widget Toggle ───
    function showWidget() {
        widget.style.display = 'flex';
        chatBtn.classList.add('chat-open');
        saveState();
    }

    function hideWidget() {
        widget.style.display = 'none';
        chatBtn.classList.remove('chat-open');
        stopConvoPolling();
        currentJobId = null;
        saveState();
    }

    chatBtn.addEventListener('click', function () {
        if (widget.style.display === 'none' || widget.style.display === '') {
            showWidget();
            showListView();
            loadChatList();
        } else {
            hideWidget();
        }
    });

    minBtn.addEventListener('click', hideWidget);

    backBtn.addEventListener('click', function () {
        showListView();
        loadChatList();
        stopConvoPolling();
        currentJobId = null;
        saveState();
    });

    // ─── View Switching ───
    function showListView() {
        listView.style.display = 'flex';
        convoView.style.display = 'none';
        backBtn.style.display = 'none';
        titleEl.textContent = 'Messages';
    }

    function showConvoView() {
        listView.style.display = 'none';
        convoView.style.display = 'flex';
        backBtn.style.display = 'block';
    }

    // ─── Tab Switching ───
    document.querySelectorAll('.chat-tab').forEach(function (tab) {
        tab.addEventListener('click', function () {
            document.querySelectorAll('.chat-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.chat-list').forEach(l => l.classList.remove('active'));
            this.classList.add('active');
            const tabName = this.dataset.tab;
            document.getElementById(tabName === 'ongoing' ? 'chatListOngoing' : 'chatListCompleted').classList.add('active');
        });
    });

    // ─── Load Chat List ───
    function loadChatList() {
        fetch(CFG.urls.chatList, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(r => r.json())
            .then(data => {
                if (!data.success) return;
                renderChatList(data.chats);
            })
            .catch(console.error);
    }

    function renderChatList(chats) {
        let ongoingHTML = '';
        let completedHTML = '';
        let ongoingCount = 0;
        let completedCount = 0;

        chats.forEach(chat => {
            const isOngoing = chat.job_status === 'IN_PROGRESS' || chat.job_status === 'SUBMITTED';
            const lastMsg = chat.last_message;
            let preview = 'No messages yet';
            let timeStr = '';

            if (lastMsg) {
                if (lastMsg.file_name) preview = '📎 ' + lastMsg.file_name;
                else if (lastMsg.text) preview = lastMsg.text;
                timeStr = formatTimeShort(lastMsg.created_at);
            }

            const unreadBadge = chat.unread_count > 0
                ? '<div class="chat-list-unread">' + chat.unread_count + '</div>'
                : '';

            if (isOngoing) ongoingCount += chat.unread_count;
            else completedCount += chat.unread_count;

            const html = '<div class="chat-list-item" data-job-id="' + chat.job_id + '" data-other="' + escapeHtml(chat.chat_label || chat.other_user) + '" data-initial="' + escapeHtml(chat.other_initial) + '" data-title="' + escapeHtml(chat.job_title) + '">' +
                '<div class="chat-list-avatar">' + escapeHtml(chat.other_initial) + '</div>' +
                '<div class="chat-list-info">' +
                '<div class="chat-list-name">' + escapeHtml(chat.chat_label || chat.other_user) + '</div>' +
                '<div class="chat-list-preview">' + escapeHtml(preview) + '</div>' +
                '</div>' +
                '<div class="chat-list-meta">' +
                '<div class="chat-list-time">' + timeStr + '</div>' +
                unreadBadge +
                '</div></div>';

            if (isOngoing) ongoingHTML += html;
            else completedHTML += html;
        });

        ongoingList.innerHTML = ongoingHTML || '<div class="chat-list-empty"><i class="fas fa-comments"></i><p>No ongoing chats</p></div>';
        completedList.innerHTML = completedHTML || '<div class="chat-list-empty"><i class="fas fa-check-circle"></i><p>No completed chats</p></div>';

        // Update tab badges
        setBadge(ongoingBadge, ongoingCount);
        setBadge(completedBadge, completedCount);

        // Add click handlers
        document.querySelectorAll('.chat-list-item').forEach(item => {
            item.addEventListener('click', function () {
                const jobId = parseInt(this.dataset.jobId);
                const other = this.dataset.other;
                const initial = this.dataset.initial;
                const jobTitle = this.dataset.title;
                openConversation(jobId, other, initial, jobTitle);
            });
        });
    }


    function setBadge(el, count) {
        if (count > 0) {
            el.textContent = count;
            el.style.display = 'flex';
        } else {
            el.style.display = 'none';
        }
    }

    // ─── Open Conversation ───
    function openConversation(jobId, otherUser, otherInitial, jobTitle) {
        currentJobId = jobId;
        lastMsgId = 0;
        messagesEl.innerHTML = '';

        // If called from session restore without params, fetch info
        if (!otherUser) {
            // Will get info from loaded messages or list
            convoName.textContent = 'Loading...';
            convoJob.textContent = '';
            convoAvatar.textContent = '?';
        } else {
            convoName.textContent = otherUser;
            convoAvatar.textContent = otherInitial;
            convoJob.textContent = jobTitle;
        }

        titleEl.textContent = otherUser || 'Chat';
        showConvoView();
        saveState();

        // Load messages
        fetchMessages(jobId, true);

        // Mark as seen
        markSeen(jobId);

        // Start polling
        startConvoPolling(jobId);
    }

    // ─── Fetch Messages ───
    function fetchMessages(jobId, initial) {
        const url = '/job/' + jobId + '/chat/messages/?after=' + lastMsgId;
        fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(r => r.json())
            .then(data => {
                if (!data.success || data.messages.length === 0) {
                    if (initial && data.messages && data.messages.length === 0) {
                        messagesEl.innerHTML = '<div class="chat-list-empty"><i class="fas fa-comments"></i><p>Start the conversation!</p></div>';
                    }
                    return;
                }

                // On first load, clear "start conversation" message
                if (initial && lastMsgId === 0) {
                    messagesEl.innerHTML = '';
                }

                data.messages.forEach(msg => {
                    appendMessage(msg);
                    lastMsgId = Math.max(lastMsgId, msg.id);
                });

                scrollToBottom();

                // Update conversation header if we have data
                if (initial && data.messages.length > 0) {
                    const firstOther = data.messages.find(m => m.sender_id !== CFG.userId);
                    if (firstOther && (!convoName.textContent || convoName.textContent === 'Loading...')) {
                        convoName.textContent = firstOther.sender;
                        convoAvatar.textContent = firstOther.sender.charAt(0).toUpperCase();
                        titleEl.textContent = firstOther.sender;
                    }
                }

                // Mark new messages as seen
                if (!initial && data.messages.some(m => m.sender_id !== CFG.userId)) {
                    markSeen(jobId);
                }
            })
            .catch(console.error);
    }

    function appendMessage(msg) {
        // Skip if already rendered (race between send response and polling)
        if (messagesEl.querySelector('[data-msg-id="' + msg.id + '"]')) return;

        const isSent = msg.sender_id === CFG.userId;
        const div = document.createElement('div');
        div.className = 'chat-msg ' + (isSent ? 'sent' : 'received');
        div.dataset.msgId = msg.id;

        let content = '';

        // File content
        if (msg.file_url) {
            if (msg.file_type === 'image') {
                content += '<div class="chat-msg-file"><img class="chat-msg-image" src="' + escapeHtml(msg.file_url) + '" alt="' + escapeHtml(msg.file_name) + '" onclick="window.openMediaViewer(\'' + escapeHtml(msg.file_url) + '\', \'' + escapeHtml(msg.file_name) + '\', \'image\')"></div>';
            } else if (msg.file_type === 'video') {
                content += '<div class="chat-msg-file"><video class="chat-msg-video" src="' + escapeHtml(msg.file_url) + '" onclick="window.openMediaViewer(\'' + escapeHtml(msg.file_url) + '\', \'' + escapeHtml(msg.file_name) + '\', \'video\')" poster=""></video><div style="font-size:0.75rem;color:rgba(255,255,255,0.5);margin-top:4px;cursor:pointer;" onclick="window.openMediaViewer(\'' + escapeHtml(msg.file_url) + '\', \'' + escapeHtml(msg.file_name) + '\', \'video\')"><i class="fas fa-play-circle"></i> Play video</div></div>';
            } else {
                content += '<div class="chat-msg-file"><a href="' + escapeHtml(msg.file_url) + '" download="' + escapeHtml(msg.file_name) + '" class="chat-msg-file-link"><i class="fas fa-file-download"></i> ' + escapeHtml(msg.file_name) + '</a></div>';
            }
        }

        // Text content
        if (msg.text) {
            content += '<div class="chat-msg-text">' + escapeHtml(msg.text) + '</div>';
        }

        // Meta (time + ticks)
        const time = formatTimeShort(msg.created_at);
        let tickHTML = '';
        if (isSent) {
            if (msg.is_seen) {
                tickHTML = '<span class="chat-msg-tick seen"><i class="fa-solid fa-check-double"></i></span>';
            } else {
                tickHTML = '<span class="chat-msg-tick"><i class="fa-solid fa-check"></i></span>';
            }
        }
        content += '<div class="chat-msg-meta">' + time + ' ' + tickHTML + '</div>';

        div.innerHTML = content;
        messagesEl.appendChild(div);
    }

    function scrollToBottom() {
        if (msgContainer) {
            msgContainer.scrollTop = msgContainer.scrollHeight;
        }
    }

    // ─── Send Message ───
    sendBtn.addEventListener('click', sendMessage);
    inputEl.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            sendMessage();
        }
    });

    function sendMessage() {
        if (!currentJobId) return;

        const text = inputEl.value.trim();
        if (!text && !selectedFile) return;

        const formData = new FormData();
        if (text) formData.append('message', text);
        if (selectedFile) formData.append('file', selectedFile);

        // Show sending state
        const tempId = 'temp-' + Date.now();
        const tempMsg = {
            id: tempId,
            sender: CFG.username,
            sender_id: CFG.userId,
            text: text,
            file_url: null,
            file_name: selectedFile ? selectedFile.name : null,
            file_type: null,
            is_seen: false,
            created_at: new Date().toISOString()
        };

        // Clear "start conversation" empty state
        const emptyState = messagesEl.querySelector('.chat-list-empty');
        if (emptyState) emptyState.remove();

        appendMessage(tempMsg);
        scrollToBottom();

        // Add sending indicator
        const tempEl = messagesEl.querySelector('[data-msg-id="' + tempId + '"]');
        if (tempEl) {
            const meta = tempEl.querySelector('.chat-msg-meta');
            if (meta) meta.innerHTML = '<span style="color:rgba(255,255,255,0.4);"><i class="fa-regular fa-clock"></i> sending</span>';
        }

        inputEl.value = '';
        clearFileSelection();

        // Clear typing
        sendTypingStatus(false);

        fetch('/job/' + currentJobId + '/chat/send/', {
            method: 'POST',
            headers: { 'X-CSRFToken': CFG.csrfToken },
            body: formData
        })
            .then(r => r.json())
            .then(data => {
                // Remove temp message
                if (tempEl) tempEl.remove();

                if (data.success) {
                    appendMessage(data.message);
                    lastMsgId = Math.max(lastMsgId, data.message.id);
                    scrollToBottom();
                }
            })
            .catch(err => {
                console.error(err);
                if (tempEl) {
                    const meta = tempEl.querySelector('.chat-msg-meta');
                    if (meta) meta.innerHTML = '<span style="color:#f87171;">Failed to send</span>';
                }
            });
    }

    // ─── File Handling ───
    attachBtn.addEventListener('click', () => fileInput.click());

    fileInput.addEventListener('change', function () {
        if (this.files && this.files[0]) {
            selectedFile = this.files[0];
            fileName.textContent = selectedFile.name;
            filePreview.style.display = 'flex';
        }
    });

    fileRemove.addEventListener('click', clearFileSelection);

    function clearFileSelection() {
        selectedFile = null;
        fileInput.value = '';
        filePreview.style.display = 'none';
    }

    // ─── Typing Indicator ───
    inputEl.addEventListener('input', function () {
        if (!currentJobId) return;
        sendTypingStatus(true);
        clearTimeout(typingDebounce);
        typingDebounce = setTimeout(() => sendTypingStatus(false), 2000);
    });

    function sendTypingStatus(isTyping) {
        if (!currentJobId) return;
        const formData = new FormData();
        formData.append('is_typing', isTyping ? 'true' : 'false');
        fetch('/job/' + currentJobId + '/chat/typing/', {
            method: 'POST',
            headers: { 'X-CSRFToken': CFG.csrfToken },
            body: formData
        }).catch(() => { });
    }

    function pollTyping() {
        if (!currentJobId) return;
        fetch('/job/' + currentJobId + '/chat/typing-status/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(r => r.json())
            .then(data => {
                if (data.success && data.typing_users.length > 0) {
                    document.getElementById('typingText').textContent = data.typing_users[0] + ' is typing...';
                    typingIndicator.style.display = 'flex';
                } else {
                    typingIndicator.style.display = 'none';
                }
            })
            .catch(() => { typingIndicator.style.display = 'none'; });
    }

    // ─── Mark Seen ───
    function markSeen(jobId) {
        fetch('/job/' + jobId + '/chat/mark-seen/', {
            method: 'POST',
            headers: {
                'X-CSRFToken': CFG.csrfToken,
                'X-Requested-With': 'XMLHttpRequest'
            }
        }).catch(() => { });
    }

    // ─── Polling ───
    function startConvoPolling(jobId) {
        stopConvoPolling();
        msgPollTimer = setInterval(() => {
            if (currentJobId === jobId) fetchMessages(jobId, false);
        }, POLL_MESSAGES);
        typingPollTimer = setInterval(pollTyping, POLL_TYPING);
    }

    function stopConvoPolling() {
        clearInterval(msgPollTimer);
        clearInterval(typingPollTimer);
        msgPollTimer = null;
        typingPollTimer = null;
    }

    // ─── Unread Badge Polling ───
    function pollUnread() {
        fetch(CFG.urls.unreadCount, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
            .then(r => r.json())
            .then(data => {
                if (!data.success) return;
                updateChatButtonBadge(data.total);
            })
            .catch(() => { });
    }

    function updateChatButtonBadge(count) {
        let badge = chatBtn.querySelector('.unread-badge');
        if (count > 0) {
            if (!badge) {
                badge = document.createElement('span');
                badge.className = 'unread-badge';
                chatBtn.appendChild(badge);
            }
            badge.textContent = count > 99 ? '99+' : count;
        } else {
            if (badge) badge.remove();
        }
    }

    // ─── Media Viewer ───
    window.openMediaViewer = function (url, name, type) {
        if (!mediaViewer) return;
        mediaName.textContent = name;
        if (type === 'image') {
            mediaContent.innerHTML = '<img src="' + url + '" alt="' + escapeHtml(name) + '">';
        } else if (type === 'video') {
            mediaContent.innerHTML = '<video src="' + url + '" controls autoplay style="max-width:90%;max-height:85vh;border-radius:8px;"></video>';
        }
        mediaViewer.style.display = 'flex';
    };

    if (mediaClose) {
        mediaClose.addEventListener('click', function () {
            mediaViewer.style.display = 'none';
            mediaContent.innerHTML = '';
        });
    }

    if (mediaViewer) {
        mediaViewer.addEventListener('click', function (e) {
            if (e.target === mediaViewer) {
                mediaViewer.style.display = 'none';
                mediaContent.innerHTML = '';
            }
        });
    }


    // ─── Utility Functions ───
    function escapeHtml(str) {
        if (!str) return '';
        const div = document.createElement('div');
        div.textContent = str;
        return div.innerHTML;
    }

    function formatTimeShort(isoStr) {
        if (!isoStr) return '';
        const d = new Date(isoStr);
        const now = new Date();
        const diffMs = now - d;
        const diffMins = Math.floor(diffMs / 60000);

        if (diffMins < 1) return 'now';
        if (diffMins < 60) return diffMins + 'm';
        const diffHrs = Math.floor(diffMins / 60);
        if (diffHrs < 24) return diffHrs + 'h';
        const diffDays = Math.floor(diffHrs / 24);
        if (diffDays < 7) return diffDays + 'd';
        return d.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }

    // ─── Expose for inline chat in job_view ───
    window.FreelanceChat = {
        openConversation: openConversation,
        showWidget: showWidget,
        loadChatList: loadChatList,
        fetchMessages: fetchMessages,
        sendMessage: sendMessage,
        currentJobId: function () { return currentJobId; }
    };

    // ─── Initialize on DOMContentLoaded ───
    function initialize() {
        // Start unread badge polling (deferred to avoid blocking page load)
        unreadPollTimer = setInterval(pollUnread, POLL_UNREAD);
        setTimeout(pollUnread, 1000); // Initial poll after 1s
        
        // Restore previous session state
        restoreState();
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        // DOM already loaded, initialize after short delay
        setTimeout(initialize, 50);
    }

})();
