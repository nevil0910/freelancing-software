// Form validation and interaction effects
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('.auth-form');
    const inputs = document.querySelectorAll('.form-group input, .form-group select');

    function showFormError(message) {
        if (!form) return;
        const oldMessage = document.querySelector('.auth-card .error-message.client-side-error');
        if (oldMessage) {
            oldMessage.remove();
        }

        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message show client-side-error';
        errorDiv.innerHTML = `<span class="error-icon">⚠️</span><span>${message}</span>`;
        form.parentNode.insertBefore(errorDiv, form);
    }
    
    // Add focus effects to form inputs
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.parentElement.classList.add('focused');
        });
        
        input.addEventListener('blur', function() {
            this.parentElement.classList.remove('focused');
        });
    });
    
    // Password tooltip functionality
    const passwordInput = document.getElementById('password');
    const passwordTooltip = document.getElementById('passwordTooltip');
    
    // Toggle password visibility for all password fields
    const togglePasswordButtons = document.querySelectorAll('.toggle-password');
    togglePasswordButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();

            // Find the password input in the same wrapper
            const wrapper = this.closest('.password-input-wrapper');
            const passwordField = wrapper.querySelector('input[type="password"], input[type="text"]');

            if (passwordField) {
                const isPassword = passwordField.getAttribute('type') === 'password';
                passwordField.setAttribute('type', isPassword ? 'text' : 'password');

                // Swap icons
                const eyeIcon = this.querySelector('.fa-eye');
                const eyeSlashIcon = this.querySelector('.fa-eye-slash');
                if (eyeIcon && eyeSlashIcon) {
                    eyeIcon.style.display = isPassword ? 'none' : '';
                    eyeSlashIcon.style.display = isPassword ? '' : 'none';
                }
            }
        });
    });
    
    if (passwordInput && passwordTooltip) {
        // Show tooltip on focus
        passwordInput.addEventListener('focus', function() {
            passwordTooltip.classList.add('show');
        });
        
        // Hide tooltip on blur (with delay)
        passwordInput.addEventListener('blur', function() {
            setTimeout(() => {
                passwordTooltip.classList.remove('show');
            }, 200);
        });
        
        // Validate password in real-time
        passwordInput.addEventListener('input', function() {
            validatePassword(this.value);
        });
        
        // Show initial state
        validatePassword('');
    }
    
    // Real-time username availability check
    const usernameInput = document.getElementById('username');
    const usernameAvailability = document.getElementById('usernameAvailability');

    if (usernameInput && usernameAvailability) {
        usernameInput.addEventListener('focus', function() {
            usernameAvailability.classList.remove('show', 'available', 'taken', 'checking');
        });
        usernameInput.addEventListener('blur', function() {
            const raw = this.value.trim();
            const username = raw.toLowerCase();
            this.value = username;

            // Reset message if empty
            if (username.length === 0) {
                usernameAvailability.classList.remove('show', 'available', 'taken', 'checking');
                return;
            }
            if(username.length === 1) {
                usernameAvailability.textContent = 'Username must be at least 2 characters long.';
                usernameAvailability.classList.add('show', 'taken');
                usernameAvailability.classList.remove('checking', 'available');
                return;
            }

            // Show checking message
            const usernameRegex = /^[a-zA-Z0-9._-]{2,30}$/;
            if (usernameRegex.test(username)) {
                usernameAvailability.textContent = '⏳ Checking availability...';
                usernameAvailability.classList.add('show', 'checking');
                usernameAvailability.classList.remove('available', 'taken');
                checkUsernameAvailability(username);
            }
        });
    }
    
    // Real-time email availability check
    const emailInput = document.getElementById('email');
    const emailAvailability = document.getElementById('emailAvailability');
    
    if (emailInput && emailAvailability) {
        emailInput.addEventListener('focus', function() {
            emailAvailability.classList.remove('show', 'available', 'taken', 'checking');
        });
        emailInput.addEventListener('blur', function() {
            const email = this.value.trim();
            
            // Reset message if empty
            if (email.length === 0) {
                emailAvailability.classList.remove('show', 'available', 'taken', 'checking');
                return;
            }
            
            // Basic email format validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,3}$/;
            if (emailRegex.test(email)) {
                emailAvailability.textContent = '⏳ Checking availability...';
                emailAvailability.classList.add('show', 'checking');
                emailAvailability.classList.remove('available', 'taken');
                checkEmailAvailability(email);
            }
            else {
                emailAvailability.textContent = '✗ Please enter a valid email (example: name@example.com)';
                emailAvailability.classList.add('show', 'taken');
                emailAvailability.classList.remove('checking', 'available');
            }
        });
    }
    
    // Form submission handling
    if (form) {
        form.addEventListener('submit', function(e) {
            const button = form.querySelector('.btn-primary');
            const usernameField = document.getElementById('username');
            const emailField = document.getElementById('email');
            const usernamePattern = /^[a-zA-Z0-9._-]{2,30}$/;
            const emailPattern = /^[^\s@]+@[^\s@]+\.[a-zA-Z]{2,3}$/;

            if (usernameField) {
                usernameField.value = usernameField.value.trim().toLowerCase();
                if (emailField) {
                    if (!usernamePattern.test(usernameField.value)) {
                        e.preventDefault();
                        showFormError('Username must be at least 2 characters and use only letters, numbers, underscores, and hyphens.');
                        return false;
                    }
                } else {
                    const isUsername = usernamePattern.test(usernameField.value);
                    const isEmail = emailPattern.test(usernameField.value);
                    if (!isUsername && !isEmail) {
                        e.preventDefault();
                        showFormError('Enter a valid username or email.');
                        return false;
                    }
                }
            }

            if (emailField) {
                emailField.value = emailField.value.trim();
                if (!emailPattern.test(emailField.value)) {
                    e.preventDefault();
                    showFormError('Please enter a valid email (example: name@example.com).');
                    return false;
                }
            }
            
            // Check if on signup page and validate password
            if (passwordInput && passwordTooltip) {
                if (!isPasswordValid(passwordInput.value)) {
                    e.preventDefault();
                    showFormError('Please ensure your password meets all requirements.');
                    return false;
                }
            }
            
            button.textContent = 'Please wait...';
            button.disabled = true;
        });
    }
    
    // Auto-hide error messages after 5 seconds
    const errorMessage = document.querySelector('.error-message');
    if (errorMessage) {
        setTimeout(() => {
            errorMessage.style.opacity = '0';
            errorMessage.style.transform = 'translateY(-10px)';
            setTimeout(() => {
                errorMessage.style.display = 'none';
            }, 300);
        }, 5000);
    }
});

// Re-export shared utilities for backward compatibility
function validatePassword(password) {
    return window.AccountValidation.validatePassword(password);
}

function isPasswordValid(password) {
    return window.AccountValidation.isPasswordValid(password);
}

function checkUsernameAvailability(username) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const usernameAvailability = document.getElementById('usernameAvailability');
    return window.AccountValidation
        .checkUsernameAvailability(username, csrftoken, usernameAvailability)
        .catch(error => {
            console.error('Error checking username:', error);
            if (usernameAvailability) {
                usernameAvailability.classList.remove('show', 'checking', 'available', 'taken');
            }
        });
}

function checkEmailAvailability(email) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    const emailAvailability = document.getElementById('emailAvailability');
    return window.AccountValidation
        .checkEmailAvailability(email, csrftoken, emailAvailability)
        .catch(error => {
            console.error('Error checking email:', error);
            if (emailAvailability) {
                emailAvailability.classList.remove('show', 'checking', 'available', 'taken');
            }
        });
}
