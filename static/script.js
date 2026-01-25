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

    // 4. Lógica para buscar horários disponíveis de confissão
    const mesSelect = document.getElementById('mes');
    const diaSelect = document.getElementById('dia');
    const horarioSelect = document.getElementById('horario');
    const horarioInfo = document.getElementById('horarioInfo');

    async function buscarHorariosDisponiveis() {
        const mes = mesSelect.value;
        const dia = diaSelect.value;

        if (!mes || !dia) {
            horarioSelect.disabled = true;
            horarioSelect.innerHTML = '<option value="">Primeiro selecione o mês e dia</option>';
            if (horarioInfo) horarioInfo.textContent = '';
            return;
        }

        // Mostrar loading
        horarioSelect.disabled = true;
        horarioSelect.innerHTML = '<option value="">Carregando horários...</option>';
        if (horarioInfo) horarioInfo.textContent = '';

        try {
            const response = await fetch(`/api/horarios-disponiveis?mes=${mes}&dia=${dia}`);
            const data = await response.json();

            if (data.status === 'success') {
                if (data.horarios.length > 0) {
                    horarioSelect.innerHTML = '<option value="">Selecione um horário</option>';
                    data.horarios.forEach(h => {
                        horarioSelect.innerHTML += `<option value="${h}">${h}</option>`;
                    });
                    horarioSelect.disabled = false;
                    if (horarioInfo) {
                        horarioInfo.textContent = `${data.horarios.length} horário(s) disponível(is) - ${data.dia_semana}`;
                        horarioInfo.style.color = '#28a745';
                    }
                } else {
                    horarioSelect.innerHTML = '<option value="">Nenhum horário disponível</option>';
                    if (horarioInfo) {
                        horarioInfo.textContent = `Não há confissões disponíveis neste dia (${data.dia_semana})`;
                        horarioInfo.style.color = '#dc3545';
                    }
                }
            } else {
                horarioSelect.innerHTML = '<option value="">Erro ao carregar</option>';
                if (horarioInfo) {
                    horarioInfo.textContent = data.message || 'Data inválida';
                    horarioInfo.style.color = '#dc3545';
                }
            }
        } catch (error) {
            horarioSelect.innerHTML = '<option value="">Erro de conexão</option>';
            if (horarioInfo) {
                horarioInfo.textContent = 'Erro ao buscar horários. Tente novamente.';
                horarioInfo.style.color = '#dc3545';
            }
        }
    }

    if (mesSelect && diaSelect && horarioSelect) {
        mesSelect.addEventListener('change', buscarHorariosDisponiveis);
        diaSelect.addEventListener('change', buscarHorariosDisponiveis);
    }

    // 5. Lógica para o formulário de Agendamento de Confissão
    const confessionForm = document.getElementById('confessionForm');
    const formMessage = document.getElementById('formMessage');

    if (confessionForm && formMessage) {
        confessionForm.addEventListener('submit', async (event) => {
            event.preventDefault();

            const submitBtn = confessionForm.querySelector('button[type="submit"]');
            const originalText = submitBtn.textContent;
            submitBtn.textContent = 'Enviando...';
            submitBtn.disabled = true;

            try {
                const formData = new FormData(confessionForm);
                const data = Object.fromEntries(formData.entries());

                const response = await fetch('/api/agendar-confissao', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (result.status === 'success') {
                    formMessage.textContent = result.message;
                    formMessage.className = 'form-message success';
                    confessionForm.reset();
                    // Resetar o select de horários após submit bem-sucedido
                    if (horarioSelect) {
                        horarioSelect.disabled = true;
                        horarioSelect.innerHTML = '<option value="">Primeiro selecione o mês e dia</option>';
                    }
                    if (horarioInfo) horarioInfo.textContent = '';
                } else {
                    formMessage.textContent = result.message;
                    formMessage.className = 'form-message error';
                }

                formMessage.style.display = 'block';
                setTimeout(() => {
                    formMessage.style.display = 'none';
                }, 7000);

            } catch (error) {
                formMessage.textContent = 'Erro ao enviar. Verifique sua conexão e tente novamente.';
                formMessage.className = 'form-message error';
                formMessage.style.display = 'block';
            } finally {
                submitBtn.textContent = originalText;
                submitBtn.disabled = false;
            }
        });
    }

    // 6. Lógica para o formulário de Contato
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