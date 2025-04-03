// static/enigmas/js/magnetic-buttons.js (o aggiungi a un file JS esistente)

document.addEventListener('DOMContentLoaded', () => {
    const magneticButtons = document.querySelectorAll('.magnetic-btn');

    magneticButtons.forEach(button => {
        button.addEventListener('mousemove', (e) => {
            const rect = button.getBoundingClientRect();
            // Calcola la posizione X e Y del mouse DENTRO il bottone (0 a 100%)
            const x = ((e.clientX - rect.left) / rect.width) * 100;
            const y = ((e.clientY - rect.top) / rect.height) * 100;

            // Aggiorna le variabili CSS --x e --y
            button.style.setProperty('--x', `${x}%`);
            button.style.setProperty('--y', `${y}%`);
        });

        button.addEventListener('mouseleave', () => {
            // Opzionale: Resetta la posizione al centro quando il mouse esce
            // per una transizione di ritorno più fluida all'inizio del prossimo hover
            // button.style.setProperty('--x', `50%`);
            // button.style.setProperty('--y', `50%`);
            // Nota: Il CSS già fa tornare a posto con la transizione su :hover,
            // quindi questo reset potrebbe non essere strettamente necessario
            // a meno che non si voglia un punto di partenza fisso per l'alone.
        });
    });
});