# Setup script for the Quotes App in JUDICO

Write-Host "Setting up the Quotes App for JUDICO" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan
Write-Host ""

# Get the script directory
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

Write-Host "Step 1: Installing required dependencies..." -ForegroundColor Green
pip install -r "$ScriptDir\requirements.txt"

Write-Host ""
Write-Host "Step 2: Creating sample Word document..." -ForegroundColor Green
python "$ScriptDir\create_sample_docx.py"

Write-Host ""
Write-Host "Step 3: Making migrations for the quotes app..." -ForegroundColor Green
python "$ScriptDir\..\manage.py" makemigrations quotes

Write-Host ""
Write-Host "Step 4: Applying migrations..." -ForegroundColor Green
python "$ScriptDir\..\manage.py" migrate quotes

Write-Host ""
Write-Host "Step 5: Importing quotes from sample document..." -ForegroundColor Green
python "$ScriptDir\..\manage.py" import_quotes "$ScriptDir\sample_quotes.docx"

Write-Host ""
Write-Host "Setup complete! The quotes app is now ready to use." -ForegroundColor Cyan
Write-Host "You can view and manage quotes in the Django admin interface." -ForegroundColor Cyan
Write-Host ""

Read-Host -Prompt "Press Enter to exit"