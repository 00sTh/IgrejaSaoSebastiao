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
    const navLinks = document.querySelectorAll('.main-nav .nav-list a');

    if (navToggle && navList) {
        navToggle.addEventListener('click', () => {
            navList.classList.toggle('active');
            navToggle.querySelector('i').classList.toggle('fa-bars');
            navToggle.querySelector('i').classList.toggle('fa-times'); // Muda o ícone para 'X'
        });

        // Fechar o menu ao clicar em um link (útil para navegação de uma página só)
        navLinks.forEach(link => {
            link.addEventListener('click', () => {
                if (navList.classList.contains('active')) {
                    navList.classList.remove('active');
                    navToggle.querySelector('i').classList.remove('fa-times');
                    navToggle.querySelector('i').classList.add('fa-bars');
                }
            });
        });
    }

    // 3. Atualizar ano no rodapé
    const currentYearSpan = document.getElementById('currentYear');
    if (currentYearSpan) {
        currentYearSpan.textContent = new Date().getFullYear();
    }

    // 4. Lógica para o formulário de Agendamento de Confissão (simulado)
    const confessionForm = document.getElementById('confessionForm');
    const formMessage = document.getElementById('formMessage');

    if (confessionForm && formMessage) {
        confessionForm.addEventListener('submit', (event) => {
            event.preventDefault(); // Impede o envio padrão do formulário

            // Aqui você faria o envio dos dados para um backend (API, email, etc.)
            // Por enquanto, vamos apenas simular um sucesso/erro.

            // Simulação de envio (pode ser substituído por uma requisição AJAX/Fetch real)
            setTimeout(() => {
                const success = Math.random() > 0.1; // 90% de chance de sucesso para o exemplo

                if (success) {
                    formMessage.textContent = 'Sua solicitação de agendamento foi enviada com sucesso! Em breve, nossa secretaria entrará em contato para confirmar.';
                    formMessage.className = 'form-message success';
                    confessionForm.reset(); // Limpa o formulário
                } else {
                    formMessage.textContent = 'Ocorreu um erro ao enviar sua solicitação. Por favor, tente novamente mais tarde.';
                    formMessage.className = 'form-message error';
                }
                formMessage.style.display = 'block';

                // Esconde a mensagem após alguns segundos
                setTimeout(() => {
                    formMessage.style.display = 'none';
                }, 7000); // Mensagem visível por 7 segundos

            }, 1000); // Simula um atraso de 1 segundo para o "envio"
        });
    }

    // 5. Lógica para o formulário de Contato genérico (simulado)
    const simpleContactForm = document.querySelector('.simple-contact-form');
    // Você pode adicionar uma div de mensagem para este formulário também, se desejar
    // const contactFormMessage = document.getElementById('contactFormMessage');

    if (simpleContactForm) {
        simpleContactForm.addEventListener('submit', (event) => {
            event.preventDefault(); // Impede o envio padrão do formulário

            // Similar ao formulário de confissão, aqui seria a lógica de backend
            alert('Mensagem enviada! Em breve entraremos em contato.'); // Alerta simples para demonstração
            simpleContactForm.reset();
            // Se você adicionar uma div de mensagem, pode mostrá-la aqui
        });
    }
});