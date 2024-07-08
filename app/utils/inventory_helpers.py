from datetime import datetime
from ..models import Loan
def get_reserved_quantity(product_id):
    # Calculate the sum of quantities for all active loans that overlap today's date
    today = datetime.utcnow()
    loans = Loan.query.filter(
        Loan.product_id == product_id,
        Loan.start_date <= today,
        Loan.end_date >= today,
        Loan.status == 'approved'  # Assuming 'approved' loans affect available inventory
    ).all()
    return sum(loan.quantity for loan in loans)

def get_active_loans(product_id):
    today = datetime.utcnow()
    active_loans = Loan.query.filter(
        Loan.product_id == product_id,
        Loan.start_date <= today,
        Loan.end_date >= today,
        Loan.status == 'approved'
    ).all()
    return active_loans