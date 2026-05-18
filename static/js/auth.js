document.addEventListener("DOMContentLoaded", () => {

    const passwordInput =
        document.getElementById("password");

    const strengthText =
        document.getElementById("password-strength");

    if (passwordInput && strengthText) {

        function updateStrength(message, className = "") {

            strengthText.textContent = message;
            strengthText.className = "";

            if (className) {
                strengthText.classList.add(className);
            }
        }

        function checkPasswordStrength(password) {

            if (password.length === 0) {
                updateStrength(
                    "Use at least 8 characters for better security."
                );
                return;
            }

            let score = 0;

            if (password.length >= 8) score++;
            if (password.length >= 12) score++;

            if (/[a-z]/.test(password) && /[A-Z]/.test(password)) {
                score++;
            }

            if (/\d/.test(password)) {
                score++;
            }

            if (/[^A-Za-z0-9]/.test(password)) {
                score++;
            }

            if (password.length < 8) {
                updateStrength("Weak password", "weak");
            }
            else if (score <= 3) {
                updateStrength("Medium password", "medium");
            }
            else {
                updateStrength("Strong password", "strong");
            }
        }

        checkPasswordStrength(passwordInput.value);

        passwordInput.addEventListener("input", () => {
            checkPasswordStrength(passwordInput.value.trim());
        });
    }


    // Show / Hide Password
    const toggleButtons =
        document.querySelectorAll(".toggle-password");

    toggleButtons.forEach(button => {

        button.addEventListener("click", () => {

            const input =
                button.previousElementSibling;

            if (input.type === "password") {
                input.type = "text";
                button.textContent = "🙈";
            }
            else {
                input.type = "password";
                button.textContent = "👁";
            }

        });

    });

});