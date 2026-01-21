document.addEventListener('DOMContentLoaded', () => {

    // =========================
    // 1) TAB SWITCHING
    // =========================
    const loginTab = document.getElementById('loginTab');
    const registerTab = document.getElementById('registerTab');
    const loginForm = document.getElementById('loginForm');
    const registerForm = document.getElementById('registerForm');

    if (loginTab && registerTab && loginForm && registerForm) {
        loginTab.addEventListener('click', () => {
            loginTab.classList.add('active');
            registerTab.classList.remove('active');
            loginForm.classList.add('active');
            registerForm.classList.remove('active');
        });

        registerTab.addEventListener('click', () => {
            registerTab.classList.add('active');
            loginTab.classList.remove('active');
            registerForm.classList.add('active');
            loginForm.classList.remove('active');
        });
    }

    // =========================
    // 2) PASSWORD TOGGLE (LOGIN)
    // =========================
    const loginPasswordToggle = document.getElementById('loginPasswordToggle');
    const loginPasswordInput = document.getElementById('loginPassword');

    if (loginPasswordToggle && loginPasswordInput) {
        loginPasswordToggle.addEventListener('click', () => {
            const type = loginPasswordInput.getAttribute('type') === 'password' ? 'text' : 'password';
            loginPasswordInput.setAttribute('type', type);
            loginPasswordToggle.innerHTML = type === 'password'
                ? '<i class="fas fa-eye"></i>'
                : '<i class="fas fa-eye-slash"></i>';
        });
    }

    // =========================
    // 3) PASSWORD STRENGTH (REGISTER)
    // =========================
    const registerPassword = document.getElementById('registerPassword');
    const passwordStrengthFill = document.getElementById('passwordStrengthFill');
    const passwordStrengthText = document.getElementById('passwordStrengthText');

    if (registerPassword && passwordStrengthFill && passwordStrengthText) {
        registerPassword.addEventListener('input', function () {
            const password = this.value;
            let strength = 0;

            if (password.length >= 8) strength += 20;
            if (password.length >= 12) strength += 10;
            if (password.match(/[a-z]/)) strength += 15;
            if (password.match(/[A-Z]/)) strength += 15;
            if (password.match(/\d/)) strength += 15;
            if (password.match(/[^a-zA-Z\d]/)) strength += 15;
            if (password.length >= 16) strength += 10;

            let text = 'Very Weak';
            let color = '#ff1744';
            let widthPercentage = 20;

            if (strength >= 90) { text = 'Very Strong'; color = '#00d2ff'; widthPercentage = 100; }
            else if (strength >= 75) { text = 'Strong'; color = '#2ed573'; widthPercentage = 80; }
            else if (strength >= 50) { text = 'Medium'; color = '#ffa502'; widthPercentage = 60; }
            else if (strength >= 25) { text = 'Weak'; color = '#ff4757'; widthPercentage = 40; }

            passwordStrengthFill.style.width = `${widthPercentage}%`;
            passwordStrengthFill.style.backgroundColor = color;
            passwordStrengthText.textContent = text;
            passwordStrengthText.style.color = color;
        });
    }

    // =========================
    // 4) INPUT FOCUS ANIMATION
    // =========================
    const formInputs = document.querySelectorAll('.input-group input');
    formInputs.forEach(input => {
        input.addEventListener('focus', function () {
            this.parentElement.classList.add('focused');
        });

        input.addEventListener('blur', function () {
            if (!this.value) {
                this.parentElement.classList.remove('focused');
            }
        });

        if (input.value) {
            input.parentElement.classList.add('focused');
        }
    });

    // NOTE:
    // Tidak ada e.preventDefault() pada submit.
    // Jadi form akan POST ke Django sesuai action="{% url 'login' %}" / "{% url 'register' %}"
});
