/* ─── Config (now provided by profile.html inline script) ───────────── */
// IS_OWNER, IS_AUTH, PROFILE_USERNAME, CSRF_TOKEN, URLS are defined in template

/* ─── Helpers ────────────────────────────────────────────────────────── */
function csrfHeaders() {
    return { 'X-CSRFToken': CSRF_TOKEN };
}

function openModal(el)  { el.classList.add('open'); document.body.style.overflow = 'hidden'; }
function closeModal(el) { el.classList.remove('open'); document.body.style.overflow = ''; }

function isVideo(url) {
    return /\.(mp4|mov|webm|avi|mkv)(\?|$)/i.test(url);
}

/* ─── DOM refs ───────────────────────────────────────────────────────── */
const cropModal      = document.getElementById('cropModal');
const cropImage      = document.getElementById('cropImage');
const cropConfirmBtn = document.getElementById('cropConfirmBtn');
const cropCancelBtn  = document.getElementById('cropCancelBtn');
const cropModalClose = document.getElementById('cropModalClose');
const cropSpinner    = document.getElementById('cropSpinner');

const addPostModal   = document.getElementById('addPostModal');
const postViewModal  = document.getElementById('postViewModal');
const postsGrid      = document.getElementById('postsGrid');
const emptyState     = document.getElementById('emptyState');

let cropper = null;

/* ══════════════════════════════════════════════════════════════════════
   SECTION 1 — PROFILE PHOTO CROPPING
   ════════════════════════════════════════════════════════════════════ */
if (IS_OWNER) {
    const editPhotoBtn   = document.getElementById('editPhotoBtn');
    const photoFileInput = document.getElementById('photoFileInput');

    editPhotoBtn.addEventListener('click', () => photoFileInput.click());

    photoFileInput.addEventListener('change', function () {
        const file = this.files[0];
        if (!file) return;
        if (!['image/jpeg', 'image/png'].includes(file.type)) {
            alert('Only JPEG or PNG images are accepted.');
            return;
        }
        const reader = new FileReader();
        reader.onload = (e) => {
            cropImage.src = e.target.result;
            openModal(cropModal);
            // Destroy old cropper before creating a new one
            if (cropper) { cropper.destroy(); cropper = null; }
            cropper = new Cropper(cropImage, {
                aspectRatio: 1,
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 0.8,
                responsive: true,
            });
        };
        reader.readAsDataURL(file);
    });

    [cropCancelBtn, cropModalClose].forEach(btn => {
        btn.addEventListener('click', () => {
            closeModal(cropModal);
            if (cropper) { cropper.destroy(); cropper = null; }
            photoFileInput.value = '';
        });
    });

    cropConfirmBtn.addEventListener('click', () => {
        if (!cropper) return;
        const canvas = cropper.getCroppedCanvas({ width: 256, height: 256 });
        if (!canvas) return;

        cropConfirmBtn.disabled = true;
        cropSpinner.classList.add('active');

        canvas.toBlob(async (blob) => {
            const formData = new FormData();
            formData.append('photo', blob, 'profile.jpg');

            try {
                const res  = await fetch(URLS.updatePhoto, {
                    method: 'POST',
                    headers: csrfHeaders(),
                    body: formData,
                });
                const data = await res.json();
                if (data.success) {
                    // Update avatar in the DOM
                    const wrap   = document.querySelector('.profile-avatar-wrap');
                    let imgEl    = document.getElementById('profileAvatarImg');
                    const initEl = document.getElementById('profileAvatarInitials');
                    if (!imgEl) {
                        imgEl = document.createElement('img');
                        imgEl.id = 'profileAvatarImg';
                        imgEl.className = 'profile-avatar';
                        imgEl.alt = 'Profile photo';
                        if (initEl) initEl.replaceWith(imgEl);
                        else wrap.prepend(imgEl);
                    }
                    imgEl.src = data.url + '?t=' + Date.now();
                    const sidebarAvatar = document.querySelector('.user-avatar-small');
                    if (sidebarAvatar && sidebarAvatar.tagName === 'IMG') {
                        sidebarAvatar.src = data.url + '?t=' + Date.now();
                    }
                    closeModal(cropModal);
                    cropper.destroy(); cropper = null;
                    photoFileInput.value = '';
                } else {
                    alert('Upload failed: ' + (data.error || 'Unknown error'));
                }
            } catch (err) {
                alert('Upload error: ' + err.message);
            } finally {
                cropConfirmBtn.disabled = false;
                cropSpinner.classList.remove('active');
            }
        }, 'image/jpeg', 0.92);
    });
}

/* ══════════════════════════════════════════════════════════════════════
   SECTION 2 — ADD POST MODAL
   ════════════════════════════════════════════════════════════════════ */
if (IS_OWNER && addPostModal) {
    const openAddPostBtn  = document.getElementById('openAddPostModal');
    const addPostClose    = document.getElementById('addPostClose');
    const addPostCancelBtn = document.getElementById('addPostCancelBtn');
    const fileDropZone    = document.getElementById('fileDropZone');
    const postFileInput   = document.getElementById('postFileInput');
    const filePreview     = document.getElementById('filePreview');
    const postCategoryEl  = document.getElementById('postCategory');
    const postCaptionEl   = document.getElementById('postCaption');
    const postSpinner     = document.getElementById('postSpinner');
    const addPostSubmitBtn = document.getElementById('addPostSubmitBtn');

    let selectedPostFile = null;

    openAddPostBtn.addEventListener('click', () => {
        resetAddPostForm();
        openModal(addPostModal);
    });

    function closeAddPost() {
        closeModal(addPostModal);
        resetAddPostForm();
    }

    [addPostClose, addPostCancelBtn].forEach(b => b.addEventListener('click', closeAddPost));

    // File drop zone click
    fileDropZone.addEventListener('click', () => postFileInput.click());

    // Drag & drop
    fileDropZone.addEventListener('dragover', (e) => { e.preventDefault(); fileDropZone.classList.add('drag-over'); });
    fileDropZone.addEventListener('dragleave', () => fileDropZone.classList.remove('drag-over'));
    fileDropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        fileDropZone.classList.remove('drag-over');
        if (e.dataTransfer.files.length) handlePostFiles(e.dataTransfer.files);
    });

    postFileInput.addEventListener('change', function () {
        if (this.files.length) handlePostFiles(this.files);
    });

    function handlePostFiles(filesList) {
        const allowed = ['image/jpeg', 'image/png', 'video/mp4'];
        
        let validFiles = Array.from(filesList).filter(f => allowed.includes(f.type) && f.size <= 50 * 1024 * 1024);
        
        if (validFiles.length === 0) {
            alert('No valid files found. Max 50MB, JPEG/PNG/MP4 only.');
            return;
        }

        if (selectedPostFiles.length + validFiles.length > 10) {
            alert('Maximum 10 files allowed.');
            validFiles = validFiles.slice(0, 10 - selectedPostFiles.length);
        }

        selectedPostFiles = [...selectedPostFiles, ...validFiles];
        renderPreviews();
    }

    function renderPreviews() {
        if (selectedPostFiles.length > 0) {
            filePreview.style.display = 'flex';
            fileDropZone.style.display = selectedPostFiles.length >= 10 ? 'none' : 'block';
            filePreview.innerHTML = '';
            
            selectedPostFiles.forEach((file, index) => {
                const url = URL.createObjectURL(file);
                const wrapper = document.createElement('div');
                wrapper.style.position = 'relative';
                wrapper.style.flexShrink = '0';
                wrapper.style.width = '100px';
                wrapper.style.height = '100px';
                
                let el;
                if (file.type === 'video/mp4') {
                    el = document.createElement('video');
                    el.src = url;
                } else {
                    el = document.createElement('img');
                    el.src = url;
                }
                el.style.width = '100%';
                el.style.height = '100%';
                el.style.objectFit = 'cover';
                el.style.borderRadius = '8px';
                
                const rmBtn = document.createElement('button');
                rmBtn.innerHTML = '&times;';
                rmBtn.style.position = 'absolute';
                rmBtn.style.top = '4px';
                rmBtn.style.right = '4px';
                rmBtn.style.background = 'rgba(0,0,0,0.6)';
                rmBtn.style.color = '#fff';
                rmBtn.style.border = 'none';
                rmBtn.style.borderRadius = '50%';
                rmBtn.style.width = '20px';
                rmBtn.style.height = '20px';
                rmBtn.style.cursor = 'pointer';
                rmBtn.style.lineHeight = '1';
                rmBtn.onclick = (e) => {
                    e.stopPropagation();
                    selectedPostFiles.splice(index, 1);
                    URL.revokeObjectURL(url);
                    renderPreviews();
                };
                
                wrapper.appendChild(el);
                wrapper.appendChild(rmBtn);
                filePreview.appendChild(wrapper);
            });
        } else {
            resetAddPostForm();
        }
    }

    function resetAddPostForm() {
        selectedPostFiles = [];
        postFileInput.value = '';
        filePreview.innerHTML = '';
        filePreview.style.display = 'none';
        fileDropZone.style.display = 'block';
        postCaptionEl.value = '';
        if (postCategoryEl) postCategoryEl.selectedIndex = 0;
        fileDropZone.classList.remove('drag-over');
    }

    addPostSubmitBtn.addEventListener('click', async () => {
        if (selectedPostFiles.length === 0) { alert('Please select a file.'); return; }

        addPostSubmitBtn.disabled = true;
        postSpinner.classList.add('active');

        const formData = new FormData();
        selectedPostFiles.forEach(f => formData.append('media', f));
        formData.append('caption', postCaptionEl.value.trim());
        formData.append('category', postCategoryEl.value);

        try {
            const res  = await fetch(URLS.addPost, {
                method : 'POST',
                headers: csrfHeaders(),
                body   : formData,
            });
            const data = await res.json();
            if (data.success) {
                closeAddPost();
                prependPostCell(data.post);
            } else {
                alert('Upload failed: ' + (data.error || 'Unknown error'));
            }
        } catch (err) {
            alert('Error: ' + err.message);
        } finally {
            addPostSubmitBtn.disabled = false;
            postSpinner.classList.remove('active');
        }
    });

    function prependPostCell(post) {
        // Remove empty state if present
        if (emptyState) emptyState.remove();

        const cell = buildPostCell(post);
        postsGrid.prepend(cell);
        bindCellEvents(cell, post);
    }
}

/* ══════════════════════════════════════════════════════════════════════
   SECTION 3 — POST VIEW MODAL
   ════════════════════════════════════════════════════════════════════ */
const postModalClose    = document.getElementById('postModalClose');
const postModalMedia    = document.getElementById('postModalMedia');
const postModalAvatar   = document.getElementById('postModalAvatar');
const postModalUsername = document.getElementById('postModalUsername');
const postModalCaption  = document.getElementById('postModalCaption');
const postLikeBtn       = document.getElementById('postLikeBtn');
const postLikesCount    = document.getElementById('postLikesCount');
const postCommentsList  = document.getElementById('postCommentsList');
const commentTextarea   = document.getElementById('commentTextarea');
const postCommentSubmit = document.getElementById('postCommentSubmit');

let currentPostId = null;

function closePostModal() {
    closeModal(postViewModal);
    currentPostId = null;
    currentSlideIndex = 0;
    // Stop any playing video BEFORE wiping DOM (prevents ghost audio)
    postModalMedia.querySelectorAll('video').forEach(v => {
        v.pause();
        v.src = '';   // detach the media stream
        v.load();     // force browser to release the resource
    });
    postModalMedia.innerHTML = ''; // Now safe to wipe
    // CRITICAL: always re-enable the info card so it never acts as an invisible blocker
    const infoCard = document.querySelector('.pm-info-card');
    if (infoCard) {
        infoCard.style.opacity = '0';
        infoCard.style.pointerEvents = 'none';
    }
}

postModalClose.addEventListener('click', closePostModal);
postViewModal.addEventListener('click', (e) => {
    if (e.target === postViewModal) closePostModal();
});

const pmMediaCard = document.getElementById('pmMediaCard');

function fitMediaCard(naturalW, naturalH) {
    /* Compute display size clamped to 70vw × 80vh, preserving aspect ratio */
    const maxW = Math.floor(window.innerWidth  * 0.70);
    const maxH = Math.floor(window.innerHeight * 0.80);
    const ratio = naturalW / naturalH;
    let w = naturalW, h = naturalH;
    if (w > maxW) { w = maxW; h = Math.round(w / ratio); }
    if (h > maxH) { h = maxH; w = Math.round(h * ratio); }
    pmMediaCard.style.width  = w + 'px';
    pmMediaCard.style.height = h + 'px';
}

function showLoadingModal(postId) {
    currentPostId = postId;
    pmMediaCard.style.width  = '150px';
    pmMediaCard.style.height = '150px';
    
    postModalMedia.innerHTML = `
        <div id="modalSpinner" class="upload-spinner active" style="position: absolute; display: flex; align-items: center; justify-content: center; inset: 0; z-index: 10;">
            <div class="spinner-ring"></div>
        </div>
    `;
    
    const infoCard = document.querySelector('.pm-info-card');
    infoCard.style.opacity = '0';
    infoCard.style.transition = 'opacity 0.3s ease';
    infoCard.style.pointerEvents = 'none';
    
    openModal(postViewModal);
}

let currentMediaFiles = [];
let currentSlideIndex = 0;

const pmPrevBtn = document.getElementById('pmPrevBtn');
const pmNextBtn = document.getElementById('pmNextBtn');
const pmDots = document.getElementById('pmDots');

pmPrevBtn.addEventListener('click', () => {
    if (currentSlideIndex > 0) {
        currentSlideIndex--;
        renderSlide(currentSlideIndex);
    }
});

pmNextBtn.addEventListener('click', () => {
    if (currentSlideIndex < currentMediaFiles.length - 1) {
        currentSlideIndex++;
        renderSlide(currentSlideIndex);
    }
});

function openPostModal(post) {
    if (currentPostId && currentPostId !== post.id) return;
    currentPostId = post.id;
    
    currentMediaFiles = post.media_files && post.media_files.length ? post.media_files : [{ url: post.media_url, resource_type: post.resource_type }];
    currentSlideIndex = 0;

    if (!postViewModal.classList.contains('open')) {
        showLoadingModal(post.id);
    }

    // Set info panel text
    const initial = (post.owner || 'U')[0].toUpperCase();
    postModalAvatar.textContent  = initial;
    postModalUsername.textContent = '@' + post.owner;
    if (post.caption) {
        postModalCaption.innerHTML = `<span class="caption-username">${post.owner}</span>${escHtml(post.caption)}`;
    } else {
        postModalCaption.innerHTML = '';
    }
    postLikesCount.textContent = post.likes_count + ' like' + (post.likes_count !== 1 ? 's' : '');
    postLikeBtn.classList.toggle('liked', !!post.liked);
    postCommentsList.innerHTML = '';
    (post.comments || []).forEach(appendComment);
    commentTextarea.value = '';

    renderSlide(currentSlideIndex);
}

/* ─── Media helpers ──────────────────────────────────────────────────── */
function isVideo(url) {
    if (!url) return false;
    const clean = url.split('?')[0].toLowerCase();
    return clean.endsWith('.mp4') || clean.endsWith('.mov') ||
           clean.endsWith('.webm') || clean.endsWith('.ogg') ||
           clean.endsWith('.avi') || clean.includes('/video/');
}

function fixCloudinaryUrl(url, resourceType) {
    if (!url) return url;
    // Cloudinary URLs with /auto/ must be rewritten to the correct delivery type
    if (url.includes('/auto/upload/')) {
        const deliveryType = (resourceType === 'video') ? 'video' : 'image';
        return url.replace('/auto/upload/', `/${deliveryType}/upload/`);
    }
    // Also fix older pattern without /upload/ segment
    if (url.includes('/auto/')) {
        const deliveryType = (resourceType === 'video') ? 'video' : 'image';
        return url.replace('/auto/', `/${deliveryType}/`);
    }
    return url;
}

function renderSlide(index) {
    if (currentMediaFiles.length === 0) return;
    
    pmPrevBtn.style.display = index > 0 ? 'flex' : 'none';
    pmNextBtn.style.display = index < currentMediaFiles.length - 1 ? 'flex' : 'none';
    
    const mediaItem = currentMediaFiles[index];
    let mUrl = mediaItem.url || '';
    
    // Determine if video: prefer explicit resource_type from backend, then URL inspection
    const resourceType = mediaItem.resource_type || (isVideo(mUrl) ? 'video' : 'image');
    const isVid = resourceType === 'video';
    
    // Fix Cloudinary /auto/ delivery type in URL
    mUrl = fixCloudinaryUrl(mUrl, resourceType);
    
    console.log('[PostMedia] url:', mUrl, '| type:', resourceType, '| isVid:', isVid);

    const onMediaLoaded = (w, h) => {
        if (!postViewModal.classList.contains('open') || currentSlideIndex !== index) return;
        
        fitMediaCard(w, h);
        
        const spinner = document.getElementById('modalSpinner');
        if (spinner) {
            spinner.style.opacity = '0';
            setTimeout(() => { if (spinner) spinner.remove(); }, 350);
        }

        const infoCard = document.querySelector('.pm-info-card');
        infoCard.style.opacity = '1';
        infoCard.style.pointerEvents = 'all';
    };

    if (!document.getElementById('modalSpinner')) {
        postModalMedia.innerHTML = `
            <div id="modalSpinner" class="upload-spinner active" style="position: absolute; display: flex; align-items: center; justify-content: center; inset: 0; z-index: 10;">
                <div class="spinner-ring"></div>
            </div>`;
    } else {
        Array.from(postModalMedia.children).forEach(el => {
            if (el.id !== 'modalSpinner') el.remove();
        });
    }

    if (isVid) {
        const vid = document.createElement('video');
        vid.src = mUrl;
        vid.controls = true;
        vid.preload = 'metadata';
        vid.playsInline = true;
        vid.style.opacity = '0';
        vid.style.transition = 'opacity 0.4s ease';
        vid.style.maxWidth = '100%';
        vid.style.maxHeight = '100%';
        vid.style.position = 'relative';
        vid.style.zIndex = '2';
        postModalMedia.appendChild(vid);
        
        vid.addEventListener('loadedmetadata', function onMeta() {
            vid.removeEventListener('loadedmetadata', onMeta);
            if (currentSlideIndex !== index) return;
            vid.style.opacity = '1';
            onMediaLoaded(vid.videoWidth || 640, vid.videoHeight || 480);
            
            // Attempt to autoplay muted if required, else just try playing.
            let playPromise = vid.play();
            if (playPromise !== undefined) {
                playPromise.catch(error => {
                    // Browser autoplay policy prevented playback. User will use controls.
                });
            }
        });

        // Fail-safe to avoid infinite spinner if metadata fails somehow
        setTimeout(() => {
            if (vid.style.opacity === '0' && currentSlideIndex === index) {
                vid.style.opacity = '1';
                onMediaLoaded(640, 480);
            }
        }, 1500);

    } else {
        const img = document.createElement('img');
        img.alt = 'Post slide';
        img.style.opacity = '0';
        img.style.transition = 'opacity 0.4s ease';
        img.style.maxWidth = '100%';
        img.style.maxHeight = '100%';
        img.style.position = 'relative';
        img.style.zIndex = '2';
        postModalMedia.appendChild(img);
        
        img.addEventListener('load', function onLoad() {
            img.removeEventListener('load', onLoad);
            if (currentSlideIndex !== index) return;
            img.style.opacity = '1';
            onMediaLoaded(img.naturalWidth, img.naturalHeight);
        });
        img.src = mUrl;
    }

    if (currentMediaFiles.length > 1) {
        pmDots.style.display = 'flex';
        pmDots.innerHTML = currentMediaFiles.map((_, i) => `<span class="dot ${i === index ? 'active' : ''}"></span>`).join('');
    } else {
        pmDots.style.display = 'none';
        pmDots.innerHTML = '';
    }
}


function appendComment(c) {
    const div = document.createElement('div');
    div.className = 'comment-item';
    const u = c.user__username || c.username || 'User';
    const utype = (c.user__user_type || c.user_type || '').toLowerCase();
    const ago = timeAgo(new Date(c.created_at));
    
    let badge = '';
    if (utype === 'freelancer') {
        badge = `<span class="comment-role-badge freelancer">Freelancer</span>`;
    } else if (utype === 'client') {
        badge = `<span class="comment-role-badge client">Client</span>`;
    }

    div.innerHTML = `
        <div class="comment-avatar">${u[0].toUpperCase()}</div>
        <div class="comment-body">
            <div class="comment-header-row" style="display: flex; align-items: center; gap: 6px;">
                <span class="comment-author">${escHtml(u)}</span>
                ${badge}
            </div>
            <span class="comment-text">${escHtml(c.text)}</span>
            <span class="comment-time">${ago}</span>
        </div>`;
    postCommentsList.appendChild(div);
    postCommentsList.scrollTop = postCommentsList.scrollHeight;
}

/* Like toggle */
postLikeBtn.addEventListener('click', async () => {
    if (!IS_AUTH) { alert('Please log in to like posts.'); return; }
    if (!currentPostId) return;
    try {
        const res  = await fetch(URLS.toggleLike(currentPostId), {
            method : 'POST',
            headers: csrfHeaders(),
        });
        const data = await res.json();
        if (data.success) {
            postLikeBtn.classList.toggle('liked', data.liked);
            postLikesCount.textContent = data.likes_count + ' like' + (data.likes_count !== 1 ? 's' : '');
            // Update cell overlay
            const cell = postsGrid.querySelector(`.post-cell[data-post-id="${currentPostId}"]`);
            if (cell) {
                const heartSpan = cell.querySelector('.post-cell-overlay span:first-child');
                if (heartSpan) heartSpan.innerHTML = `<i class="fas fa-heart"></i> ${data.likes_count}`;
            }
        }
    } catch (err) { console.error(err); }
});

/* Add comment */
async function submitComment() {
    if (!IS_AUTH) { alert('Please log in to comment.'); return; }
    const text = commentTextarea.value.trim();
    if (!text || !currentPostId) return;

    try {
        const res  = await fetch(URLS.addComment(currentPostId), {
            method : 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF_TOKEN },
            body   : JSON.stringify({ text }),
        });
        const data = await res.json();
        if (data.success) {
            commentTextarea.value = '';
            appendComment(data.comment);
            // Update cell overlay comment count
            const cell = postsGrid.querySelector(`.post-cell[data-post-id="${currentPostId}"]`);
            if (cell) {
                const commentSpan = cell.querySelector('.post-cell-overlay span:last-child');
                if (commentSpan) {
                    const cur = parseInt(commentSpan.textContent) || 0;
                    commentSpan.innerHTML = `<i class="fas fa-comment"></i> ${cur + 1}`;
                }
            }
        }
    } catch (err) { console.error(err); }
}

postCommentSubmit.addEventListener('click', submitComment);
commentTextarea.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submitComment(); }
});

/* ══════════════════════════════════════════════════════════════════════
   SECTION 4 — CATEGORY FILTER (AJAX)
   ════════════════════════════════════════════════════════════════════ */
const categoryFilters = document.getElementById('categoryFilters');

categoryFilters.addEventListener('click', async (e) => {
    const pill = e.target.closest('.filter-pill');
    if (!pill) return;

    categoryFilters.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
    pill.classList.add('active');

    const category = pill.dataset.category;
    const url = URLS.filterPosts + (category ? `?category=${encodeURIComponent(category)}` : '');

    try {
        const res  = await fetch(url);
        const data = await res.json();
        if (data.success) renderPosts(data.posts);
    } catch (err) { console.error(err); }
});

function renderPosts(posts) {
    postsGrid.innerHTML = '';
    if (!posts.length) {
        postsGrid.innerHTML = `<div class="posts-empty"><i class="fas fa-images"></i><p>No posts in this category.</p></div>`;
        return;
    }
    posts.forEach(post => {
        const cell = buildPostCell(post);
        postsGrid.appendChild(cell);
        bindCellEvents(cell, post);
    });
}

function buildPostCell(post) {
    const cell = document.createElement('div');
    cell.className = 'post-cell';
    cell.dataset.postId  = post.id;
    cell.dataset.category = post.category;

    let mediaFiles = post.media_files && post.media_files.length ? post.media_files : [{ url: post.media_url, resource_type: post.resource_type }];
    let firstMedia = mediaFiles[0];
    let mediaUrl = firstMedia.url || '';
    const isVid = firstMedia.resource_type === 'video' || isVideo(mediaUrl);
    
    if (mediaUrl.includes('/auto/')) {
        mediaUrl = mediaUrl.replace('/auto/', isVid ? '/video/' : '/image/');
    }

    let mediaHtml = '';
    if (isVid) {
        mediaHtml = `<video src="${mediaUrl}" muted preload="metadata" loading="lazy"></video>
                     <span class="post-video-badge"><i class="fas fa-play-circle"></i></span>`;
    } else {
        mediaHtml = `<img src="${mediaUrl}" alt="Post" loading="lazy">`;
    }

    let carouselHtml = mediaFiles.length > 1 ? `<span class="post-carousel-badge"><i class="fas fa-copy"></i></span>` : '';

    const deleteBtn = IS_OWNER
        ? `<button class="post-delete-btn" data-post-id="${post.id}" title="Delete"><i class="fas fa-trash-alt"></i></button>`
        : '';

    cell.innerHTML = `
        ${mediaHtml}
        ${carouselHtml}
        <div class="post-cell-overlay">
            <span><i class="fas fa-heart"></i> ${post.likes_count}</span>
            <span><i class="fas fa-comment"></i> ${post.comments_count}</span>
        </div>
        <span class="post-cat-badge">${escHtml(post.category_display)}</span>
        ${deleteBtn}
    `;
    return cell;
}

function bindCellEvents(cell, post) {
    // Click to open post modal
    cell.addEventListener('click', (e) => {
        if (e.target.closest('.post-delete-btn')) return;
        showLoadingModal(post.id);
        openPostModal(post);
    });
    // Delete
    const delBtn = cell.querySelector('.post-delete-btn');
    if (delBtn) {
        delBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!confirm('Delete this post?')) return;
            try {
                const res = await fetch(URLS.deletePost(post.id), {
                    method : 'POST',
                    headers: csrfHeaders(),
                });
                const data = await res.json();
                if (data.success) {
                    cell.remove();
                    if (!postsGrid.querySelector('.post-cell')) {
                        postsGrid.innerHTML = `<div class="posts-empty" id="emptyState">
                            <i class="fas fa-images"></i>
                            <p>No posts yet. Click <strong>Add Post</strong> to share your work!</p>
                        </div>`;
                    }
                }
            } catch (err) { console.error(err); }
        });
    }
}

/* Bind existing cells (server-rendered) */
document.querySelectorAll('.post-cell[data-post-id]').forEach(cell => {
    const postId = parseInt(cell.dataset.postId);
    // Fetch post data lazily only when clicked
    cell.addEventListener('click', async (e) => {
        if (e.target.closest('.post-delete-btn')) return;
        showLoadingModal(postId); // Instantiate skeleton loading box before fetch
        try {
            const res  = await fetch(`/api/profile/${PROFILE_USERNAME}/posts/`);
            const data = await res.json();
            if (data.success) {
                const post = data.posts.find(p => p.id === postId);
                // IF user hasn't cancelled the modal by clicking outside while it fetched
                if (post && currentPostId === postId) {
                    openPostModal(post); 
                }
            }
        } catch (err) { 
            console.error(err); 
            if (currentPostId === postId) closePostModal(); 
        }
    });
    // Delete button (server-rendered cells)
    const delBtn = cell.querySelector('.post-delete-btn');
    if (delBtn) {
        delBtn.addEventListener('click', async (e) => {
            e.stopPropagation();
            if (!confirm('Delete this post?')) return;
            try {
                const res  = await fetch(URLS.deletePost(postId), {
                    method : 'POST',
                    headers: csrfHeaders(),
                });
                const data = await res.json();
                if (data.success) {
                    cell.remove();
                    if (!postsGrid.querySelector('.post-cell')) {
                        postsGrid.innerHTML = `<div class="posts-empty">
                            <i class="fas fa-images"></i>
                            <p>No posts yet. Click <strong>Add Post</strong> to share your work!</p>
                        </div>`;
                    }
                }
            } catch (err) { console.error(err); }
        });
    }
});

/* ── Utility ─────────────────────────────────────────────────────────── */
function escHtml(str) {
    if (!str) return '';
    return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

function timeAgo(date) {
    const secs = Math.floor((Date.now() - date) / 1000);
    if (secs < 60)  return 'just now';
    if (secs < 3600) return Math.floor(secs / 60) + 'm';
    if (secs < 86400) return Math.floor(secs / 3600) + 'h';
    return Math.floor(secs / 86400) + 'd';
}
