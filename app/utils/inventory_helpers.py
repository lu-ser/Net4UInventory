from datetime import datetime
from ..models import Loan

def get_reserved_quantity(product_id, date=None):
    """
    Calcola la quantità riservata per un prodotto in una data specifica.
    Se non viene specificata una data, usa la data corrente.
    """
    if date is None:
        date = datetime.utcnow()
    
    # Calcola la somma delle quantità per tutti i prestiti attivi che si sovrappongono alla data specificata
    loans = Loan.query.filter(
        Loan.product_id == product_id,
        Loan.start_date <= date,
        Loan.end_date >= date,
        Loan.status.in_(['approved', 'in_review'])  # Include anche quelli in review
    ).all()
    
    total_reserved = sum(loan.quantity for loan in loans)
    return total_reserved

def get_active_loans(product_id, date=None):
    """
    Restituisce tutti i prestiti attivi per un prodotto in una data specifica.
    """
    if date is None:
        date = datetime.utcnow()
        
    active_loans = Loan.query.filter(
        Loan.product_id == product_id,
        Loan.start_date <= date,
        Loan.end_date >= date,
        Loan.status.in_(['approved', 'in_review'])
    ).all()
    return active_loans

def get_available_quantity(product_id, date=None):
    """
    Calcola la quantità disponibile per un prodotto in una data specifica.
    """
    from ..models import Product
    
    product = Product.query.get(product_id)
    if not product:
        return 0
        
    reserved = get_reserved_quantity(product_id, date)
    available = max(0, product.quantity - reserved)  # Non può essere negativo
    return available