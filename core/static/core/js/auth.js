// Form validation and interaction effects
document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('.auth-form');
    const inputs = document.querySelectorAll('.form-group input, .form-group select');
    
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
    let usernameTimeout;
    
    if (usernameInput && usernameAvailability) {
        usernameInput.addEventListener('input', function() {
            const username = this.value.trim();
            
            // Clear previous timeout
            clearTimeout(usernameTimeout);
            
            // Reset message if empty
            if (username.length === 0) {
                usernameAvailability.classList.remove('show', 'available', 'taken', 'checking');
                return;
            }
            
            // Show checking message
            if (username.length > 0) {
                usernameAvailability.textContent = '⏳ Checking availability...';
                usernameAvailability.classList.add('show', 'checking');
                usernameAvailability.classList.remove('available', 'taken');
                
                // Debounce - wait 500ms after user stops typing
                usernameTimeout = setTimeout(() => {
                    checkUsernameAvailability(username);
                }, 500);
            }
        });
    }
    
    // Real-time email availability check
    const emailInput = document.getElementById('email');
    const emailAvailability = document.getElementById('emailAvailability');
    let emailTimeout;
    
    if (emailInput && emailAvailability) {
        emailInput.addEventListener('input', function() {
            const email = this.value.trim();
            
            // Clear previous timeout
            clearTimeout(emailTimeout);
            
            // Reset message if empty
            if (email.length === 0) {
                emailAvailability.classList.remove('show', 'available', 'taken', 'checking');
                return;
            }
            
            // Basic email format validation
            const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
            if (emailRegex.test(email)) {
                emailAvailability.textContent = '⏳ Checking availability...';
                emailAvailability.classList.add('show', 'checking');
                emailAvailability.classList.remove('available', 'taken');
                
                // Debounce - wait 500ms after user stops typing
                emailTimeout = setTimeout(() => {
                    checkEmailAvailability(email);
                }, 500);
            }
        });
    }
    
    // Form submission handling
    if (form) {
        form.addEventListener('submit', function(e) {
            const button = form.querySelector('.btn-primary');
            
            // Check if on signup page and validate password
            if (passwordInput && passwordTooltip) {
                if (!isPasswordValid(passwordInput.value)) {
                    e.preventDefault();
                    alert('Please ensure your password meets all requirements.');
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
