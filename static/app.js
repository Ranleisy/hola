document.addEventListener("DOMContentLoaded", function () {
    // La siguiente sección está comentada para evitar conflictos con la nueva implementación
    /*
    const togglePassword = document.getElementById("togglePassword");
    const passwordField = document.getElementById("password");

    togglePassword.addEventListener("click", function () {
        // Cambiar el tipo de input entre 'password' y 'text'
        const isPasswordHidden = passwordField.type === "password"; // Verifica si está oculto
        passwordField.type = isPasswordHidden ? "text" : "password";

        // Alternar la clase 'active' en el ícono para reflejar el estado visual
        this.classList.toggle("active", isPasswordHidden);
    });
    */

    // Aquí puedes agregar cualquier comportamiento dinámico si es necesario
    // Ejemplo: Cambiar las iniciales con el nombre del usuario al iniciar sesión
    const userInitialsElement = document.getElementById('user-initials');
    if (userInitialsElement) {
        const userInitials = 'DN'; // Suponiendo que 'DN' son las iniciales del usuario
        userInitialsElement.textContent = userInitials;
    }
});