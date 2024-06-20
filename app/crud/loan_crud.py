# CRUD per LOAN
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.models import Loan
from app.extensions import db

def create_loan(product_id, borrower_id, manager_id, start_date, end_date, status='pending', extension_requested=False, new_end_date=None):
    """Crea un nuovo prestito con specifiche complete."""
    new_loan = Loan(
        product_id=product_id,
        borrower_id=borrower_id,
        manager_id=manager_id,
        start_date=start_date,
        end_date=end_date,
        status=status,
        extension_requested=extension_requested,
        new_end_date=new_end_date
    )
    db.session.add(new_loan)
    db.session.commit()
    return new_loan

def update_loan(loan_id, **kwargs):
    """Aggiorna le proprietà di un prestito esistente."""
    loan = Loan.query.get(loan_id)
    if loan:
        for key, value in kwargs.items():
            setattr(loan, key, value)
        db.session.commit()
        return loan
    return None

def delete_loan(loan_id):
    """Elimina un prestito specificato dall'ID."""
    loan = Loan.query.get(loan_id)
    if loan:
        db.session.delete(loan)
        db.session.commit()
        return True
    return False