#!/usr/bin/env python3
"""
Script di test per verificare che il sistema promemoria funzioni correttamente.
"""

import sys
import os

# Aggiungi il percorso dell'app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.services.reminder_service import ReminderService
from app.models import Loan, Product, User
from datetime import datetime, timedelta

def test_reminder_system():
    """Testa il sistema promemoria"""
    print("=== Test Sistema Promemoria ===\n")
    
    # Crea l'app context
    app = create_app()
    
    with app.app_context():
        # Inizializza il servizio
        reminder_service = ReminderService()
        
        print("1. Controllo configurazione...")
        config = reminder_service.config
        if not config:
            print("❌ ERRORE: File di configurazione non trovato!")
            return
        
        print(f"✅ Configurazione caricata")
        print(f"   - Sistema abilitato: {config.get('settings', {}).get('enabled', False)}")
        print(f"   - Orario invio: {config.get('settings', {}).get('send_time', 'N/A')}")
        
        print("\n2. Controllo timezone...")
        try:
            tz = reminder_service.get_timezone()
            print(f"✅ Timezone: {tz}")
        except Exception as e:
            print(f"❌ Errore timezone: {e}")
            return
        
        print("\n3. Ricerca prestiti che necessitano promemoria...")
        try:
            loans_to_remind = reminder_service.get_loans_needing_reminders()
            print(f"✅ Trovati {len(loans_to_remind)} prestiti da processare")
            
            for loan, reminder_type, config in loans_to_remind:
                print(f"   - Loan ID {loan.id}: {reminder_type} (scade il {loan.end_date.strftime('%d/%m/%Y')})")
                
        except Exception as e:
            print(f"❌ Errore nella ricerca: {e}")
            return
        
        print("\n4. Test invio promemoria (REALE)...")
        try:
            if loans_to_remind:
                print(f"   Tentativo di invio per {len(loans_to_remind)} prestiti...")
                # Usa force=True per bypassare il controllo orario
                stats = reminder_service.process_all_reminders(force=True)
                print(f"   ✅ Risultato: {stats['processed']} processati, {stats['sent']} inviati, {stats['errors']} errori")
                
                if stats['errors'] > 0:
                    print("   ⚠️  Ci sono stati degli errori nell'invio")
                elif stats['sent'] > 0:
                    print("   🎉 Email inviate con successo!")
                else:
                    print("   ℹ️  Nessuna email da inviare (probabilmente già inviate)")
            else:
                print("   ℹ️  Nessun prestito necessita di promemoria al momento")
                # Test con force per vedere se il sistema funziona comunque
                stats = reminder_service.process_all_reminders(force=True)
                print(f"   📊 Test force: {stats}")
        except Exception as e:
            print(f"   ❌ Errore nel test invio: {e}")
        
        print("\n5. Controllo database...")
        try:
            from app.models import ReminderNotification
            total_notifications = ReminderNotification.query.count()
            print(f"✅ Notifiche totali nel database: {total_notifications}")
        except Exception as e:
            print(f"❌ Errore database: {e}")
            print("   Probabilmente devi eseguire la migrazione: flask db upgrade")
        
        print("\n6. Controllo prestiti attivi...")
        try:
            active_loans = Loan.query.filter_by(status='approved').count()
            print(f"✅ Prestiti attivi: {active_loans}")
            
            # Mostra i prossimi in scadenza (fix deprecation warning)
            now = datetime.now()
            upcoming_loans = Loan.query.filter(
                Loan.status == 'approved',
                Loan.end_date >= now,
                Loan.end_date <= now + timedelta(days=10)
            ).order_by(Loan.end_date).limit(5).all()
            
            if upcoming_loans:
                print("   Prossimi in scadenza (10 giorni):")
                for loan in upcoming_loans:
                    product = loan.product
                    borrower = loan.borrower
                    days_left = (loan.end_date.date() - datetime.now().date()).days
                    print(f"     - {product.name} (ID:{loan.id}) - {borrower.name} {borrower.surname} - tra {days_left} giorni")
            else:
                print("   Nessun prestito in scadenza nei prossimi 10 giorni")
                
        except Exception as e:
            print(f"❌ Errore controllo prestiti: {e}")
        
        print("\n=== Test Completato ===")
        print("\nProssimi passi:")
        print("1. Installa dipendenze: pip install -r requirements_reminders.txt")
        print("2. Esegui migrazione: flask db upgrade")
        print("3. Configura cron job o avvia daemon")
        print("4. Monitora su /admin/reminders/status")

if __name__ == '__main__':
    test_reminder_system()