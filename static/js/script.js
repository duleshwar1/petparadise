// PetParadise Frontend Logic
document.addEventListener('DOMContentLoaded', () => {
    console.log('PetParadise Loaded!');

    // --- Smooth Scroll ---
    const links = document.querySelectorAll('a[href^="#"]');
    links.forEach(link => {
        link.addEventListener('click', (e) => {
            e.preventDefault();
            const targetId = link.getAttribute('href').substring(1);
            const targetElement = document.getElementById(targetId);
            if (targetElement) {
                window.scrollTo({
                    top: targetElement.offsetTop - 100,
                    behavior: 'smooth'
                });
            }
        });
    });

    // --- Flash Message Auto-dismiss ---
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.style.opacity = '0';
            alert.style.transform = 'translateY(-20px)';
            setTimeout(() => alert.remove(), 500);
        }, 5000);
    });

    // --- Hover effects for cards ---
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.addEventListener('mouseenter', () => {
            // Add subtle glow or extra effect if desired
        });
    });

    // --- Form Validation Helper ---
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', (e) => {
            // Simple validation could go here
            // e.preventDefault();
        });
    });

    // --- Mobile Menu Toggle ---
    const burger = document.querySelector('.burger'); // Add this to HTML if needed
    const navLinks = document.querySelector('.nav-links');
    if (burger) {
        burger.addEventListener('click', () => {
            navLinks.classList.toggle('nav-active');
            burger.classList.toggle('toggle');
        });
    }
});
