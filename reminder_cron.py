#!/usr/bin/env python3
"""
INVIA PROMEMORIA EMAIL - FILE SEMPLICE
"""

import sys
import os

# Aggiungi il percorso dell'app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.reminder_service import ReminderService

def main():
    print("📧 INVIO PROMEMORIA EMAIL")
    print("=" * 50)
    
    app = create_app()
    
    with app.app_context():
        reminder_service = ReminderService()
        
        print("🔍 Cerco prestiti che necessitano promemoria...")
        loans_to_remind = reminder_service.get_loans_needing_reminders()
        
        if not loans_to_remind:
            print("✅ Nessun promemoria da inviare!")
            return
        
        print(f"📋 Trovati {len(loans_to_remind)} promemoria da inviare:")
        print()
        
        for loan, reminder_type, config in loans_to_remind:
            borrower = loan.borrower
            product = loan.product
            
            print(f"📧 {reminder_type.upper()}:")
            print(f"   • Prodotto: {product.name}")
            print(f"   • A: {borrower.name} {borrower.surname} ({borrower.email})")
            print(f"   • Scadenza: {loan.end_date.strftime('%d/%m/%Y')}")
        
        print()
        print("🚀 INVIO AUTOMATICO dei promemoria...")
        
        stats = reminder_service.process_all_reminders(force=True)
        
        print(f"\n✅ COMPLETATO!")
        print(f"   📊 Processati: {stats['processed']}")
        print(f"   📧 Inviati: {stats['sent']}")
        print(f"   ❌ Errori: {stats['errors']}")
        
        if stats['errors'] > 0:
            print("\n⚠️  Controlla i log per gli errori")
        elif stats['sent'] > 0:
            print("\n🎉 Email inviate con successo!")
        else:
            print("\n💡 Nessuna email da inviare (probabilmente già inviate)")

if __name__ == '__main__':
    main()