/* ==========================================================================
   DAV CLOUD SOLUTIONS - AUTHENTICATION INTERACTIVE JAVASCRIPT
   Tech Stack: HTML5, CSS3, JavaScript (ES6+), Python Flask, MongoDB
   File: static/js/auth.js
   ========================================================================== */

document.addEventListener('DOMContentLoaded', function() {

    // ----------------------------------------------------------------------
    // 1. DYNAMIC REGISTRATION ROLE SELECTION & CONDITIONAL FIELDS
    // ----------------------------------------------------------------------
    const roleSelect = document.getElementById('role');
    const businessFields = document.getElementById('business-fields');
    const studentField = document.getElementById('student-field');
    const companyNameInput = document.getElementById('company_name');

    if (roleSelect && businessFields) {
        function updateRoleFields() {
            const selectedRole = roleSelect.value;

            if (selectedRole === 'business') {
                businessFields.style.display = 'block';
                if (studentField) studentField.style.display = 'none';
                if (companyNameInput) companyNameInput.setAttribute('required', 'required');
            } else {
                businessFields.style.display = 'none';
                if (studentField) studentField.style.display = 'block';
                if (companyNameInput) companyNameInput.removeAttribute('required');
            }
        }

        roleSelect.addEventListener('change', updateRoleFields);
        updateRoleFields(); // Execute on initial page load
    }

    // ----------------------------------------------------------------------
    // 2. CLIENT-SIDE PASSWORD MATCH & STRENGTH VALIDATION
    // ----------------------------------------------------------------------
    const registerForm = document.getElementById('register-form');
    const passwordInput = document.getElementById('password');
    const confirmPasswordInput = document.getElementById('confirm_password');

    if (registerForm && passwordInput && confirmPasswordInput) {
        registerForm.addEventListener('submit', function(e) {
            const password = passwordInput.value;
            const confirmPassword = confirmPasswordInput.value;

            // Password length check
            if (password.length < 8) {
                e.preventDefault();
                alert('Password must be at least 8 characters long.');
                passwordInput.focus();
                return false;
            }

            // Confirm password matching check
            if (password !== confirmPassword) {
                e.preventDefault();
                alert('Passwords do not match! Please re-enter your passwords.');
                confirmPasswordInput.focus();
                return false;
            }
        });

        // Real-time visual feedback on confirm password matching
        confirmPasswordInput.addEventListener('input', function() {
            if (confirmPasswordInput.value === '') {
                confirmPasswordInput.style.borderColor = 'var(--border-color)';
            } else if (confirmPasswordInput.value === passwordInput.value) {
                confirmPasswordInput.style.borderColor = 'var(--accent-emerald)';
            } else {
                confirmPasswordInput.style.borderColor = 'var(--accent-rose)';
            }
        });
    }

    // ----------------------------------------------------------------------
    // 3. PASSWORD VISIBILITY TOGGLE (LOGIN & REGISTER)
    // ----------------------------------------------------------------------
    const togglePasswordBtn = document.getElementById('toggle-password');
    const toggleIcon = document.getElementById('toggle-icon');

    if (togglePasswordBtn && passwordInput && toggleIcon) {
        togglePasswordBtn.addEventListener('click', function() {
            const isPassword = passwordInput.getAttribute('type') === 'password';
            passwordInput.setAttribute('type', isPassword ? 'text' : 'password');

            toggleIcon.classList.toggle('fa-eye', !isPassword);
            toggleIcon.classList.toggle('fa-eye-slash', isPassword);
        });
    }

});