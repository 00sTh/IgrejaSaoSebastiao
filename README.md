# Igreja Sao Sebastiao - Sistema de Gerenciamento

Sistema completo de gerenciamento de site para a Igreja Sao Sebastiao, com painel administrativo moderno e totalmente editavel.

## Indice

- [Sobre o Projeto](#sobre-o-projeto)
- [Funcionalidades](#funcionalidades)
- [Requisitos](#requisitos)
- [Instalacao](#instalacao)
- [Configuracao](#configuracao)
- [Como Usar](#como-usar)
- [Painel Administrativo](#painel-administrativo)
- [Sistema de Mensagens](#sistema-de-mensagens)
- [Agendamento de Confissoes](#agendamento-de-confissoes)
- [Gerenciamento de Usuarios](#gerenciamento-de-usuarios)
- [Configuracao de Email SMTP](#configuracao-de-email-smtp)
- [Validacoes do Sistema](#validacoes-do-sistema)
- [Backup e Seguranca](#backup-e-seguranca)
- [Problemas Comuns](#problemas-comuns)
- [Changelog](#changelog)

## Sobre o Projeto

Este e um sistema web completo desenvolvido especialmente para a Igreja Sao Sebastiao em Ponte Nova/MG. O sistema permite gerenciar todo o conteudo do site atraves de um painel administrativo intuitivo e moderno.

### Versao Atual: 2.1.0 (Producao)

## Funcionalidades

### Site Publico
- Pagina inicial moderna e responsiva
- Secao de noticias e eventos
- Horarios de missas atualizaveis
- Galeria de fotos com categorias
- Historia e informacoes da paroquia
- Informacoes de contato e localizacao
- **Agendamento online de confissoes**
- **Formulario de contato com validacao**
- Design totalmente responsivo

### Painel Administrativo
- Dashboard com estatisticas
- Gerenciamento completo de noticias e eventos
- Gerenciamento de horarios de missas
- Edicao de informacoes da paroquia
- Gerenciamento de galeria de fotos
- **Sistema de resposta a mensagens**
- **Gerenciamento de usuarios (CRUD completo)**
- **Gerenciamento de agendamentos de confissao**
- Configuracoes gerais editaveis
- Sistema de backup automatico
- Interface moderna e intuitiva

### Seguranca
- Autenticacao com sessoes seguras
- Protecao CSRF em todos os formularios
- Rate limiting contra brute force
- Senhas com hash PBKDF2-SHA256
- Sistema de permissoes por roles (RBAC)
- Validacao de email com verificacao DNS
- Validacao de telefone brasileiro

## Requisitos

- Python 3.8 ou superior
- Navegador web moderno (Chrome, Firefox, Safari, Edge)
- Sistema operacional: Windows, Linux ou macOS

## Instalacao

### 1. Clone o Repositorio

```bash
git clone https://github.com/00sTh/IgrejaSaoSebastiao.git
cd IgrejaSaoSebastiao
```

### 2. Crie um Ambiente Virtual

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

### 3. Instale as Dependencias

```bash
pip install -r requirements.txt
```

## Configuracao

### 1. Configure as Variaveis de Ambiente

Copie o arquivo `.env.example` para `.env`:

```bash
cp .env.example .env
```

### 2. Edite o arquivo `.env`

```env
# Chave secreta (IMPORTANTE: Gere uma chave unica!)
# Use: python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY=sua_chave_secreta_muito_segura_aqui

# Credenciais do Admin
ADMIN_USERNAME=admin
ADMIN_PASSWORD=sua_senha_segura

# Banco de Dados
DATABASE_PATH=database.db

# Uploads
UPLOAD_FOLDER=static/uploads
MAX_FILE_SIZE=5242880

# Ambiente (PRODUCAO: DEBUG=False)
FLASK_ENV=production
DEBUG=False
```

**IMPORTANTE:**
- Nunca compartilhe seu arquivo `.env`
- Use senhas fortes em producao
- Mantenha `DEBUG=False` em producao

### 3. Configuracao de Email (Opcional)

Para enviar respostas por email, adicione no `.env`:

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASS=sua_senha_de_app
SMTP_FROM=contato@igrejasaosebastiao.com.br
```

**Para Gmail:** Use uma "Senha de App" (Configuracoes > Seguranca > Senhas de app)

## Como Usar

### Iniciando o Servidor

```bash
python app.py
```

O servidor iniciara em: `http://localhost:5000`

### Acessando o Sistema

| Pagina | URL |
|--------|-----|
| Site Publico | `http://localhost:5000` |
| Painel Admin | `http://localhost:5000/admin` |

### Credenciais Padrao

```
Usuario: admin
Senha: (definida no .env)
```

## Painel Administrativo

### Dashboard

Ao fazer login, voce vera:
- Estatisticas do site (noticias, fotos, horarios)
- Mensagens nao lidas
- Agendamentos pendentes
- Acoes rapidas
- Informacoes do sistema

### Menu Lateral

O menu esta organizado em categorias:

**Conteudo:**
- Noticias - Gerenciar noticias e eventos
- Galeria de Fotos - Upload e organizacao de imagens

**Configuracoes:**
- Conteudo do Site - Editar textos das secoes
- Imagens do Site - Trocar imagens de fundo
- Horarios de Missas - Gerenciar horarios
- Contatos - Informacoes de contato
- Configuracoes - Configuracoes gerais

**Sistema:**
- Usuarios - Gerenciar usuarios do painel

**Confissoes:**
- Horarios Disponiveis - Definir horarios de confissao
- Agendamentos - Ver e gerenciar agendamentos

**Comunicacao:**
- Mensagens - Responder mensagens de contato

## Sistema de Mensagens

### Recebendo Mensagens

Quando alguem envia uma mensagem pelo formulario de contato do site:
1. A mensagem aparece em **Mensagens** no painel
2. Mensagens novas ficam destacadas com badge "Nova"
3. O dashboard mostra contador de mensagens nao lidas

### Respondendo Mensagens

1. Acesse **Mensagens** no menu lateral
2. Clique em **Responder** na mensagem desejada
3. Digite sua resposta no formulario
4. Clique em **Enviar Resposta**

**Com SMTP configurado:** A resposta e enviada automaticamente por email

**Sem SMTP:** A resposta e salva no sistema e voce pode:
- Usar o botao "Abrir no Email" para enviar pelo seu cliente de email
- Copiar a resposta manualmente

### Indicadores de Status

| Badge | Significado |
|-------|-------------|
| Nova | Mensagem nao lida |
| Respondida | Mensagem ja foi respondida |

## Agendamento de Confissoes

### Configurando Horarios Disponiveis

1. Acesse **Horarios Disponiveis** no menu
2. Clique em **Adicionar Horario**
3. Preencha:
   - Dia da semana
   - Horario de inicio
   - Horario de fim
   - Vagas por horario
4. Ative o horario
5. Clique em **Salvar**

### Gerenciando Agendamentos

1. Acesse **Agendamentos** no menu
2. Veja todos os agendamentos com:
   - Nome do fiel
   - Data e horario
   - Status (pendente/confirmado/cancelado)
3. Acoes disponiveis:
   - Confirmar agendamento
   - Cancelar agendamento
   - Editar informacoes

### Como Funciona para o Fiel

1. No site, acessa a secao "Confissao"
2. Seleciona mes e dia
3. Sistema mostra horarios disponiveis
4. Preenche nome, email e telefone
5. Confirma agendamento
6. Recebe confirmacao na tela

## Gerenciamento de Usuarios

### Niveis de Acesso (Roles)

| Role | Permissoes |
|------|-----------|
| super_admin | Acesso total, incluindo gestao de usuarios |
| admin | Tudo exceto gestao de usuarios |
| editor | Criar e editar conteudo, sem deletar |
| viewer | Apenas visualizar |

### Criando Novo Usuario

1. Acesse **Usuarios** no menu (categoria Sistema)
2. Clique em **Novo Usuario**
3. Preencha:
   - Nome de usuario (unico)
   - Email
   - Senha (minimo 8 caracteres)
   - Nivel de acesso (role)
4. Clique em **Criar**

### Editando Usuario

1. Na lista de usuarios, clique em **Editar**
2. Altere os campos desejados
3. Deixe a senha em branco para manter a atual
4. Clique em **Salvar**

## Configuracao de Email SMTP

Para enviar emails automaticamente (respostas, notificacoes):

### Gmail

```env
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=seu_email@gmail.com
SMTP_PASS=xxxx xxxx xxxx xxxx
SMTP_FROM=contato@suaigreja.com.br
```

**Obter Senha de App do Gmail:**
1. Acesse myaccount.google.com
2. Seguranca > Verificacao em duas etapas (ativar)
3. Seguranca > Senhas de app
4. Gere uma senha para "Email"
5. Use essa senha no SMTP_PASS

### Outlook/Hotmail

```env
SMTP_HOST=smtp-mail.outlook.com
SMTP_PORT=587
SMTP_USER=seu_email@outlook.com
SMTP_PASS=sua_senha
SMTP_FROM=seu_email@outlook.com
```

### Outros Provedores

Consulte a documentacao do seu provedor de email para obter:
- Servidor SMTP (SMTP_HOST)
- Porta (geralmente 587 para TLS)
- Credenciais de acesso

## Validacoes do Sistema

### Validacao de Email

O sistema valida emails de forma rigorosa:

| Verificacao | Descricao |
|-------------|-----------|
| Formato | Verifica se o formato e valido |
| Dominio | Verifica se o dominio existe (DNS) |
| Temporarios | Bloqueia emails descartaveis |

**Dominios bloqueados:** tempmail.com, mailinator.com, guerrillamail.com, 10minutemail.com, yopmail.com, e outros.

### Validacao de Telefone

O sistema valida telefones brasileiros:

| Verificacao | Descricao |
|-------------|-----------|
| DDD | Verifica se o DDD e valido (11-99) |
| Celular | 11 digitos, comeca com 9 apos DDD |
| Fixo | 10 digitos, NAO comeca com 9 apos DDD |

**Exemplos validos:**
- Celular: (31) 99999-8888 ou 31999998888
- Fixo: (31) 3295-1379 ou 3132951379

**Exemplos invalidos:**
- DDD 00 ou 01 (nao existem)
- Celular sem o 9: 31899998888
- Menos de 10 digitos

## Backup e Seguranca

### Criar Backup Manual

1. No Dashboard, clique em **Fazer Backup**
2. O backup sera salvo em `backups/`
3. Nome do arquivo: `database_backup_YYYYMMDD_HHMMSS.db`

### Restaurar Backup

1. Pare o servidor
2. Substitua `database.db` pelo arquivo de backup
3. Reinicie o servidor

### Boas Praticas de Seguranca

- Altere as credenciais padrao imediatamente
- Use senhas fortes (minimo 12 caracteres)
- Faca backups regulares (diarios recomendado)
- Mantenha DEBUG=False em producao
- Use HTTPS em producao
- Nao compartilhe o arquivo .env
- Revise os logs periodicamente

## Problemas Comuns

### Erro: "ModuleNotFoundError"

```bash
pip install -r requirements.txt
```

### Erro: "Address already in use"

Outra aplicacao esta usando a porta 5000. Mude a porta:
```python
app.run(debug=Config.DEBUG, host='0.0.0.0', port=5001)
```

### Erro ao fazer upload de imagem

Verificar:
- Tamanho do arquivo (maximo 5MB)
- Formato do arquivo (JPG, PNG, JPEG, GIF, WEBP)
- Permissoes da pasta `static/uploads/`

### Email nao enviado

Verificar:
- Variaveis SMTP configuradas no .env
- Senha de app correta (Gmail)
- Porta correta (587 para TLS)

### Telefone/Email rejeitado

O sistema valida rigorosamente:
- Email deve ter dominio real (verificado via DNS)
- Telefone deve ter DDD brasileiro valido
- Celular deve ter 11 digitos com 9 na frente

## Estrutura de Arquivos

```
IgrejaSaoSebastiao/
├── app.py                  # Aplicacao principal
├── config.py               # Configuracoes
├── requirements.txt        # Dependencias Python
├── .env                    # Variaveis de ambiente (NAO COMMITAR!)
├── .env.example            # Exemplo de configuracao
├── database.db             # Banco de dados SQLite
├── core/                   # Modulos do sistema
│   ├── crud.py             # Engine CRUD dinamico
│   ├── schema.py           # Schemas das entidades
│   ├── routes.py           # Rotas do CRUD
│   ├── cache.py            # Sistema de cache
│   └── media.py            # Processamento de imagens
├── middleware/             # Middlewares
│   ├── auth.py             # Autenticacao e RBAC
│   └── logger.py           # Sistema de logs
├── static/                 # Arquivos estaticos
│   ├── uploads/            # Uploads de usuarios
│   ├── img/                # Imagens do site
│   ├── style.css           # Estilos
│   └── script.js           # Scripts
├── templates/              # Templates HTML
│   ├── index.html          # Pagina inicial
│   ├── admin_*.html        # Templates do admin
│   └── crud/               # Templates do CRUD
├── tests/                  # Testes automatizados
└── backups/                # Backups do banco
```

## Changelog

### Versao 2.1.0 (25 de Janeiro de 2026)
- **Sistema de resposta a mensagens** - Responda mensagens diretamente pelo painel
- **Validacao avancada de email** - Verifica se o dominio existe via DNS
- **Validacao de telefone brasileiro** - Valida DDD e formato correto
- **Bloqueio de emails temporarios** - Impede cadastros com emails descartaveis
- **Envio de email via SMTP** - Configure para enviar respostas automaticamente
- **CRUD de usuarios completo** - Crie e gerencie usuarios do sistema
- **Correcoes de bugs** - Diversos ajustes e melhorias

### Versao 2.0.0 (12 de Janeiro de 2026)
- Novo painel administrativo moderno
- Sistema de gerenciamento completo
- CRUD dinamico baseado em schemas
- Sistema de agendamento de confissoes
- Galeria de fotos com categorias
- Editor de conteudo do site
- Sistema de autenticacao com RBAC
- Cache inteligente
- Processamento de imagens
- Sistema de backup integrado
- Interface responsiva
- Melhorias de seguranca

### Versao 1.0.0
- Lancamento inicial

## Suporte

Em caso de problemas ou duvidas:

1. Verifique a secao [Problemas Comuns](#problemas-comuns)
2. Consulte a documentacao completa
3. Abra uma issue no GitHub

## Licenca

Este projeto foi desenvolvido especialmente para a Igreja Sao Sebastiao.

---

**Versao:** 2.1.0
**Status:** Producao
**Ultima Atualizacao:** 25 de Janeiro de 2026
