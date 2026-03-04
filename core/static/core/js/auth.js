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
                const type = passwordField.getAttribute('type') === 'password' ? 'text' : 'password';
                passwordField.setAttribute('type', type);
                
                // Toggle button class for styling
                this.classList.toggle('hide');
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
            if (username.length >= 3) {
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

// Password validation function
function validatePassword(password) {
    const requirements = {
        length: password.length >= 8,
        uppercase: /[A-Z]/.test(password),
        number: /[0-9]/.test(password),
        special: /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~;]/.test(password)
    };
    
    // Update UI for each requirement
    updateRequirement('req-length', requirements.length);
    updateRequirement('req-uppercase', requirements.uppercase);
    updateRequirement('req-number', requirements.number);
    updateRequirement('req-special', requirements.special);
    
    return Object.values(requirements).every(Boolean);
}

function isPasswordValid(password) {
    return password.length >= 8 &&
           /[A-Z]/.test(password) &&
           /[0-9]/.test(password) &&
           /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~;]/.test(password);
}

function updateRequirement(elementId, isValid) {
    const element = document.getElementById(elementId);
    if (element) {
        const icon = element.querySelector('.requirement-icon');
        if (isValid) {
            element.classList.add('valid');
            element.classList.remove('invalid');
            icon.textContent = '✓';
        } else {
            element.classList.add('invalid');
            element.classList.remove('valid');
            icon.textContent = '✗';
        }
    }
}

// Check username availability via AJAX
function checkUsernameAvailability(username) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
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
            const usernameAvailability = document.getElementById('usernameAvailability');
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
            const usernameAvailability = document.getElementById('usernameAvailability');
            usernameAvailability.classList.remove('show', 'checking', 'available', 'taken');
        });
}

// Check email availability via AJAX
function checkEmailAvailability(email) {
    const csrftoken = document.querySelector('[name=csrfmiddlewaretoken]').value;
    
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
            const emailAvailability = document.getElementById('emailAvailability');
            if (data.available) {
                emailAvailability.textContent = '✓ Email is available';
                emailAvailability.classList.remove('checking', 'taken');
                emailAvailability.classList.add('available');
            } else {
                emailAvailability.textContent = '✗ Email is already registered';
                emailAvailability.classList.remove('checking', 'available');
                emailAvailability.classList.add('taken');
            }
        })
        .catch(error => {
            console.error('Error checking email:', error);
            const emailAvailability = document.getElementById('emailAvailability');
            emailAvailability.classList.remove('show', 'checking', 'available', 'taken');
        });
}
