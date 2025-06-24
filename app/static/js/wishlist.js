/**
 * WISHLIST FUNCTIONALITY
 * Sistema di gestione wishlist per l'inventario
 */

class WishlistManager {
    constructor() {
        this.init();
    }

    init() {
        // Carica il conteggio wishlist al caricamento della pagina
        document.addEventListener('DOMContentLoaded', () => {
            this.loadWishlistCount();
        });
    }

    /**
     * Toggle wishlist per un prodotto
     * @param {number} productId - ID del prodotto
     * @param {HTMLElement} buttonElement - Elemento button cliccato
     */
    toggleWishlist(productId, buttonElement) {
        const icon = buttonElement.querySelector('i');
        const originalClass = icon.className;

        // Loading state
        icon.className = 'fas fa-spinner fa-spin';
        buttonElement.disabled = true;

        fetch(`/toggle_wishlist/${productId}`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            }
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    // Aggiorna l'icona in base all'azione
                    if (data.action === 'added') {
                        icon.className = 'fas fa-heart text-danger';
                        buttonElement.setAttribute('title', 'Rimuovi dalla wishlist');
                        buttonElement.classList.remove('btn-outline-danger');
                        buttonElement.classList.add('btn-danger');
                    } else {
                        icon.className = 'far fa-heart';
                        buttonElement.setAttribute('title', 'Aggiungi alla wishlist');
                        buttonElement.classList.remove('btn-danger');
                        buttonElement.classList.add('btn-outline-danger');

                        // Se siamo nella pagina wishlist, rimuovi la riga
                        if (window.location.pathname === '/my_wishlist') {
                            this.removeProductFromWishlistTable(buttonElement);
                        }
                    }

                    // Aggiorna il badge nella sidebar
                    this.updateWishlistBadge(data.wishlist_count);

                    // Mostra messaggio di successo
                    this.showToast(data.message, 'success', data.icon);

                } else {
                    // Ripristina icona originale in caso di errore
                    icon.className = originalClass;
                    this.showToast(data.message, 'error', '❌');
                }
            })
            .catch(error => {
                console.error('Errore wishlist:', error);
                // Ripristina icona originale in caso di errore
                icon.className = originalClass;
                this.showToast('Errore di connessione', 'error', '❌');
            })
            .finally(() => {
                buttonElement.disabled = false;
            });
    }

    /**
     * Rimuove una riga dalla tabella nella pagina wishlist
     * @param {HTMLElement} buttonElement 
     */
    removeProductFromWishlistTable(buttonElement) {
        const row = buttonElement.closest('tr');
        if (row) {
            // Animazione fade out
            row.style.transition = 'opacity 0.3s ease';
            row.style.opacity = '0';

            setTimeout(() => {
                row.remove();

                // Se non ci sono più prodotti, ricarica per mostrare messaggio vuoto
                const tbody = document.querySelector('tbody');
                if (!tbody || tbody.children.length === 0) {
                    setTimeout(() => location.reload(), 500);
                }
            }, 300);
        }
    }

    /**
     * Aggiorna il badge conteggio wishlist nella sidebar
     * @param {number} count - Numero di elementi nella wishlist
     */
    updateWishlistBadge(count) {
        const badge = document.getElementById('wishlist-badge');
        if (badge) {
            badge.textContent = count;
            badge.style.display = count > 0 ? 'inline' : 'none';

            // Animazione del badge
            if (count > 0) {
                badge.style.transform = 'scale(1.2)';
                setTimeout(() => {
                    badge.style.transform = 'scale(1)';
                }, 200);
            }
        }
    }

    /**
     * Carica il conteggio wishlist dal server
     */
    loadWishlistCount() {
        fetch('/wishlist_count')
            .then(response => response.json())
            .then(data => this.updateWishlistBadge(data.count))
            .catch(error => console.log('Errore nel caricamento conteggio wishlist:', error));
    }

    /**
     * Mostra notifiche toast
     * @param {string} message - Messaggio da mostrare
     * @param {string} type - Tipo di notifica (success, error)
     * @param {string} icon - Icona da mostrare
     */
    showToast(message, type, icon) {
        // Rimuovi toast esistenti
        const existingToasts = document.querySelectorAll('.wishlist-toast');
        existingToasts.forEach(toast => toast.remove());

        const alertClass = type === 'success' ? 'alert-success' : 'alert-danger';
        const toastId = 'toast-' + Date.now();

        const alertHtml = `
            <div id="${toastId}" class="alert ${alertClass} alert-dismissible fade show position-fixed wishlist-toast" 
                 style="top: 20px; right: 20px; z-index: 9999; max-width: 400px; transition: all 0.3s ease;">
                ${icon} ${message}
                <button type="button" class="close" data-dismiss="alert" onclick="document.getElementById('${toastId}').remove()">
                    <span>&times;</span>
                </button>
            </div>
        `;

        document.body.insertAdjacentHTML('beforeend', alertHtml);

        // Auto-remove dopo 4 secondi
        setTimeout(() => {
            const toast = document.getElementById(toastId);
            if (toast) {
                toast.style.opacity = '0';
                toast.style.transform = 'translateX(100%)';
                setTimeout(() => toast.remove(), 300);
            }
        }, 4000);
    }

    /**
     * Inizializza tutti i pulsanti wishlist nella pagina
     */
    initializeWishlistButtons() {
        const wishlistButtons = document.querySelectorAll('[data-wishlist-btn]');
        wishlistButtons.forEach(button => {
            const productId = button.getAttribute('data-product-id');
            if (productId) {
                button.addEventListener('click', (e) => {
                    e.preventDefault();
                    this.toggleWishlist(parseInt(productId), button);
                });
            }
        });
    }

    /**
     * Aggiorna lo stato di tutti i pulsanti wishlist nella pagina
     * @param {Array} wishlistProductIds - Array di ID prodotti nella wishlist
     */
    updateWishlistButtonsState(wishlistProductIds) {
        const wishlistButtons = document.querySelectorAll('[data-wishlist-btn]');
        wishlistButtons.forEach(button => {
            const productId = parseInt(button.getAttribute('data-product-id'));
            const icon = button.querySelector('i');

            if (wishlistProductIds.includes(productId)) {
                icon.className = 'fas fa-heart text-danger';
                button.setAttribute('title', 'Rimuovi dalla wishlist');
                button.classList.remove('btn-outline-danger');
                button.classList.add('btn-danger');
            } else {
                icon.className = 'far fa-heart';
                button.setAttribute('title', 'Aggiungi alla wishlist');
                button.classList.remove('btn-danger');
                button.classList.add('btn-outline-danger');
            }
        });
    }
}

// Inizializza il manager della wishlist
const wishlistManager = new WishlistManager();

// Funzioni globali per compatibilità con gli onclick esistenti
function toggleWishlist(productId, buttonElement) {
    wishlistManager.toggleWishlist(productId, buttonElement);
}

// Funzioni helper per sviluppi futuri
window.WishlistManager = WishlistManager;
window.wishlistManager = wishlistManager;