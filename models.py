from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_login import UserMixin

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)  # plain text – for learning only

class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), unique=True, nullable=False)
    opening_stock = db.Column(db.Integer, default=0)
    unit_buying_price = db.Column(db.Float(precision=2), default=0.0)
    unit_selling_price = db.Column(db.Float(precision=2), default=0.0)
    current_stock = db.Column(db.Integer, default=0)

    transactions = db.relationship('Transaction', backref='item', lazy=True, cascade="all, delete-orphan")

    def total_buying_cost(self):
        return sum(t.quantity * self.unit_buying_price for t in self.transactions if t.type == 'IN')

    def total_sales_value(self):
        return sum(t.quantity * self.unit_selling_price for t in self.transactions if t.type == 'OUT')

    def profit(self):
        return self.total_sales_value() - self.total_buying_cost()
    
    def total_stock_in(self):
        """Calculate total units received"""
        return sum(t.quantity for t in self.transactions if t.type == 'IN')
    
    def total_stock_out(self):
        """Calculate total units sold/removed"""
        return sum(t.quantity for t in self.transactions if t.type == 'OUT')
    
    def recent_transactions(self, limit=5):
        """Get recent transactions for this item"""
        return sorted(self.transactions, 
                     key=lambda x: x.transaction_date, 
                     reverse=True)[:limit]

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    type = db.Column(db.Enum('IN', 'OUT'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)
    notes = db.Column(db.Text, nullable=True)