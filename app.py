from flask import Flask, render_template, request, redirect, url_for, flash, send_file,jsonify
from flask_migrate import Migrate
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from models import db, Item, Transaction, User
from config import Config
import pandas as pd
from io import BytesIO
from datetime import datetime

app = Flask(__name__)
app.config.from_object(Config)

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Initialize database + default data
with app.app_context():
    db.create_all()

    # Create default admin user if none exists
    if User.query.count() == 0:
        admin = User(username='admin', password='admin123')
        db.session.add(admin)
        db.session.commit()

    # Auto-add original 30 items only if table is empty
    if Item.query.count() == 0:
        items_list = [
            "Paracetamol Tablets", "Amoxicillin Capsules", "Cough Syrup", "IV Fluids (Normal Saline)",
            "Gloves (Box)", "Syringes (5ml)", "Face Masks", "Hand Sanitizer", "Bandages", "Cotton Wool",
            "Gauze Pads", "Thermometer", "Blood Pressure Machine", "Stethoscope", "Antiseptic Solution",
            "Insulin Injection", "ORS Sachets", "Vitamin C Tablets", "Metformin Tablets", "Aspirin Tablets",
            "Surgical Blade", "IV Cannula", "Pregnancy Test Kit", "Rapid Malaria Test Kit", "Nebulizer",
            "Oxygen Mask", "Surgical Tape", "Glucose Test Strips", "Antimalarial Drugs", "Antibiotic Ointment"
        ]
        for name in items_list:
            db.session.add(Item(name=name))
        db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and user.password == request.form['password']:
            login_user(user)
            flash('Login successful', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid credentials', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('login'))

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

ITEMS_PER_PAGE = 15  # Change this number as needed (10, 15, 20, 25...)

@app.route('/dashboard')
@login_required
def dashboard():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    is_ajax = request.args.get('ajax', 'false').lower() == 'true'

    query = Item.query.order_by(Item.name)
    if search:
        query = query.filter(Item.name.ilike(f'%{search}%'))

    pagination = query.paginate(page=page, per_page=ITEMS_PER_PAGE, error_out=False)
    items = pagination.items

    if is_ajax:
        return jsonify({
            'html': render_template('_dashboard_table.html', 
                                   items=items, 
                                   pagination=pagination, 
                                   search=search, 
                                   page=page),
            'current_page': pagination.page,
            'total_pages': pagination.pages,
            'total_items': pagination.total
        })

    return render_template('dashboard.html',
                           items=items,
                           search=search,
                           pagination=pagination,
                           page=page)
@app.route('/total')

@app.route('/add_item', methods=['GET', 'POST'])
@login_required
def add_item():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash('Item name is required', 'danger')
            return redirect(url_for('add_item'))

        if Item.query.filter_by(name=name).first():
            flash(f'Item "{name}" already exists', 'warning')
            return redirect(url_for('add_item'))

        try:
            new_item = Item(
                name=name,
                unit_buying_price=float(request.form.get('buying_price', 0)),
                unit_selling_price=float(request.form.get('selling_price', 0)),
                opening_stock=int(request.form.get('opening_stock', 0)),
                current_stock=int(request.form.get('opening_stock', 0))
            )
            db.session.add(new_item)
            db.session.commit()
            flash(f'Item "{name}" added successfully', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding item: {str(e)}', 'danger')

    return render_template('add_item.html')
@app.route('/stock_in/<int:item_id>', methods=['GET', 'POST'])
@login_required
def stock_in(item_id):
    item = Item.query.get_or_404(item_id)
    if request.method == 'POST':
        try:
            qty = int(request.form['quantity'])
            transaction = Transaction(item_id=item.id, type='IN', quantity=qty,
                                    notes=request.form.get('notes', ''))
            item.current_stock += qty
            db.session.add(transaction)
            db.session.commit()
            flash(f'Added {qty} × {item.name}', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('stock_form.html', item=item, action='IN')
@app.route('/stock_out/<int:item_id>', methods=['GET', 'POST'])
@login_required
def stock_out(item_id):
    item = Item.query.get_or_404(item_id)
    if request.method == 'POST':
        try:
            qty = int(request.form['quantity'])
            if qty > item.current_stock:
                flash(f'Only {item.current_stock} available', 'danger')
                return redirect(url_for('stock_out', item_id=item_id))
            transaction = Transaction(item_id=item.id, type='OUT', quantity=qty,
                                    notes=request.form.get('notes', ''))
            item.current_stock -= qty
            db.session.add(transaction)
            db.session.commit()
            flash(f'Removed {qty} × {item.name}', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    # Changed from 'stock_out.html' to 'stock_form.html'
    return render_template('stock_form.html', item=item, action='OUT')

@app.route('/edit_item/<int:item_id>', methods=['GET', 'POST'])
@login_required
def edit_item(item_id):
    item = Item.query.get_or_404(item_id)
    if request.method == 'POST':
        try:
            item.unit_buying_price = float(request.form['buying_price'])
            item.unit_selling_price = float(request.form['selling_price'])
            db.session.commit()
            flash(f'Prices updated for {item.name}', 'success')
            return redirect(url_for('dashboard'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {str(e)}', 'danger')
    return render_template('edit_item.html', item=item)

@app.route('/history')
@login_required
def history():
    transactions = Transaction.query.order_by(Transaction.transaction_date.desc()).all()
    return render_template('history.html', transactions=transactions)
@app.route('/delete_item/<int:item_id>', methods=['POST'])
@login_required
def delete_item(item_id):
    item = Item.query.get_or_404(item_id)
    
    try:
        # Optional: extra safety check (e.g. prevent delete if current_stock > 0)
        # if item.current_stock > 0:
        #     flash(f'Cannot delete {item.name} – stock is not zero ({item.current_stock})', 'warning')
        #     return redirect(url_for('dashboard'))
        
        db.session.delete(item)           # This deletes the item
        db.session.commit()               # Transactions are auto-deleted (cascade)
        
        flash(f'Item "{item.name}" deleted successfully', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Error deleting item: {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))
@app.route('/export_excel')
@login_required
def export_excel():
    items = Item.query.all()
    data = []
    for item in items:
        data.append({
            'Item Name': item.name,
            'Opening Stock': item.opening_stock,
            'Entries (Stock In)': sum(t.quantity for t in item.transactions if t.type == 'IN'),
            'Outs (Stock Out)': sum(t.quantity for t in item.transactions if t.type == 'OUT'),
            'Unit Buying Price': item.unit_buying_price,
            'Unit Selling Price': item.unit_selling_price,
            'Current Stock': item.current_stock,
            'Total Buying Cost (Entries)': item.total_buying_cost(),
            'Total Sales Value (Outs)': item.total_sales_value(),
            'Profit': item.profit()
        })
        
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Medical Stock Management')
    output.seek(0)
    filename = f"medical_stock_{datetime.now().strftime('%Y-%m-%d_%H%M')}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename)
@app.route('/totals')
@login_required
def totals():
    items = Item.query.all()
    
    total_products = len(items)
    total_quantity = sum(item.current_stock for item in items)
    
    total_buying_value = sum(item.current_stock * item.unit_buying_price for item in items)
    total_selling_value = sum(item.current_stock * item.unit_selling_price for item in items)
    potential_profit = total_selling_value - total_buying_value
    
    # Total realized profit from all past sales
    total_realized_profit = sum(item.profit() for item in items)
    
    return render_template('totals.html',
                           total_products=total_products,
                           total_quantity=total_quantity,
                           total_buying_value=total_buying_value,
                           total_selling_value=total_selling_value,
                           potential_profit=potential_profit,
                           total_realized_profit=total_realized_profit)
    
@app.route('/live')
@app.route('/live_stock')
def live_stock():
    items = Item.query.order_by(Item.name).all()
    
    # Optional: add simple icon mapping (you can expand this)
    icon_map = {
        'tablet': '💊', 'capsule': '💊', 'syrup': '🧴', 'fluid': '💧', 'gloves': '🧤',
        'syringe': '💉', 'mask': '😷', 'sanitizer': '🧴', 'bandage': '🩹', 'cotton': '🧶',
        'thermometer': '🌡️', 'pressure': '❤️', 'stethoscope': '🩺', 'antiseptic': '🧴',
        'insulin': '💉', 'ors': '💧', 'vitamin': '🍊', 'metformin': '💊', 'aspirin': '💊',
        'blade': '🔪', 'cannula': '💉', 'pregnancy': '🧪', 'malaria': '🧪',
        'nebulizer': '🌬️', 'oxygen': '😷', 'tape': '🩹', 'glucose': '🧪',
        'antimalarial': '💊', 'ointment': '🧴'
    }
    
    for item in items:
        name_lower = item.name.lower()
        item.icon = '💊'  # default
        for key, icon in icon_map.items():
            if key in name_lower:
                item.icon = icon
                break
    
    return render_template('live_stock.html', items=items)    

if __name__ == '__main__':
    app.run(debug=True)