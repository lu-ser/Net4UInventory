import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.models import Product, ProductCategory, Loan
from app.extensions import db
def search_products_by_category(category_id):
    return Product.query.join(ProductCategory).filter_by(category_id=category_id).all()

def search_available_products():
    return Product.query.filter(Product.quantity > 0).all()

def search_loan_history(user_id):
    return Loan.query.filter_by(borrower_id=user_id).order_by(Loan.start_date.desc()).all()

#Automazione del Processo di Restituzione
def return_product(loan_id):
    loan = Loan.query.get(loan_id)
    if loan and loan.status == 'approved':
        product = Product.query.get(loan.product_id)
        product.quantity += 1  # Aggiorna la quantità disponibile
        loan.status = 'returned'
        db.session.commit()


def check_product_availability(product_id, start_date, end_date):
    product = Product.query.get(product_id)
    if not product:
        return False, 0

    overlapping_loans = Loan.query.filter(
        Loan.product_id == product_id,
        Loan.end_date >= start_date,
        Loan.start_date <= end_date,
        Loan.status == 'approved'
    ).all()

    total_loaned = sum(loan.quantity for loan in overlapping_loans)
    available_quantity = product.quantity - total_loaned
    print(f"Debug: Total quantity={product.quantity}, Loaned during period={total_loaned}, Available={available_quantity}")
    
    return available_quantity > 0, available_quantity



