import os, sqlite3
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "change-this-secret-before-deployment")
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DB_PATH = os.path.join(BASE_DIR, "retro_rack.db")
UPLOAD_DIR = os.path.join(BASE_DIR, "static", "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "webp", "gif"}
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "ChangeMe123!")

def db():
    con = sqlite3.connect(DB_PATH)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with db() as con:
        con.execute("""CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL,
            price REAL NOT NULL, description TEXT NOT NULL, image TEXT NOT NULL DEFAULT '')""")
        con.execute("""CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT NOT NULL,
            mobile TEXT NOT NULL, whatsapp TEXT NOT NULL, city TEXT NOT NULL,
            area TEXT NOT NULL, nearby TEXT NOT NULL, address TEXT NOT NULL,
            items TEXT NOT NULL, total REAL NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP)""")
        count = con.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        if count == 0:
            con.executemany("INSERT INTO products (name, price, description, image) VALUES (?,?,?,?)", [
                ("Household Floor Wiper", 850, "A useful cleaning helper for everyday home use.", ""),
                ("Decorative LED Lamp", 1200, "A lovely lamp for a cozy home.", ""),
                ("Storage Basket", 650, "A practical basket for organizing household items.", ""),
                ("Mini Desk Fan", 1500, "Compact fan for your desk or bedside.", "")
            ])

def admin_required(fn):
    @wraps(fn)
    def wrapped(*args, **kwargs):
        if not session.get("admin_logged_in"):
            return redirect(url_for("admin_login"))
        return fn(*args, **kwargs)
    return wrapped

def get_cart():
    return session.get("cart", {})

def cart_details():
    cart = get_cart()
    products, total, count = [], 0, 0
    with db() as con:
        for pid, qty in cart.items():
            p = con.execute("SELECT * FROM products WHERE id=?", (pid,)).fetchone()
            if p and int(qty) > 0:
                subtotal = p["price"] * int(qty)
                products.append({"product": p, "qty": int(qty), "subtotal": subtotal})
                total += subtotal
                count += int(qty)
    return products, total, count

@app.context_processor
def inject_cart_count():
    try:
        return {"cart_count": cart_details()[2]}
    except Exception:
        return {"cart_count": 0}

@app.route("/")
def home():
    with db() as con:
        products = con.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    return render_template("home.html", products=products)

@app.route("/cart/add/<int:product_id>", methods=["POST"])
def add_to_cart(product_id):
    with db() as con:
        exists = con.execute("SELECT id FROM products WHERE id=?", (product_id,)).fetchone()
    if exists:
        cart = get_cart()
        cart[str(product_id)] = int(cart.get(str(product_id), 0)) + 1
        session["cart"] = cart
        flash("Product added to your cart.")
    return redirect(request.referrer or url_for("home"))

@app.route("/cart")
def cart():
    items, total, _ = cart_details()
    return render_template("cart.html", items=items, total=total)

@app.route("/cart/update", methods=["POST"])
def update_cart():
    cart = get_cart()
    for pid in list(cart.keys()):
        try:
            qty = int(request.form.get("qty_"+pid, "0"))
            if qty <= 0: cart.pop(pid, None)
            else: cart[pid] = min(qty, 99)
        except ValueError:
            cart.pop(pid, None)
    session["cart"] = cart
    return redirect(url_for("cart"))

@app.route("/checkout", methods=["GET", "POST"])
def checkout():
    items, total, _ = cart_details()
    if not items:
        flash("Your cart is empty. Please add a product first.")
        return redirect(url_for("home"))
    if request.method == "POST":
        fields = ["customer_name","mobile","whatsapp","city","area","nearby","address"]
        data = {f: request.form.get(f, "").strip() for f in fields}
        if any(not value for value in data.values()):
            flash("Please fill in every field.")
            return render_template("checkout.html", items=items, total=total, data=data)
        summary = "; ".join(f'{x["product"]["name"]} x{x["qty"]}' for x in items)
        with db() as con:
            con.execute("""INSERT INTO orders
                (customer_name,mobile,whatsapp,city,area,nearby,address,items,total)
                VALUES (?,?,?,?,?,?,?,?,?)""",
                (data["customer_name"],data["mobile"],data["whatsapp"],data["city"],
                 data["area"],data["nearby"],data["address"],summary,total))
        session["cart"] = {}
        return render_template("success.html")
    return render_template("checkout.html", items=items, total=total, data={})

@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        flash("Incorrect username or password.")
    return render_template("admin_login.html")

@app.route("/admin/logout")
def admin_logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/admin")
@admin_required
def admin_dashboard():
    with db() as con:
        orders = con.execute("SELECT * FROM orders ORDER BY id DESC").fetchall()
        products = con.execute("SELECT * FROM products ORDER BY id DESC").fetchall()
    return render_template("admin.html", orders=orders, products=products)

@app.route("/admin/products/add", methods=["POST"])
@admin_required
def add_product():
    name = request.form.get("name", "").strip()
    description = request.form.get("description", "").strip()
    try: price = float(request.form.get("price", "0"))
    except ValueError: price = 0
    image_file = request.files.get("image")
    image_name = ""
    if not name or not description or price <= 0:
        flash("Enter a product name, a description and a price above zero.")
        return redirect(url_for("admin_dashboard"))
    if image_file and image_file.filename:
        filename = secure_filename(image_file.filename)
        ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
        if ext not in ALLOWED_EXTENSIONS:
            flash("Image must be PNG, JPG, JPEG, WEBP or GIF.")
            return redirect(url_for("admin_dashboard"))
        image_name = f"{os.urandom(8).hex()}_{filename}"
        image_file.save(os.path.join(UPLOAD_DIR, image_name))
    with db() as con:
        con.execute("INSERT INTO products (name,price,description,image) VALUES (?,?,?,?)",
                    (name, price, description, image_name))
    flash("Product added successfully.")
    return redirect(url_for("admin_dashboard"))

@app.route("/admin/products/delete/<int:product_id>", methods=["POST"])
@admin_required
def delete_product(product_id):
    with db() as con:
        p = con.execute("SELECT image FROM products WHERE id=?", (product_id,)).fetchone()
        con.execute("DELETE FROM products WHERE id=?", (product_id,))
    if p and p["image"]:
        try: os.remove(os.path.join(UPLOAD_DIR, p["image"]))
        except OSError: pass
    cart = get_cart()
    cart.pop(str(product_id), None)
    session["cart"] = cart
    flash("Product deleted.")
    return redirect(url_for("admin_dashboard"))

init_db()
if __name__ == "__main__":
    app.run(debug=True)
