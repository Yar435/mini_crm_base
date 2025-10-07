# Create venv with Python 3.11 and install dev requirements
param(
    [string]$Python = "python",
    [string]$VenvName = "venv"
)

# Write-Host "Creating virtual environment..." -ForegroundColor Cyan
# & $Python -m venv $VenvName

$venvActivate = ".\{0}\Scripts\Activate.ps1" -f $VenvName
Write-Host "Activating venv: $venvActivate" -ForegroundColor Cyan
& $venvActivate

python -m pip install --upgrade pip
pip install -r requirements-dev.txt

Write-Host "Installing pre-commit hooks..." -ForegroundColor Cyan
pre-commit install

Write-Host "Done. To activate later: `n .\$VenvName\Scripts\Activate.ps1" -ForegroundColor Green
