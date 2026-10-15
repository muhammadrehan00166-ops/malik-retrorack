RETRO RACK - Python Flask starter website
==========================================

WHAT IS INCLUDED
- Product listing, descriptions and prices
- Add to cart, quantity update and checkout
- Separate customer fields: name, mobile, WhatsApp, city, area, nearby landmark, complete address
- Success page after order
- Admin login, order list, add product with image, delete product
- SQLite database (created automatically)

RUN LOCALLY IN VS CODE (Windows)
1. Install Python 3.11+ from https://www.python.org/downloads/ and tick "Add Python to PATH".
2. Extract this ZIP into a folder, for example Desktop\retro_rack_python.
3. Open VS Code -> File -> Open Folder -> select retro_rack_python.
4. In VS Code choose Terminal -> New Terminal.
5. Create virtual environment:
   py -m venv .venv
6. Activate it in PowerShell:
   .\.venv\Scripts\Activate.ps1
   If PowerShell blocks activation, run this in Command Prompt terminal instead:
   .venv\Scripts\activate.bat
7. Install dependencies:
   python -m pip install -r requirements.txt
8. Start website:
   python app.py
9. Open http://127.0.0.1:5000 in your browser.
10. Admin dashboard: http://127.0.0.1:5000/admin/login
    Default local login: username admin / password ChangeMe123!

IMPORTANT SECURITY
- Before public hosting, set strong ADMIN_USERNAME, ADMIN_PASSWORD and SECRET_KEY environment variables.
- Never publish your admin password or SECRET_KEY in a public GitHub repository.
- This is a starter project. Add CSRF protection, rate limiting, backups and production server configuration before serious commercial use.
- Customer phone/address data is private. Protect the dashboard and database and collect only what you need.
- Do not use Flask's development server for production.

LIVE LINK / HOSTING
The local address 127.0.0.1 only works on your computer. To get a public link you must deploy the project to a hosting provider. Free plans and their terms can change, and no free host can guarantee a link will last forever. A PythonAnywhere account can be one option for a Python/Flask app; follow its current Flask deployment instructions. The uploaded images and SQLite database need persistent storage and backups on whichever host you choose.
