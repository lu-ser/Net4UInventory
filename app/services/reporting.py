import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.models import Product, Loan

def inventory_status_report():
    products = Product.query.all()
    report = {product.id: {'name': product.name, 'total': product.quantity, 'available': product.quantity - sum(loan.quantity for loan in product.loans if loan.status != 'returned')} for product in products}
    return report

def loans_period_report(start_date, end_date):
    return Loan.query.filter(Loan.start_date >= start_date, Loan.end_date <= end_date).all()
