# Multi-Project Workspace: PharmaNexes, Tahzcare, VitaLense

This repository contains three small Python/Flask-based projects. This README provides a concise, professional analysis of each project, setup instructions, and a complete workflow for development and testing.

**Repository layout**
- `PharmaNexes/` — a small inventory/scan/dashboard web app (includes `medicines.csv`).
- `Tahzcare/` — a simple Flask app with templates and `requirements.txt`.
- `VitaLense/` — a Flask app with a doctor view and index template.

—

**Common prerequisites (global)**
- Python 3.8+ installed.
- (Recommended) Create an isolated virtual environment for each project:

  Windows (PowerShell):

  ```powershell
  python -m venv .venv
  .\.venv\Scripts\Activate.ps1
  pip install --upgrade pip
  ```

  Windows (cmd.exe):

  ```cmd
  python -m venv .venv
  .\.venv\Scripts\activate
  pip install --upgrade pip
  ```

—

**1) PharmaNexes**

Project purpose
- Light-weight pharmacy inventory + scanning demo with a dashboard and local CSV-backed medicines list.

Key files
- `PharmaNexes/app.py` — application entrypoint.
- `PharmaNexes/inventory_service.py` — backend logic for inventory operations.
- `PharmaNexes/index.html`, `PharmaNexes/login.html`, `PharmaNexes/dashboard.html`, `PharmaNexes/scan.html` — front-end pages.
- `PharmaNexes/medicines.csv` — sample data store for medicines.

Setup
- Create and activate a venv inside `PharmaNexes`.
- Install likely dependencies (Flask is expected):

  ```cmd
  pip install flask pandas
  ```

Run (typical)

```cmd
cd PharmaNexes
python app.py
``` 

If the app uses `flask run` instead, set `FLASK_APP=app.py` on Windows before running.

Workflow (end-to-end)
- Start the service (`python app.py`).
- Open `http://127.0.0.1:5000/` in a browser to reach the landing page (`index.html`).
- Authenticate with the login page (`login.html`) if required.
- Use `scan.html` to scan/add medicines — frontend POSTs to backend handlers in `app.py` or `inventory_service.py`.
- Inventory updates are written/read from `medicines.csv` and surfaced in `dashboard.html`.

Notes & suggestions
- `medicines.csv` is a single-file datastore: ensure file write permissions and consider migrating to SQLite for concurrency.
- Review `inventory_service.py` for input validation and CSV locking.

—

**2) Tahzcare**

Project purpose
- Small Flask app with a templated frontend. Likely a demo site or microservice.

Key files
- `Tahzcare/app.py` — application entrypoint.
- `Tahzcare/requirements.txt` — Python dependencies (install with pip).
- `Tahzcare/templates/index.html` — main template.

Setup

```cmd
cd Tahzcare
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

Workflow (end-to-end)
- Start the app with `python app.py`.
- Open `http://127.0.0.1:5000/` to view `index.html`.
- Modify templates in `templates/` for UI changes and reload the app.

Notes & suggestions
- Use `pip freeze > requirements.txt` after adding packages to keep the file current.

—

**3) VitaLense**

Project purpose
- Another small Flask site, includes a `doctor.html` template — likely shows doctor-related pages or forms.

Key files
- `VitaLense/app.py` — entrypoint.
- `VitaLense/templates/index.html` and `VitaLense/templates/doctor.html` — UI templates.

Setup

```cmd
cd VitaLense
python -m venv .venv
.\.venv\Scripts\activate
pip install flask
python app.py
```

Workflow (end-to-end)
- Start the app and navigate to the index page.
- Visit the doctor view (likely `/doctor` or similar route) to validate the `doctor.html` UI.

Notes & suggestions
- If these apps share common dependencies, consider centralizing shared requirements or using per-project `requirements.txt` files.

—

**Development & testing recommendations (workspace-wide)**
- Use a separate virtual environment per project to avoid dependency conflicts.
- Add `requirements.txt` to `PharmaNexes` and `VitaLense` if dependencies are confirmed; use `pip freeze` to capture them.
- Add a small `README` inside each project folder if unique configuration exists (ports, environment variables, secret keys).
- For `PharmaNexes`, move `medicines.csv` to a `data/` folder and add a `.gitignore` rule for persistent runtime data if necessary.

Troubleshooting tips
- If an app fails to start, inspect `app.py` for the framework used (Flask is common). Look for missing imports and install those packages.
- Check port collisions: multiple apps default to port 5000. Stop other servers or change ports in code when running multiple apps locally.

Next steps you might want me to do
- Run each app locally and verify routes.
- Extract and pin exact dependencies into `requirements.txt` for each project.
- Add per-project README files with screenshots or example data flows.

—

If you want, I can now: (a) run the apps to verify they start, (b) generate `requirements.txt` files, or (c) split this README into per-project READMEs. Tell me which next step you prefer.
