// Global AJAX setup
document.addEventListener('DOMContentLoaded', function() {
    // Flash message auto-hide
    let flashMessages = document.querySelectorAll('.alert');
    flashMessages.forEach(function(message) {
        setTimeout(function() {
            message.style.opacity = '0';
            setTimeout(function() {
                message.remove();
            }, 300);
        }, 3000);
    });
});

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('.registration-form');
    const password = document.getElementById('password');
    const confirmPassword = document.getElementById('confirm_password');

    // Password validation
    function validatePassword() {
        const regex = /^(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{8,}$/;
        const isValid = regex.test(password.value);
        
        if (!isValid) {
            password.setCustomValidity('Password must meet all requirements');
        } else {
            password.setCustomValidity('');
        }
    }

    // Confirm password validation
    function validateConfirmPassword() {
        if (confirmPassword.value !== password.value) {
            confirmPassword.setCustomValidity('Passwords do not match');
        } else {
            confirmPassword.setCustomValidity('');
        }
    }

    password.addEventListener('input', validatePassword);
    confirmPassword.addEventListener('input', validateConfirmPassword);

    form.addEventListener('submit', function(e) {
        validatePassword();
        validateConfirmPassword();
        
        if (!form.checkValidity()) {
            e.preventDefault();
            return false;
        }
    });
});

// Form validation
function validateForm(formElement) {
    let isValid = true;
    let requiredFields = formElement.querySelectorAll('[required]');
    
    requiredFields.forEach(function(field) {
        if (!field.value) {
            isValid = false;
            field.classList.add('invalid');
        } else {
            field.classList.remove('invalid');
        }
    });
    
    return isValid;
}

// Navigation menu for mobile
function toggleMobileMenu() {
    const navLinks = document.querySelector('.nav-links');
    navLinks.classList.toggle('active');
}