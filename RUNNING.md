# Running the Markdown Server

## Requirements

- Python 3.11 or newer
- Windows PowerShell, Command Prompt, or a Unix-like shell

## Set up the environment on Windows

Open PowerShell in the project root and create the virtual environment:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
```

If PowerShell blocks activation, allow scripts for the current user and activate again:

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
\.venv\Scripts\Activate.ps1
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

Confirm that the required server package is installed:

```powershell
python -c "import uvicorn; print(uvicorn.__version__)"
```

## Start the server

With the virtual environment activated, from the project root:

```powershell
python .\run.py
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
