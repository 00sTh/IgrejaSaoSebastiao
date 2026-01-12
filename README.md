# 🙏 Sistema de Gerenciamento - Igreja São Sebastião

Sistema completo de gerenciamento de site para a Igreja São Sebastião, com painel administrativo moderno e totalmente editável.

## 📋 Índice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Como Usar](#como-usar)
- [Painel Administrativo](#painel-administrativo)
- [Backup e Segurança](#backup-e-segurança)
- [Problemas Comuns](#problemas-comuns)
- [Suporte](#suporte)

## 🎯 Sobre o Projeto

Este é um sistema web completo desenvolvido especialmente para a Igreja São Sebastião em Ponte Nova/MG. O sistema permite gerenciar todo o conteúdo do site através de um painel administrativo intuitivo e moderno.

### Versão Atual: 2.0.0 Beta (Fase de Testes)

## ✨ Funcionalidades

### Site Público
- ✅ Página inicial moderna e responsiva
- ✅ Seção de notícias e eventos
- ✅ Horários de missas atualizáveis
- ✅ Galeria de fotos
- ✅ História e informações da paróquia
- ✅ Informações de contato e localização
- ✅ Agendamento de confissões
- ✅ Design totalmente responsivo

### Painel Administrativo
- ✅ Dashboard com estatísticas
- ✅ Gerenciamento completo de notícias e eventos
- ✅ Gerenciamento de horários de missas
- ✅ Edição de informações da paróquia
- ✅ Gerenciamento de galeria de fotos
- ✅ Configurações gerais editáveis
- ✅ Sistema de backup automático
- ✅ Interface moderna e intuitiva

## 💻 Requisitos

- Python 3.8 ou superior
- Navegador web moderno (Chrome, Firefox, Safari, Edge)
- Sistema operacional: Windows, Linux ou macOS

## 🚀 Instalação

### 1. Clone o Repositório (se aplicável)

```bash
git clone https://github.com/seu-usuario/IgrejaSaoSebastiao.git
cd IgrejaSaoSebastiao
```

### 2. Crie um Ambiente Virtual (Recomendado)

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Instale as Dependências

```bash
pip install -r requirements.txt
```

## ⚙️ Configuração

### 1. Configure as Variáveis de Ambiente

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

### 2. Edite o arquivo `.env`

Abra o arquivo `.env` e configure:

```env
# Chave secreta (IMPORTANTE: Mude isso!)
SECRET_KEY=sua_chave_secreta_muito_segura_aqui

# Credenciais do Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=sua_senha_segura

# Outras configurações
DATABASE_PATH=database.db
UPLOAD_FOLDER=static/uploads
MAX_FILE_SIZE=5242880
DEBUG=True
```

**⚠️ IMPORTANTE:**
- Nunca compartilhe seu arquivo `.env`
- Use senhas fortes em produção
- Gere uma chave secreta aleatória

### 3. Inicialize o Banco de Dados

O banco de dados será criado automaticamente na primeira execução.

## 🎮 Como Usar

### Iniciando o Servidor

```bash
python app.py
```

O servidor iniciará em: `http://localhost:5000`

### Acessando o Site

- **Site Público:** `http://localhost:5000`
- **Painel Admin:** `http://localhost:5000/admin`

### Credenciais Padrão

```
Usuário: admin
Senha: admin123
```

**⚠️ MUDE A SENHA IMEDIATAMENTE EM PRODUÇÃO!**

## 🎛️ Painel Administrativo

### Dashboard

Ao fazer login, você verá:
- Estatísticas do site (notícias, fotos, horários)
- Ações rápidas
- Notícias recentes
- Informações do sistema

### Gerenciamento de Notícias e Eventos

**Criar Nova Notícia:**
1. Acesse "Notícias e Eventos" no menu
2. Clique em "Nova Notícia"
3. Preencha:
   - Título
   - Tipo (Notícia ou Evento)
   - Subtítulo (opcional)
   - Conteúdo
   - Imagem (opcional)
4. Clique em "Salvar"

**Editar Notícia:**
1. Na lista de notícias, clique em "Editar"
2. Faça as alterações desejadas
3. Clique em "Salvar"

**Excluir Notícia:**
1. Na lista, clique em "Excluir"
2. Confirme a ação

### Gerenciamento de Horários de Missas

**Adicionar Horário:**
1. Acesse "Horários de Missas"
2. Clique em "Novo Horário"
3. Preencha:
   - Dia da semana
   - Horário
   - Tipo (Missa, Adoração, etc.)
4. Marque "Ativo"
5. Clique em "Salvar"

**Dica:** Você pode ter múltiplos horários no mesmo dia!

### Gerenciamento de Informações

**Editar Seções do Site:**
1. Acesse "Informações"
2. Clique em "Editar" na seção desejada
3. Altere o título e conteúdo
4. Clique em "Salvar"

**Seções Disponíveis:**
- Hero (Cabeçalho principal)
- Sobre a Paróquia
- Nossa História
- Nossa Missão
- E mais...

### Galeria de Fotos

**Adicionar Fotos:**
1. Acesse "Galeria de Fotos"
2. Clique em "Adicionar Foto"
3. Selecione a imagem (formatos: JPG, PNG, JPEG, GIF, WEBP)
4. Adicione título e descrição
5. Clique em "Salvar"

**Limites:**
- Tamanho máximo: 5MB por foto
- Formatos aceitos: JPG, PNG, JPEG, GIF, WEBP

### Configurações Gerais

**Editar Informações Básicas:**
1. Acesse "Configurações"
2. Edite:
   - Nome do site
   - Descrição
   - Endereço
   - Telefone
   - Email
   - Redes sociais
3. Clique em "Salvar Configurações"

## 🔒 Backup e Segurança

### Criar Backup Manual

1. No Dashboard, clique em "Fazer Backup"
2. O backup será salvo em `backups/`
3. Nome do arquivo: `database_backup_YYYYMMDD_HHMMSS.db`

### Restaurar Backup

1. Pare o servidor
2. Substitua `database.db` pelo arquivo de backup
3. Reinicie o servidor

### Segurança

**Recomendações:**
- ✅ Altere as credenciais padrão
- ✅ Use senhas fortes
- ✅ Faça backups regulares
- ✅ Mantenha o sistema atualizado
- ✅ Não compartilhe credenciais
- ✅ Use HTTPS em produção

## 🐛 Problemas Comuns

### Erro: "ModuleNotFoundError: No module named 'flask'"

**Solução:**
```bash
pip install -r requirements.txt
```

### Erro: "Address already in use"

**Solução:**
Outra aplicação está usando a porta 5000. Pare-a ou mude a porta em `app.py`:
```python
app.run(debug=Config.DEBUG, host='0.0.0.0', port=5001)
```

### Erro ao fazer upload de imagem

**Verificar:**
- Tamanho do arquivo (máximo 5MB)
- Formato do arquivo (JPG, PNG, JPEG, GIF, WEBP)
- Permissões da pasta `static/uploads/`

### Site não carrega estilos

**Solução:**
1. Limpe o cache do navegador (Ctrl + F5)
2. Verifique se os arquivos CSS estão em `static/`

## 📚 Estrutura de Arquivos

```
IgrejaSaoSebastiao/
├── app.py                  # Aplicação principal
├── config.py               # Configurações
├── requirements.txt        # Dependências Python
├── .env                    # Variáveis de ambiente (não commitar!)
├── .env.example            # Exemplo de configuração
├── database.db             # Banco de dados (criado automaticamente)
├── static/                 # Arquivos estáticos
│   ├── uploads/            # Uploads de usuários
│   ├── img/                # Imagens do site
│   ├── style.css           # Estilos
│   └── script.js           # Scripts
├── templates/              # Templates HTML
│   ├── index.html          # Página inicial
│   ├── admin_*.html        # Templates do admin
│   └── ...
└── backups/                # Backups do banco de dados
```

## 🔄 Atualizações

### Como Atualizar o Sistema

1. Faça backup do banco de dados
2. Faça backup do arquivo `.env`
3. Baixe a nova versão
4. Restaure o `.env`
5. Instale novas dependências: `pip install -r requirements.txt`
6. Reinicie o servidor

## 📝 Changelog

### Versão 2.0.0 Beta (2026-01-12)
- ✨ Novo painel administrativo moderno
- ✨ Sistema de gerenciamento completo
- ✨ Configurações via variáveis de ambiente
- ✨ Sistema de backup integrado
- ✨ Interface responsiva
- 🔒 Melhorias de segurança
- 🐛 Correções de bugs

### Versão 1.0.0
- 🎉 Lançamento inicial

## 🤝 Suporte

Em caso de problemas ou dúvidas:

1. Verifique a seção [Problemas Comuns](#problemas-comuns)
2. Consulte a documentação completa
3. Entre em contato com o suporte técnico

## 📄 Licença

Este projeto foi desenvolvido especialmente para a Igreja São Sebastião.

## 👨‍💻 Desenvolvido com ❤️

Sistema desenvolvido para servir a comunidade da Igreja São Sebastião em Ponte Nova/MG.

---

**Versão:** 2.0.0 Beta
**Status:** Fase de Testes
**Última Atualização:** 12 de Janeiro de 2026
