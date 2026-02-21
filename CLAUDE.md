# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Site e painel administrativo da Igreja Sao Sebastiao (Ponte Nova/MG). Flask + SQLite + Jinja2, single-page public site with full admin panel. Portuguese (pt-BR) codebase.

## Commands

```bash
# Activate venv (required - system python does not have flask)
source venv/bin/activate

# Run server (listens on 0.0.0.0:5000)
python app.py

# Or without activating venv:
./venv/bin/python app.py

# Run tests
pytest tests/

# Access
# Site: http://localhost:5000
# Admin: http://localhost:5000/admin
```

## Architecture

### Data Flow
`app.py` is the monolithic Flask application. It reads all data from `database.db` (SQLite) and passes it to `templates/index.html` as template variables. The admin panel has ~20 routes for CRUD operations on each entity.

### Key Pattern: `paroquia_info` table
Most site content is stored in the `paroquia_info` table with columns `secao` (section key), `titulo`, and `conteudo`. The `index()` route loads all rows into a dict keyed by `secao`:
```python
info_paroquia[info['secao']] = {'titulo': info['titulo'], 'conteudo': info['conteudo']}
```
In templates, content is accessed via `info_paroquia.get('section_key', {}).get('titulo')` for short values or `.get('conteudo')` for long-form text (like `historia_texto`, `historia_marcos`). **Be careful**: the admin "Conteudo do Site" editor (`admin_conteudo_site_save`) only saves to the `titulo` column, while the "Informacoes" editor saves both `titulo` and `conteudo`. Know which column your template reads from.

### Database Migrations
Done inline in `init_db()` via try/except `ALTER TABLE` blocks. There is no migration framework. When adding a column, add both the `ALTER TABLE` migration in `init_db()` and include the column in the `CREATE TABLE IF NOT EXISTS` statement for fresh installs.

### Module Structure
- **`app.py`** - All routes (public + admin), DB init, file upload, email, form validation
- **`config.py`** - Config from `.env` (via python-dotenv): SECRET_KEY, DATABASE_PATH, ADMIN credentials
- **`middleware/auth.py`** - AuthManager (sessions, CSRF, RBAC), RateLimiter, login_required/role_required/permission_required decorators. Users table with roles: super_admin, admin, editor, viewer
- **`middleware/logger.py`** - JSON structured logging to `logs/app.log` with request tracking
- **`core/`** - CRUD engine (schema-driven), media pipeline (Pillow resize/webp), cache. Routes registered via `init_crud_routes(app)`
- **`templates/index.html`** - Single-page public site (all sections: hero, about, hours, events, gallery, history, location, contact, footer)
- **`templates/admin_*.html`** - Admin panel templates, extend `admin_base.html`

### Authentication
Session-based with CSRF protection. All admin routes use `@login_required`. CSRF token is auto-injected into templates and validated on POST/PUT/DELETE. Public API routes (`/api/agendar-confissao`, `/api/enviar-mensagem`) are exempt from CSRF.

### File Uploads
Saved to `static/uploads/`. Uses `core/media.py` pipeline (resize to medium/large/thumb, convert to webp) with fallback to direct save. Max 5MB, allowed: png/jpg/jpeg/gif/webp.

## Important Gotchas

- **venv required**: Flask is only installed in `venv/`, not system-wide. Always use `./venv/bin/python` or activate the venv first.
- **Pipe-separated values**: Some `paroquia_info` fields use `|` as delimiter (e.g., `confissoes_horarios`, `historia_marcos`). Templates split on `|` to render lists.
- **`database.db` is tracked in git** but contains runtime data. Be careful with commits.
- **No test database**: Tests use the same SQLite file unless configured otherwise.
