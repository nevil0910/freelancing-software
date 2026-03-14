const otpBoxes = document.querySelectorAll('.otp-box');
const otpForm = document.getElementById('otpForm');
const otpHidden = document.getElementById('otpHidden');

// Auto-focus first box
otpBoxes[0].focus();

otpBoxes.forEach((box, index) => {
    // Only allow numbers
    box.addEventListener('input', function (e) {
        this.value = this.value.replace(/[^0-9]/g, '');

        if (this.value) {
            this.classList.add('filled');
            // Move to next box
            if (index < otpBoxes.length - 1) {
                otpBoxes[index + 1].focus();
            }
        } else {
            this.classList.remove('filled');
        }

        // Update hidden field
        updateOTP();
    });

    // Handle backspace
    box.addEventListener('keydown', function (e) {
        if (e.key === 'Backspace' && !this.value && index > 0) {
            otpBoxes[index - 1].focus();
            otpBoxes[index - 1].value = '';
            otpBoxes[index - 1].classList.remove('filled');
            updateOTP();
        }
    });

    // Handle paste
    box.addEventListener('paste', function (e) {
        e.preventDefault();
        const pastedData = e.clipboardData.getData('text').replace(/[^0-9]/g, '');

        for (let i = 0; i < pastedData.length && index + i < otpBoxes.length; i++) {
            otpBoxes[index + i].value = pastedData[i];
            otpBoxes[index + i].classList.add('filled');
        }

        updateOTP();

        // Focus last filled box or next empty
        const lastIndex = Math.min(index + pastedData.length, otpBoxes.length - 1);
        otpBoxes[lastIndex].focus();
    });
});

function updateOTP() {
    const otp = Array.from(otpBoxes).map(box => box.value).join('');
    otpHidden.value = otp;

    // Auto-submit when all boxes are filled
    if (otp.length === 6) {
        setTimeout(() => {
            otpForm.submit();
        }, 300);
    }
}