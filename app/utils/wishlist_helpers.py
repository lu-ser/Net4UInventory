from ..models import User, Product

def is_in_wishlist(user_id, product_id):
    """Controlla se un prodotto è nella wishlist dell'utente"""
    user = User.query.get(user_id)
    product = Product.query.get(product_id)
    return product in user.wishlist if user and product else False

def get_wishlist_count(user_id):
    """Ottiene il conteggio della wishlist dell'utente"""
    user = User.query.get(user_id)
    return len(user.wishlist) if user else 0

def get_user_wishlist(user_id):
    """Ottiene tutti i prodotti nella wishlist dell'utente"""
    user = User.query.get(user_id)
    return user.wishlist if user else []