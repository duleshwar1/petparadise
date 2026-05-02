import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import pymysql
import pymysql.cursors
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from datetime import datetime
from dotenv import load_dotenv
import urllib.parse

# Load environment variables
load_dotenv()

app = Flask(__name__)
# Use environment variable for secret key, with fallback for development
app.secret_key = os.environ.get('SECRET_KEY', 'default_dev_secret_key')
app.config['UPLOAD_FOLDER'] = os.environ.get('UPLOAD_FOLDER', 'static/images')
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

# Logging Configuration
if os.environ.get('FLASK_ENV') == 'production':
    if not os.path.exists('logs'):
        os.makedirs('logs')
    # Rotating log files: keeps last 10 logs of max 10MB each
    file_handler = RotatingFileHandler('logs/petzone.log', maxBytes=10485760, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('PetZone startup')

# Database Configuration using DATABASE_URL
def get_db_connection():
    database_url = os.environ.get('DATABASE_URL')
    if not database_url:
        app.logger.error("DATABASE_URL environment variable is not set")
        return None
        
    try:
        url = urllib.parse.urlparse(database_url)
        conn = pymysql.connect(
            host=url.hostname,
            user=url.username,
            password=url.password,
            database=url.path[1:],
            port=url.port or 3306,
            cursorclass=pymysql.cursors.DictCursor,
            connect_timeout=10
        )
        return conn
    except Exception as e:
        app.logger.error(f"Error connecting to MySQL with PyMySQL: {e}")
    return None

# --- Filters ---
@app.template_filter('currency')
def currency_filter(value):
    try:
        if value is None:
            return "₹0"
        # Convert Decimal or string to float for formatting safety
        float_val = float(value)
        # Standard Indian formatting is slightly different, but for simplicity:
        return f"₹{float_val:,.2f}"
    except (ValueError, TypeError):
        return f"₹{value}"

# --- Middleware ---
def is_logged_in():
    return 'user_id' in session

def is_admin():
    return session.get('role') == 'admin'

@app.before_request
def check_cart():
    if 'cart' not in session:
        session['cart'] = []

# --- User Routes ---

@app.route('/')
def index():
    conn = get_db_connection()
    
    if not conn:
        flash("Database connection failed. Please try again later.", "danger")
        return render_template('index.html', featured_pets=[], featured_products=[])

    try:
        cursor = conn.cursor(dictionary=True)

        # Fetch featured pets
        cursor.execute("SELECT * FROM pets ORDER BY id DESC LIMIT 4")
        featured_pets = cursor.fetchall()

        # Fetch featured products
        cursor.execute("SELECT * FROM products ORDER BY id DESC LIMIT 4")
        featured_products = cursor.fetchall()

        return render_template(
            'index.html',
            featured_pets=featured_pets,
            featured_products=featured_products
        )

    except Exception as e:
        app.logger.error(f"Database error in index: {e}")
        flash("Something went wrong!", "danger")
        return render_template('index.html', featured_pets=[], featured_products=[])

    finally:
        if conn:
            conn.close()

@app.route('/pets')
@app.route('/pets/<category>')
def pets(category=None):
    conn = get_db_connection()
    if not conn:
        flash("Our adoption center is temporarily unavailable.", "danger")
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM pets WHERE category = %s ORDER BY created_at DESC", (category,))
        else:
            cursor.execute("SELECT * FROM pets ORDER BY created_at DESC")
        pets_list = cursor.fetchall()
        return render_template('pets.html', pets=pets_list, current_category=category)
    except Exception as e:
        app.logger.error(f"Database error in pets: {e}")
        flash("Internal Error occurred.", "danger")
        return redirect(url_for('index'))
    finally:
        if conn:
            conn.close()

@app.route('/products')
@app.route('/products/<category>')
def products(category=None):
    conn = get_db_connection()
    if not conn:
        flash("Our shop is currently taking a break.", "danger")
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        if category:
            cursor.execute("SELECT * FROM products WHERE category = %s ORDER BY created_at DESC", (category,))
        else:
            cursor.execute("SELECT * FROM products ORDER BY created_at DESC")
        products_list = cursor.fetchall()
        return render_template('products.html', products=products_list, current_category=category)
    except Exception as e:
        app.logger.error(f"Database error in products: {e}")
        flash("Internal Error occurred.", "danger")
        return redirect(url_for('index'))
    finally:
        if conn and conn.is_connected():
            conn.close()

@app.route('/product/<int:id>')
def product_details(id):
    conn = get_db_connection()
    if not conn:
        flash("Item details currently unavailable.", "danger")
        return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        # Check if id belongs to pets or products
        cursor.execute("SELECT * FROM pets WHERE id = %s", (id,))
        item = cursor.fetchone()
        item_type = 'pet'
        if not item:
            cursor.execute("SELECT * FROM products WHERE id = %s", (id,))
            item = cursor.fetchone()
            item_type = 'product'
            
        if not item:
            flash("Item not found", "warning")
            return redirect(url_for('index'))
        
        return render_template('details.html', item=item, item_type=item_type)
    except Exception as e:
        app.logger.error(f"Error in product_details: {e}")
        flash("Could not fetch item details.", "danger")
        return redirect(url_for('index'))
    finally:
        if conn:
            conn.close()

@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total = sum(item['price'] * item['quantity'] for item in cart_items)
    return render_template('cart.html', cart_items=cart_items, total=total)

@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    item_id = int(request.form.get('id'))
    item_name = request.form.get('name')
    price = float(request.form.get('price'))
    image = request.form.get('image')
    item_type = request.form.get('type')
    
    cart = session.get('cart', [])
    
    # Check if item already in cart
    found = False
    for item in cart:
        if item['id'] == item_id and item['type'] == item_type:
            item['quantity'] += 1
            found = True
            break
            
    if not found:
        cart.append({
            'id': item_id,
            'name': item_name,
            'price': price,
            'image': image,
            'type': item_type,
            'quantity': 1
        })
    
    session['cart'] = cart
    flash(f"{item_name} added to cart!", "success")
    return redirect(request.referrer or url_for('index'))

@app.route('/update_cart', methods=['POST'])
def update_cart():
    item_id = int(request.form.get('id'))
    item_type = request.form.get('type')
    action = request.form.get('action')
    
    cart = session.get('cart', [])
    for i, item in enumerate(cart):
        if item['id'] == item_id and item['type'] == item_type:
            if action == 'increase':
                item['quantity'] += 1
            elif action == 'decrease':
                item['quantity'] -= 1
                if item['quantity'] <= 0:
                    cart.pop(i)
            elif action == 'remove':
                cart.pop(i)
            break
            
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if not is_logged_in():
        flash("Please login to checkout", "warning")
        return redirect(url_for('login', next='checkout'))
        
    if not session.get('cart'):
        flash("Your cart is empty", "warning")
        return redirect(url_for('index'))
        
    if request.method == 'POST':
        phone = request.form.get('phone')
        house_no = request.form.get('house_no')
        address = request.form.get('address')
        city = request.form.get('city')
        state = request.form.get('state')
        pincode = request.form.get('pincode')
        
        cart_items = session.get('cart', [])
        total_price = sum(item['price'] * item['quantity'] for item in cart_items)
        
        conn = get_db_connection()
        if not conn:
            flash("Database connection lost. Please try again.", "danger")
            return redirect(url_for('checkout'))
            
        try:
            cursor = conn.cursor()
            # Create Order (matching the SQL schema)
            cursor.execute("""
                INSERT INTO orders (user_id, total_price, house_no, address, city, state, pincode, phone, product_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (session['user_id'], total_price, house_no, address, city, state, pincode, phone, cart_items[0]['id']))
            order_id = cursor.lastrowid
            
            # Create Order Items (new table!)
            for item in cart_items:
                cursor.execute("""
                    INSERT INTO order_items (order_id, item_type, item_id, quantity, price)
                    VALUES (%s, %s, %s, %s, %s)
                """, (order_id, item['type'], item['id'], item['quantity'], item['price']))
            
            conn.commit()
            session['cart'] = [] # Clear cart
            flash("Order placed successfully!", "success")
            return render_template('order_success.html', order_id=order_id)
        except Exception as e:
            if conn: conn.rollback()
            app.logger.error(f"Checkout error: {e}")
            flash(f"Error placing order: {e}", "danger")
        finally:
            if conn: conn.close()
            
    total = sum(item['price'] * item['quantity'] for item in session.get('cart', []))
    return render_template('checkout.html', total=total)

# --- Auth Routes ---

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        phone = request.form.get('phone')
        password = request.form.get('password')
        hashed_pw = generate_password_hash(password)
        
        conn = get_db_connection()
        if not conn:
            flash("Service unavailable.", "danger")
            return redirect(url_for('signup'))
            
        try:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (name, email, phone, password) VALUES (%s, %s, %s, %s)",
                           (name, email, phone, hashed_pw))
            conn.commit()
            flash("Signup successful! Please login.", "success")
            return redirect(url_for('login'))
        except Exception as e:
            app.logger.error(f"Signup error: {e}")
            flash("Email already exists or error occurred.", "danger")
        finally:
            if conn: conn.close()
            
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        conn = get_db_connection()
        if not conn:
            flash("Login service unavailable.", "danger")
            return redirect(url_for('login'))
            
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
            user = cursor.fetchone()
        except Exception as e:
            app.logger.error(f"Login error: {e}")
            user = None
        finally:
            if conn: conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['user_name'] = user['name']
            session['role'] = user['role']
            flash(f"Welcome back, {user['name']}!", "success")
            
            next_page = request.args.get('next')
            if user['role'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(next_page or url_for('index'))
        else:
            flash("Invalid email or password", "danger")
            
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for('index'))

# --- Info Routes ---

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        
        conn = get_db_connection()
        if conn:
            try:
                cursor = conn.cursor()
                cursor.execute("INSERT INTO contact (name, email, message) VALUES (%s, %s, %s)", (name, email, message))
                conn.commit()
                flash("Message sent! We will get back to you soon.", "success")
            finally:
                conn.close()
        else:
            flash("Contact service unavailable.", "danger")
        return redirect(url_for('contact'))
        
    return render_template('contact.html')

# --- Admin Routes ---

@app.route('/admin/dashboard')
def admin_dashboard():
    if not is_admin():
        flash("Access denied.", "danger")
        return redirect(url_for('login'))
        
    conn = get_db_connection()
    if not conn: return redirect(url_for('index'))
    
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT COUNT(*) as count FROM users")
        total_users = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM pets")
        total_pets = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM orders")
        total_orders = cursor.fetchone()['count']
        
        cursor.execute("SELECT COUNT(*) as count FROM products")
        total_products = cursor.fetchone()['count']
        
        cursor.execute("""
            SELECT orders.*, users.name as user_name 
            FROM orders 
            JOIN users ON orders.user_id = users.id 
            ORDER BY orders.order_date DESC
        """)
        orders = cursor.fetchall()
        
        return render_template('admin/dashboard.html', total_users=total_users, total_pets=total_pets, total_orders=total_orders, total_products=total_products, orders=orders)
    except Exception as e:
        app.logger.error(f"Admin dashboard error: {e}")
        flash("Admin dashboard failed to load.", "danger")
        return redirect(url_for('index'))
    finally:
        if conn: conn.close()

@app.route('/admin/pets', methods=['GET', 'POST'])
def admin_pets():
    if not is_admin(): return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn: return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor()
        
        if request.method == 'POST':
            name = request.form.get('name')
            price = float(request.form.get('price'))
            category = request.form.get('category')
            description = request.form.get('description')
            
            file = request.files.get('image')
            filename = ""
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
            cursor.execute("INSERT INTO pets (name, price, category, description, image) VALUES (%s, %s, %s, %s, %s)",
                           (name, price, category, description, filename))
            conn.commit()
            flash("Pet added successfully!", "success")

        cursor.execute("SELECT * FROM pets")
        pets_list = cursor.fetchall()
        return render_template('admin/pets.html', pets=pets_list)
    except Exception as e:
        app.logger.error(f"Admin pets error: {e}")
        flash("Error managing pets.", "danger")
        return redirect(url_for('admin_dashboard'))
    finally:
        if conn: conn.close()

@app.route('/admin/delete_pet/<int:id>')
def delete_pet(id):
    if not is_admin(): return redirect(url_for('login'))
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM pets WHERE id = %s", (id,))
            conn.commit()
            flash("Pet deleted.", "info")
        finally:
            conn.close()
    return redirect(url_for('admin_pets'))

@app.route('/admin/products', methods=['GET', 'POST'])
def admin_products():
    if not is_admin(): return redirect(url_for('login'))
    
    conn = get_db_connection()
    if not conn: return redirect(url_for('admin_dashboard'))
    
    try:
        cursor = conn.cursor()
        
        if request.method == 'POST':
            name = request.form.get('name')
            price = float(request.form.get('price'))
            category = request.form.get('category')
            description = request.form.get('description')
            
            file = request.files.get('image')
            filename = ""
            if file:
                filename = secure_filename(file.filename)
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                
            cursor.execute("INSERT INTO products (name, price, category, description, image) VALUES (%s, %s, %s, %s, %s)",
                           (name, price, category, description, filename))
            conn.commit()
            flash("Product added successfully!", "success")

        cursor.execute("SELECT * FROM products")
        products_list = cursor.fetchall()
        return render_template('admin/products.html', products=products_list)
    except Exception as e:
        app.logger.error(f"Admin products error: {e}")
        flash("Error managing products.", "danger")
        return redirect(url_for('admin_dashboard'))
    finally:
        if conn: conn.close()

@app.route('/admin/delete_product/<int:id>')
def delete_product(id):
    if not is_admin(): return redirect(url_for('login'))
    conn = get_db_connection()
    if conn:
        try:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM products WHERE id = %s", (id,))
            conn.commit()
            flash("Product removed.", "info")
        finally:
            conn.close()
    return redirect(url_for('admin_products'))

# --- Error Handlers ---
@app.errorhandler(404)
def not_found_error(error):
    return "404 Not Found. The requested URL was not found on the server.", 404

@app.errorhandler(500)
def internal_error(error):
    app.logger.error(f'Server Error: {error}')
    return "500 Internal Server Error. We've logged the error and will investigate.", 500

# --- Health Route ---
@app.route('/health')
def health():
    conn = get_db_connection()
    db_status = "connected" if conn else "disconnected"
    if conn:
        conn.close()
        
    status = "healthy" if db_status == "connected" else "degraded"
    
    if 'text/html' in request.headers.get('Accept', ''):
        return render_template('health.html', status=status, db_status=db_status)
        
    return jsonify({
        "status": status,
        "database": db_status,
        "timestamp": datetime.now().isoformat()
    }), 200 if db_status == "connected" else 503

if __name__ == '__main__':
    # Disable debug mode automatically if in production env
    is_debug = os.environ.get('FLASK_ENV') != 'production'
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=is_debug)