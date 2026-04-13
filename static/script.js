document.addEventListener('DOMContentLoaded', () => {
    // 1. Funcionalidade para o Cabeçalho Fixo (Sticky Header)
    const mainHeader = document.getElementById('mainHeader');
    if (mainHeader) {
        let lastScrollY = window.scrollY;

        window.addEventListener('scroll', () => {
            if (window.scrollY > 0) { // Adiciona a classe 'sticky' se houver scroll
                mainHeader.classList.add('sticky');
            } else { // Remove a classe 'sticky' se estiver no topo
                mainHeader.classList.remove('sticky');
            }

            // Opcional: Esconder/Mostrar cabeçalho ao rolar para cima/baixo
            // if (window.scrollY > lastScrollY) {
            //     // Rolando para baixo
            //     mainHeader.style.transform = 'translateY(-100%)';
            // } else {
            //     // Rolando para cima
            //     mainHeader.style.transform = 'translateY(0)';
            // }
            // lastScrollY = window.scrollY;
        });
    }

    // 2. Funcionalidade do Menu Mobile (Toggle)
    const navToggle = document.querySelector('.nav-toggle');
    const navList = document.querySelector('.main-nav .nav-list');
    const navLinks = document.querySelectorAll('.main-nav .nav-list > li > a:not(.has-dropdown a)');

    if (navToggle && navList) {
        navToggle.addEventListener('click', () => {
            navList.classList.toggle('active');
            const icon = navToggle.querySelector('i');
            icon.classList.toggle('fa-bars');
            icon.classList.toggle('fa-times');
        });

        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (navList.classList.contains('active')) {
                    navList.classList.remove('active');
                    const icon = navToggle.querySelector('i');
                    icon.classList.remove('fa-times');
                    icon.classList.add('fa-bars');
                }
            });
        });
    }

    // Dropdown mobile toggle
    document.querySelectorAll('.has-dropdown > a').forEach(link => {
        link.addEventListener('click', (e) => {
            if (window.innerWidth <= 992) {
                e.preventDefault();
                const parent = link.parentElement;
                const wasOpen = parent.classList.contains('open');
                document.querySelectorAll('.has-dropdown.open').forEach(d => d.classList.remove('open'));
                if (!wasOpen) parent.classList.add('open');
            }
        });
    });

    // 3. Atualizar ano no rodapé
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }

    // 4. Lógica para o formulário de Contato
    const simpleContactForm = document.querySelector('.simple-contact-form');

    if (simpleContactForm) {
        // Criar div de mensagem se não existir
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
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.status === 'success') {
                    contactMessage.textContent = result.message;
                    contactMessage.className = 'contact-form-message success';
                    contactMessage.style.cssText = 'display: block; padding: 12px; margin-top: 15px; border-radius: 6px; background: #d4edda; color: #155724;';
                    simpleContactForm.reset();
                } else {
                    contactMessage.textContent = result.message;
                    contactMessage.className = 'contact-form-message error';
                    contactMessage.style.cssText = 'display: block; padding: 12px; margin-top: 15px; border-radius: 6px; background: #f8d7da; color: #721c24;';
                }

                setTimeout(() => {
                    contactMessage.style.display = 'none';
                }, 7000);

            } catch (error) {
                contactMessage.textContent = 'Erro ao enviar. Tente novamente.';
                contactMessage.className = 'contact-form-message error';
                contactMessage.style.cssText = 'display: block; padding: 12px; margin-top: 15px; border-radius: 6px; background: #f8d7da; color: #721c24;';
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }
});