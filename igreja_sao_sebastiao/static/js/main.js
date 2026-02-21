document.addEventListener('DOMContentLoaded', () => {
    // 1. Sticky Header
    const mainHeader = document.getElementById('mainHeader');
    if (mainHeader) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 0) {
                mainHeader.classList.add('sticky');
            } else {
                mainHeader.classList.remove('sticky');
            }
        });
    }

    // 2. Mobile Menu Toggle
    const navToggle = document.querySelector('.nav-toggle');
    const navList = document.querySelector('.main-nav .nav-list');
    const navLinks = document.querySelectorAll('.main-nav .nav-list a');

    if (navToggle && navList) {
        navToggle.addEventListener('click', () => {
            const isOpen = navList.classList.toggle('active');
            navToggle.setAttribute('aria-expanded', isOpen);
            navToggle.querySelector('i').classList.toggle('fa-bars');
            navToggle.querySelector('i').classList.toggle('fa-times');
        });

        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (navList.classList.contains('active')) {
                    navList.classList.remove('active');
                    navToggle.setAttribute('aria-expanded', 'false');
                    navToggle.querySelector('i').classList.remove('fa-times');
                    navToggle.querySelector('i').classList.add('fa-bars');
                }
            });
        });
    }

    // 3. Footer year
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }

    // 4. Contact Form (AJAX)
    const simpleContactForm = document.querySelector('.simple-contact-form');

    if (simpleContactForm) {
        let contactMessage = simpleContactForm.querySelector('.contact-form-message');
        if (!contactMessage) {
            contactMessage = document.createElement('div');
            contactMessage.className = 'contact-form-message';
            contactMessage.style.display = 'none';
            simpleContactForm.appendChild(contactMessage);
        }

        simpleContactForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const submitBtn = simpleContactForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Enviando...';
            submitBtn.disabled = true;

            try {
                const formData = new FormData(simpleContactForm);
                const data = Object.fromEntries(formData.entries());

                const response = await fetch('/api/enviar-mensagem', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.status === 'success') {
                    contactMessage.textContent = result.message;
                    contactMessage.style.cssText = 'display: block; padding: 12px; margin-top: 15px; border-radius: 6px; background: #d4edda; color: #155724;';
                    simpleContactForm.reset();
                } else {
                    contactMessage.textContent = result.message;
                    contactMessage.style.cssText = 'display: block; padding: 12px; margin-top: 15px; border-radius: 6px; background: #f8d7da; color: #721c24;';
                }

                setTimeout(() => {
                    contactMessage.style.display = 'none';
                }, 7000);

            } catch (error) {
                contactMessage.textContent = 'Erro ao enviar. Tente novamente.';
                contactMessage.style.cssText = 'display: block; padding: 12px; margin-top: 15px; border-radius: 6px; background: #f8d7da; color: #721c24;';
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }
});
