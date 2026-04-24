(function () {
    'use strict';

    function updateRequirement(elementId, isValid) {
        const element = document.getElementById(elementId);
        if (!element) return;
        const icon = element.querySelector('.requirement-icon');
        if (isValid) {
            element.classList.add('valid');
            element.classList.remove('invalid');
            if (icon) icon.textContent = '✓';
        } else {
            element.classList.add('invalid');
            element.classList.remove('valid');
            if (icon) icon.textContent = '✗';
        }
    }

    function validatePassword(password) {
        const requirements = {
            length: password.length >= 8,
            uppercase: /[A-Z]/.test(password),
            number: /[0-9]/.test(password),
            special: /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/`~;]/.test(password)
        };

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

    function setAvailabilityState(targetEl, kind, text) {
        if (!targetEl) return;
        targetEl.textContent = text;
        targetEl.classList.add('show');
        targetEl.classList.remove('checking', 'available', 'taken');
        if (kind) targetEl.classList.add(kind);
    }

    function checkUsernameAvailability(username, csrfToken, targetEl) {
        return fetch('/check-username/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: `username=${encodeURIComponent(username)}`
        })
            .then(response => response.json())
            .then(data => {
                if (targetEl) {
                    if (data.available) {
                        setAvailabilityState(targetEl, 'available', '✓ Username is available');
                    } else {
                        setAvailabilityState(targetEl, 'taken', '✗ Username is already taken');
                    }
                }
                return data;
            });
    }

    function checkEmailAvailability(email, csrfToken, targetEl) {
        return fetch('/check-email/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: `email=${encodeURIComponent(email)}`
        })
            .then(response => response.json())
            .then(data => {
                if (targetEl) {
                    if (data.error) {
                        setAvailabilityState(targetEl, 'taken', `✗ ${data.error}`);
                    } else if (data.available) {
                        setAvailabilityState(targetEl, 'available', '✓ Email is available');
                    } else {
                        setAvailabilityState(targetEl, 'taken', '✗ Email is already registered');
                    }
                }
                return data;
            });
    }

    window.AccountValidation = {
        updateRequirement,
        validatePassword,
        isPasswordValid,
        checkUsernameAvailability,
        checkEmailAvailability,
        setAvailabilityState
    };
})();
