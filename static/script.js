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
// script.js (Adicionar ao final)
// 6. Lógica de Edição Front-end (In-Place Editing)

// Verifica se a página está sendo visualizada por um administrador logado
// Para simplificar, vamos verificar se há um elemento de controle de edição no DOM 
// (mas o ideal seria que o Flask injetasse uma variável JS ou um elemento invisível)

// VAMOS ASSUMIR QUE O ADMIN ESTÁ LOGADO SE O FLASK INJETAR UM ELEMENTO ESPECÍFICO.
// VOLTE AO app.py e no 'index' injete a variável de sessão:
// return render_template('index.html', noticias=noticias, is_admin=session.get('logged_in'))
// No index.html, adicione: <input type="hidden" id="isAdmin" value="{{ 'true' if is_admin else 'false' }}">

const isAdminElement = document.getElementById('isAdmin');
const isAdmin = isAdminElement ? isAdminElement.value === 'true' : false;

if (isAdmin) {
    console.log("Modo de Edição Ativo.");
    
    // 1. Tornar todos os elementos com a classe 'editable-text' editáveis
    const editableTexts = document.querySelectorAll('.editable-text');
    
    editableTexts.forEach(element => {
        element.setAttribute('contenteditable', 'true');
        element.style.outline = '1px dashed red'; // Visual de que está editável
        
        // 2. Adicionar Event Listener para salvar ao perder o foco (blur)
        element.addEventListener('blur', function() {
            const postId = this.dataset.id;
            const fieldName = this.dataset.field;
            const newValue = this.textContent;
            
            console.log(`Salvando: ID ${postId}, Campo ${fieldName}, Valor: ${newValue}`);

            // Chamada API para o Flask para salvar
            fetch('/api/update_content', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    id: postId,
                    field: fieldName,
                    value: newValue
                }),
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    console.log('Salvo com sucesso!', data.message);
                    // Opcional: Feedback visual de sucesso
                    this.style.backgroundColor = '#d4edda';
                    setTimeout(() => {
                         this.style.backgroundColor = 'transparent';
                    }, 1500);
                } else {
                    console.error('Falha ao salvar:', data.message);
                    alert('Erro ao salvar: ' + data.message);
                }
            })
            .catch(error => {
                console.error('Erro de rede/servidor:', error);
                alert('Erro de conexão ao salvar.');
            });
        });
    });

    // 3. Lógica para EDIÇÃO/UPLOAD DE IMAGENS (Mais Complexo - Requer Formulário Flutuante)
    // Para simplificar, a edição da imagem continuará sendo feita no painel /admin/edit/ por enquanto.
    // Editar imagens in-place requer um formulário de upload flutuante e mais lógica.
    
}