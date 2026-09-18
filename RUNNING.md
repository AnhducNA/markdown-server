# Running the Markdown Server

## Requirements

- Python 3.11 or newer
- Windows PowerShell, Command Prompt, or a Unix-like shell

## Set up the environment

From the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

For Command Prompt, activate the environment with:

```bat
.venv\Scripts\activate.bat
```

For macOS or Linux, use:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e .
```

## Start the server

With the virtual environment activated:

```powershell
python run.py
```

The server runs with the host and port configured by the application settings. The default local URLs are:

- API root: http://127.0.0.1:8000/
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc
- Health check: http://127.0.0.1:8000/api/v1/health

The server reloads automatically when source files change. Stop it with `Ctrl+C`.

## Start with Uvicorn directly

To choose the host or port explicitly:

```powershell
python -m uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

## Run the tests

```powershell
python -m pytest
```

## Deactivate the environment

```powershell
deactivate
```
