/**
 * Edit Profile Page JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
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

    let usernameCheckTimeout = null;
    let emailCheckTimeout = null;
    let emailVerified = false;
    let otpSent = false;

    // Get original values
    const originalUsername = usernameInput.getAttribute('data-original');
    const originalEmail = emailInput.getAttribute('data-original');

    // Username availability check
    if (usernameInput && usernameAvailability) {
        usernameInput.addEventListener('input', function() {
            const username = this.value.trim();
            
            // Clear previous timeout
            clearTimeout(usernameCheckTimeout);
            
            // If empty or same as original, hide message
            if (!username || username === originalUsername) {
                usernameAvailability.classList.remove('show', 'available', 'taken', 'checking');
                return;
            }
            
            // Show checking status
            usernameAvailability.textContent = '⏳ Checking availability...';
            usernameAvailability.classList.add('show', 'checking');
            usernameAvailability.classList.remove('available', 'taken');
            
            // Debounce the check (wait 500ms after user stops typing)
            usernameCheckTimeout = setTimeout(() => {
                checkUsernameAvailability(username);
            }, 500);
        });
    }

    // Email availability check (no auto-send OTP)
    if (emailInput && emailAvailability) {
        emailInput.addEventListener('input', function() {
            const email = this.value.trim();
            
            // Clear previous timeout
            clearTimeout(emailCheckTimeout);
            
            // Reset OTP state when email changes
            emailVerified = false;
            otpSent = false;
            otpSection.style.display = 'none';
            sendOtpBtn.style.display = 'none';
            otpStatus.classList.remove('show', 'success', 'error');
            
            // If empty or same as original, hide message
            if (!email || email === originalEmail) {
                emailAvailability.classList.remove('show', 'available', 'taken', 'checking');
                return;
            }
            
            // Show checking status
            emailAvailability.textContent = '⏳ Checking availability...';
            emailAvailability.classList.add('show', 'checking');
            emailAvailability.classList.remove('available', 'taken');
            
            // Debounce the check (wait 500ms after user stops typing)
            emailCheckTimeout = setTimeout(() => {
                checkEmailAvailability(email);
            }, 500);
        });
    }

    // Send OTP button click
    sendOtpBtn.addEventListener('click', function() {
        const email = emailInput.value.trim();
        if (email && email !== originalEmail) {
            sendOtpBtn.disabled = true;
            sendOTPToEmail(email);
        }
    });

    // Check username availability via AJAX
    function checkUsernameAvailability(username) {
        const csrftoken = form.querySelector('[name=csrfmiddlewaretoken]').value;
        
        fetch('/check-username/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrftoken
            },
            body: `username=${encodeURIComponent(username)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.available) {
                usernameAvailability.textContent = '✓ Username is available';
                usernameAvailability.classList.remove('checking', 'taken');
                usernameAvailability.classList.add('available');
            } else {
                usernameAvailability.textContent = '✗ Username is already taken';
                usernameAvailability.classList.remove('checking', 'available');
                usernameAvailability.classList.add('taken');
            }
        })
        .catch(error => {
            console.error('Error checking username:', error);
            usernameAvailability.classList.remove('show', 'checking', 'available', 'taken');
        });
    }

    // Check email availability via AJAX
    function checkEmailAvailability(email) {
        const csrftoken = form.querySelector('[name=csrfmiddlewaretoken]').value;
        
        fetch('/check-email/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrftoken
            },
            body: `email=${encodeURIComponent(email)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.available) {
                emailAvailability.textContent = '✓ Email is available';
                emailAvailability.classList.remove('checking', 'taken');
                emailAvailability.classList.add('available');
                
                // Show Send OTP button
                sendOtpBtn.style.display = 'block';
                sendOtpBtn.disabled = false;
            } else {
                emailAvailability.textContent = '✗ Email is already registered';
                emailAvailability.classList.remove('checking', 'available');
                emailAvailability.classList.add('taken');
                sendOtpBtn.style.display = 'none';
            }
        })
        .catch(error => {
            console.error('Error checking email:', error);
            emailAvailability.classList.remove('show', 'checking', 'available', 'taken');
            sendOtpBtn.style.display = 'none';
        });
    }

    // Send OTP to new email
    function sendOTPToEmail(email) {
        const csrftoken = form.querySelector('[name=csrfmiddlewaretoken]').value;
        
        // Show sending status
        emailAvailability.textContent = '⏳ Sending OTP...';
        emailAvailability.classList.add('checking');
        emailAvailability.classList.remove('available', 'taken');
        
        fetch('/profile/send-email-otp/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrftoken
            },
            body: `email=${encodeURIComponent(email)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                emailAvailability.textContent = '✓ OTP sent! Check your new email.';
                emailAvailability.classList.remove('checking');
                emailAvailability.classList.add('available');
                otpSection.style.display = 'block';
                sendOtpBtn.style.display = 'none';
                otpSent = true;
            } else {
                emailAvailability.textContent = '✗ ' + (data.error || 'Failed to send OTP');
                emailAvailability.classList.remove('checking', 'available');
                emailAvailability.classList.add('taken');
                sendOtpBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error sending OTP:', error);
            emailAvailability.textContent = '✗ Failed to send OTP';
            emailAvailability.classList.remove('checking', 'available');
            emailAvailability.classList.add('taken');
            sendOtpBtn.disabled = false;
        });
    }

    // Verify OTP button click
    verifyOtpBtn.addEventListener('click', function() {
        const otp = emailOtpInput.value.trim();
        
        if (!otp || otp.length !== 6) {
            otpStatus.textContent = '✗ Please enter 6-digit OTP';
            otpStatus.classList.add('show', 'error');
            otpStatus.classList.remove('success', 'checking');
            return;
        }
        
        // Show checking status
        otpStatus.textContent = '⏳ Verifying OTP...';
        otpStatus.classList.add('show', 'checking');
        otpStatus.classList.remove('success', 'error');
        verifyOtpBtn.disabled = true;
        
        const csrftoken = form.querySelector('[name=csrfmiddlewaretoken]').value;
        
        fetch('/profile/verify-email-otp/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrftoken
            },
            body: `otp=${encodeURIComponent(otp)}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                otpStatus.textContent = '✓ Email verified successfully!';
                otpStatus.classList.remove('checking', 'error');
                otpStatus.classList.add('success');
                emailVerified = true;
                emailOtpInput.disabled = true;
                verifyOtpBtn.disabled = true;
                
                // Update email availability message
                emailAvailability.textContent = '✓ Email verified and ready to update';
                emailAvailability.classList.remove('taken');
                emailAvailability.classList.add('available');
            } else {
                otpStatus.textContent = '✗ ' + (data.error || 'Invalid OTP');
                otpStatus.classList.remove('checking', 'success');
                otpStatus.classList.add('error');
                verifyOtpBtn.disabled = false;
            }
        })
        .catch(error => {
            console.error('Error verifying OTP:', error);
            otpStatus.textContent = '✗ Failed to verify OTP';
            otpStatus.classList.remove('checking', 'success');
            otpStatus.classList.add('error');
            verifyOtpBtn.disabled = false;
        });
    });

    // Form submission
    form.addEventListener('submit', async function(e) {
        e.preventDefault();

        // Check if username/email are taken before submitting
        if (usernameAvailability.classList.contains('taken') || 
            emailAvailability.classList.contains('taken')) {
            showMessage('Please fix the errors before saving', 'error');
            return;
        }

        // Check if email was changed but not verified
        const currentEmail = emailInput.value.trim();
        if (currentEmail !== originalEmail && !emailVerified) {
            showMessage('Please verify your new email address with the OTP sent to you.', 'error');
            return;
        }

        // Show loading overlay
        loadingOverlay.classList.add('active');
        saveBtn.disabled = true;

        const formData = new FormData(form);
        
        // Add email verification status
        formData.append('email_verified', emailVerified ? 'true' : 'false');

        try {
            const response = await fetch('/profile/update/', {
                method: 'POST',
                body: formData,
                headers: {
                    'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
                }
            });

            const data = await response.json();

            if (data.success) {
                // Show success message
                showMessage('Profile updated successfully! Redirecting...', 'success');
                
                // Redirect to dashboard after 1 second
                setTimeout(() => {
                    window.location.href = '/dashboard/';
                }, 1000);
            } else {
                // Hide loading and show error
                loadingOverlay.classList.remove('active');
                saveBtn.disabled = false;
                showMessage(data.error || 'Failed to update profile', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            loadingOverlay.classList.remove('active');
            saveBtn.disabled = false;
            showMessage('An error occurred. Please try again.', 'error');
        }
    });

    function showMessage(message, type) {
        // Remove existing messages
        const existingMessages = document.querySelectorAll('.error-message, .success-message');
        existingMessages.forEach(msg => msg.remove());

        // Create message element
        const messageDiv = document.createElement('div');
        messageDiv.className = type === 'success' ? 'success-message show' : 'error-message show';
        messageDiv.textContent = message;

        // Insert before form
        form.parentNode.insertBefore(messageDiv, form);

        // Auto-hide error messages after 5 seconds
        if (type === 'error') {
            setTimeout(() => {
                messageDiv.classList.remove('show');
                setTimeout(() => messageDiv.remove(), 300);
            }, 5000);
        }
    }
});
