document.addEventListener('DOMContentLoaded', function () {
    const form = document.getElementById('editProfileForm');
    const saveBtn = document.getElementById('saveBtn');
    const loadingOverlay = document.getElementById('loadingOverlay');

    const usernameInput = document.getElementById('username');
    const emailInput = document.getElementById('email');
    const usernameAvailability = document.getElementById('usernameAvailability');
    const emailAvailability = document.getElementById('emailAvailability');
    const sendOtpBtn = document.getElementById('sendOtpBtn');
    const otpSection = document.getElementById('otpSection');
    const emailOtpInput = document.getElementById('emailOtp');
    const verifyOtpBtn = document.getElementById('verifyOtpBtn');
    const otpStatus = document.getElementById('otpStatus');

    const changePasswordBtn = document.getElementById('changePasswordBtn');
    const currentPasswordInput = document.getElementById('currentPassword');
    const newPasswordInput = document.getElementById('newPassword');
    const confirmPasswordInput = document.getElementById('confirmPassword');
    const passwordTooltip = document.getElementById('passwordTooltip');

    const editPhotoBtn = document.getElementById('editPhotoBtn');
    const photoFileInput = document.getElementById('photoFileInput');
    const cropModal = document.getElementById('cropModal');
    const cropImage = document.getElementById('cropImage');
    const cropConfirmBtn = document.getElementById('cropConfirmBtn');
    const cropCancelBtn = document.getElementById('cropCancelBtn');
    const cropModalClose = document.getElementById('cropModalClose');
    const cropSpinner = document.getElementById('cropSpinner');

    let usernameTimeout = null;
    let emailTimeout = null;
    let emailVerified = false;
    let cropper = null;

    const originalUsername = usernameInput.getAttribute('data-original');
    const originalEmail = emailInput.getAttribute('data-original');
    const csrfToken = form.querySelector('[name=csrfmiddlewaretoken]').value;

    function showMessage(message, type) {
        document.querySelectorAll('.error-message, .success-message').forEach(el => el.remove());
        const div = document.createElement('div');
        div.className = type === 'success' ? 'success-message show' : 'error-message show';
        div.textContent = message;
        form.parentNode.insertBefore(div, form);
        if (type !== 'success') {
            setTimeout(() => {
                div.classList.remove('show');
                setTimeout(() => div.remove(), 300);
            }, 5000);
        }
    }

    function resetOtpState() {
        emailVerified = false;
        otpSection.style.display = 'none';
        sendOtpBtn.style.display = 'none';
        emailOtpInput.value = '';
        emailOtpInput.disabled = false;
        verifyOtpBtn.disabled = false;
        otpStatus.classList.remove('show', 'success', 'error', 'checking');
    }

    // Reuse shared availability checker from account_validation.js
    usernameInput.addEventListener('input', function () {
        const username = this.value.trim();
        clearTimeout(usernameTimeout);
        if (!username || username === originalUsername) {
            usernameAvailability.classList.remove('show', 'available', 'taken', 'checking');
            return;
        }
        AccountValidation.setAvailabilityState(usernameAvailability, 'checking', '⏳ Checking availability...');
        usernameTimeout = setTimeout(() => {
            AccountValidation.checkUsernameAvailability(username, csrfToken, usernameAvailability)
                .catch(() => usernameAvailability.classList.remove('show', 'checking', 'available', 'taken'));
        }, 500);
    });

    emailInput.addEventListener('input', function () {
        const email = this.value.trim();
        clearTimeout(emailTimeout);
        resetOtpState();

        if (!email || email === originalEmail) {
            emailAvailability.classList.remove('show', 'available', 'taken', 'checking');
            return;
        }

        AccountValidation.setAvailabilityState(emailAvailability, 'checking', '⏳ Checking availability...');
        emailTimeout = setTimeout(() => {
            AccountValidation.checkEmailAvailability(email, csrfToken, emailAvailability)
                .then((data) => {
                    if (data.available) {
                        sendOtpBtn.style.display = 'block';
                        sendOtpBtn.disabled = false;
                    }
                })
                .catch(() => {
                    emailAvailability.classList.remove('show', 'checking', 'available', 'taken');
                    sendOtpBtn.style.display = 'none';
                });
        }, 500);
    });

    sendOtpBtn.addEventListener('click', function () {
        const email = emailInput.value.trim();
        if (!email || email === originalEmail) return;
        sendOtpBtn.disabled = true;
        AccountValidation.setAvailabilityState(emailAvailability, 'checking', '⏳ Sending OTP...');
        fetch('/profile/send-email-otp/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: `email=${encodeURIComponent(email)}`
        })
            .then(r => r.json())
            .then(data => {
                if (!data.success) throw new Error(data.error || 'Failed to send OTP');
                AccountValidation.setAvailabilityState(emailAvailability, 'available', '✓ OTP sent! Check your new email.');
                otpSection.style.display = 'block';
                sendOtpBtn.style.display = 'none';
            })
            .catch(err => {
                AccountValidation.setAvailabilityState(emailAvailability, 'taken', `✗ ${err.message}`);
                sendOtpBtn.disabled = false;
            });
    });

    verifyOtpBtn.addEventListener('click', function () {
        const otp = emailOtpInput.value.trim();
        if (!otp || otp.length !== 6) {
            otpStatus.textContent = '✗ Please enter 6-digit OTP';
            otpStatus.classList.add('show', 'error');
            otpStatus.classList.remove('success', 'checking');
            return;
        }
        otpStatus.textContent = '⏳ Verifying OTP...';
        otpStatus.classList.add('show', 'checking');
        otpStatus.classList.remove('success', 'error');
        verifyOtpBtn.disabled = true;

        fetch('/profile/verify-email-otp/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: `otp=${encodeURIComponent(otp)}`
        })
            .then(r => r.json())
            .then(data => {
                if (!data.success) throw new Error(data.error || 'Invalid OTP');
                otpStatus.textContent = '✓ Email verified successfully!';
                otpStatus.classList.remove('checking', 'error');
                otpStatus.classList.add('success');
                emailVerified = true;
                emailOtpInput.disabled = true;
                verifyOtpBtn.disabled = true;
                AccountValidation.setAvailabilityState(emailAvailability, 'available', '✓ Email verified and ready to update');
            })
            .catch(err => {
                otpStatus.textContent = `✗ ${err.message}`;
                otpStatus.classList.remove('checking', 'success');
                otpStatus.classList.add('error');
                verifyOtpBtn.disabled = false;
            });
    });

    form.addEventListener('submit', async function (e) {
        e.preventDefault();
        if (usernameAvailability.classList.contains('taken') || emailAvailability.classList.contains('taken')) {
            showMessage('Please fix the errors before saving.', 'error');
            return;
        }

        const currentEmail = emailInput.value.trim();
        if (currentEmail !== originalEmail && !emailVerified) {
            showMessage('Please verify your new email address with OTP first.', 'error');
            return;
        }

        loadingOverlay.classList.add('active');
        saveBtn.disabled = true;
        const formData = new FormData(form);
        formData.append('email_verified', emailVerified ? 'true' : 'false');

        try {
            const response = await fetch('/profile/update/', {
                method: 'POST',
                body: formData,
                headers: { 'X-CSRFToken': csrfToken }
            });
            const data = await response.json();
            if (!data.success) throw new Error(data.error || 'Failed to update profile');
            showMessage('Profile updated successfully! Redirecting...', 'success');
            setTimeout(() => { window.location.href = '/dashboard/'; }, 1000);
        } catch (error) {
            loadingOverlay.classList.remove('active');
            saveBtn.disabled = false;
            showMessage(error.message || 'An error occurred. Please try again.', 'error');
        }
    });

    // Password toggle
    document.querySelectorAll('.toggle-password').forEach(btn => {
        btn.addEventListener('click', function () {
            const wrapper = this.closest('.password-input-wrapper');
            const input = wrapper.querySelector('input');
            const eye = this.querySelector('.fa-eye');
            const eyeSlash = this.querySelector('.fa-eye-slash');
            const isPassword = input.type === 'password';
            input.type = isPassword ? 'text' : 'password';
            eye.style.display = isPassword ? 'none' : '';
            eyeSlash.style.display = isPassword ? '' : 'none';
        });
    });

    // Reuse password checklist logic from shared module
    if (newPasswordInput && passwordTooltip) {
        newPasswordInput.addEventListener('focus', () => passwordTooltip.classList.add('show'));
        newPasswordInput.addEventListener('blur', () => setTimeout(() => passwordTooltip.classList.remove('show'), 200));
        newPasswordInput.addEventListener('input', () => AccountValidation.validatePassword(newPasswordInput.value));
        AccountValidation.validatePassword('');
    }

    changePasswordBtn.addEventListener('click', async function () {
        const currentPassword = currentPasswordInput.value;
        const newPassword = newPasswordInput.value;
        const confirmPassword = confirmPasswordInput.value;

        if (!currentPassword || !newPassword || !confirmPassword) {
            showMessage('Please fill all password fields.', 'error');
            return;
        }
        if (!AccountValidation.isPasswordValid(newPassword)) {
            showMessage('New password does not meet requirements.', 'error');
            return;
        }
        if (newPassword !== confirmPassword) {
            showMessage('New password and confirm password do not match.', 'error');
            return;
        }

        changePasswordBtn.disabled = true;
        try {
            const body = new URLSearchParams({
                current_password: currentPassword,
                new_password: newPassword,
                confirm_password: confirmPassword
            });
            const response = await fetch('/profile/change-password/', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': csrfToken
                },
                body
            });
            const data = await response.json();
            if (!data.success) throw new Error(data.error || 'Failed to update password');
            showMessage('Password updated successfully.', 'success');
            currentPasswordInput.value = '';
            newPasswordInput.value = '';
            confirmPasswordInput.value = '';
            AccountValidation.validatePassword('');
        } catch (err) {
            showMessage(err.message, 'error');
        } finally {
            changePasswordBtn.disabled = false;
        }
    });

    // Photo upload/crop flow (same as profile page)
    function openModal(el) { el.classList.add('open'); document.body.style.overflow = 'hidden'; }
    function closeModal(el) { el.classList.remove('open'); document.body.style.overflow = ''; }

    editPhotoBtn.addEventListener('click', () => photoFileInput.click());

    photoFileInput.addEventListener('change', function () {
        const file = this.files[0];
        if (!file) return;
        if (!['image/jpeg', 'image/png'].includes(file.type)) {
            showMessage('Only JPEG or PNG images are accepted.', 'error');
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            cropImage.src = e.target.result;
            openModal(cropModal);
            if (cropper) { cropper.destroy(); cropper = null; }
            cropper = new Cropper(cropImage, {
                aspectRatio: 1,
                viewMode: 1,
                dragMode: 'move',
                autoCropArea: 0.8,
                responsive: true
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

    cropConfirmBtn.addEventListener('click', function () {
        if (!cropper) return;
        const canvas = cropper.getCroppedCanvas({ width: 256, height: 256 });
        if (!canvas) return;

        cropConfirmBtn.disabled = true;
        cropSpinner.classList.add('active');

        canvas.toBlob(async (blob) => {
            const fd = new FormData();
            fd.append('photo', blob, 'profile.jpg');
            try {
                const res = await fetch('/profile/update-photo/', {
                    method: 'POST',
                    headers: { 'X-CSRFToken': csrfToken },
                    body: fd
                });
                const data = await res.json();
                if (!data.success) throw new Error(data.error || 'Upload failed');

                const wrap = document.querySelector('.profile-avatar-wrap');
                let imgEl = document.getElementById('profileAvatarImg');
                const initEl = document.getElementById('profileAvatarInitials');
                if (!imgEl) {
                    imgEl = document.createElement('img');
                    imgEl.id = 'profileAvatarImg';
                    imgEl.className = 'profile-avatar';
                    imgEl.alt = 'Profile photo';
                    if (initEl) initEl.replaceWith(imgEl);
                    else wrap.prepend(imgEl);
                }
                imgEl.src = `${data.url}?t=${Date.now()}`;

                const sidebarAvatar = document.querySelector('.user-avatar-small');
                if (sidebarAvatar && sidebarAvatar.tagName === 'IMG') {
                    sidebarAvatar.src = `${data.url}?t=${Date.now()}`;
                }

                closeModal(cropModal);
                cropper.destroy();
                cropper = null;
                photoFileInput.value = '';
                showMessage('Profile photo updated successfully.', 'success');
            } catch (err) {
                showMessage(err.message || 'Upload failed.', 'error');
            } finally {
                cropConfirmBtn.disabled = false;
                cropSpinner.classList.remove('active');
            }
        }, 'image/jpeg', 0.92);
    });
});
