// ===================================================================
// == PRUEBA DE BYPASS TOTAL                                      ==
// ===================================================================
document.addEventListener('DOMContentLoaded', () => {
    console.log("Página cargada. Asignando evento de prueba...");

    const startButton = document.getElementById('start-button');
        
    if (startButton) {
        startButton.addEventListener('click', () => {
            // Si ves esta alerta, ¡el botón funciona!
            alert("¡EL BOTÓN START FUNCIONA!"); 
        });
        console.log("Evento de prueba asignado al botón START.");
    } else {
        console.error("No se pudo encontrar el botón START (#start-button).");
    }
});
