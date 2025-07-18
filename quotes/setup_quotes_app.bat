@echo off
echo Setting up the Quotes App for JUDICO
echo ===================================

echo.
echo Step 1: Installing required dependencies...
pip install -r "%~dp0requirements.txt"

echo.
echo Step 2: Creating sample Word document...
python "%~dp0create_sample_docx.py"

echo.
echo Step 3: Making migrations for the quotes app...
python "%~dp0..\manage.py" makemigrations quotes

echo.
echo Step 4: Applying migrations...
python "%~dp0..\manage.py" migrate quotes

echo.
echo Step 5: Importing quotes from sample document...
python "%~dp0..\manage.py" import_quotes "%~dp0sample_quotes.docx"

echo.
echo Setup complete! The quotes app is now ready to use.
echo You can view and manage quotes in the Django admin interface.
echo.

pause