import yaml
import logging
from datetime import datetime, timedelta, time
from typing import List, Dict, Any
import pytz
from sqlalchemy import and_, func

from app.extensions import db
from app.models import Loan, ReminderNotification, User, Product
from app.utils.utils import send_email


class ReminderService:
    """Servizio per gestire i promemoria delle scadenze prestiti"""
    
    def __init__(self, config_path: str = 'reminder_config.yaml'):
        self.config_path = config_path
        self.config = self._load_config()
        self.logger = self._setup_logging()
    
    def _load_config(self) -> Dict[str, Any]:
        """Carica la configurazione dal file YAML"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            self.logger.error(f"File di configurazione {self.config_path} non trovato")
            return {}
        except yaml.YAMLError as e:
            self.logger.error(f"Errore nel parsing del file YAML: {e}")
            return {}
    
    def _setup_logging(self) -> logging.Logger:
        """Configura il logging per i promemoria"""
        logger = logging.getLogger('reminder_service')
        logger.setLevel(logging.INFO)
        
        if self.config.get('settings', {}).get('log_notifications', True):
            log_file = self.config.get('settings', {}).get('log_file', 'logs/reminders.log')
            
            # Crea la directory logs se non esiste
            import os
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            handler = logging.FileHandler(log_file)
            formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def get_timezone(self) -> pytz.timezone:
        """Ottiene il timezone configurato"""
        tz_name = self.config.get('settings', {}).get('timezone', 'Europe/Rome')
        return pytz.timezone(tz_name)
    
    def should_send_reminders_now(self) -> bool:
        """Verifica se è il momento giusto per inviare i promemoria"""
        if not self.config.get('settings', {}).get('enabled', True):
            return False
        
        send_time_str = self.config.get('settings', {}).get('send_time', '09:00')
        send_hour, send_minute = map(int, send_time_str.split(':'))
        
        tz = self.get_timezone()
        now = datetime.now(tz)
        
        # Controlla se siamo nell'orario di invio (con tolleranza di 5 minuti)
        target_time = now.replace(hour=send_hour, minute=send_minute, second=0, microsecond=0)
        time_diff = abs((now - target_time).total_seconds())
        
        return time_diff <= 300  # 5 minuti di tolleranza
    
    def get_loans_needing_reminders(self) -> List[Loan]:
        """Ottiene tutti i prestiti che necessitano di promemoria"""
        if not self.config.get('settings', {}).get('enabled', True):
            return []
        
        # Usa timezone configurato per la data corrente
        tz = self.get_timezone()
        now_local = datetime.now(tz).replace(tzinfo=None)  # Rimuovi tzinfo per compatibilità DB
        loans_to_remind = []
        
        # Per ogni tipo di promemoria configurato
        for reminder_type, reminder_config in self.config.get('reminders', {}).items():
            if not reminder_config.get('enabled', True):
                continue
            
            days_before = reminder_config.get('days_before', 0)
            # Calcola la data di scadenza per cui inviare promemoria oggi
            target_date = now_local.date() + timedelta(days=days_before)
            
            # Trova i prestiti che scadono nella data target
            loans = db.session.query(Loan).filter(
                and_(
                    Loan.status == 'approved',  # Solo prestiti approvati
                    func.date(Loan.end_date) == target_date
                )
            ).all()
            
            # Filtra i prestiti per cui non è stato già inviato questo tipo di promemoria
            for loan in loans:
                if not self._notification_already_sent(loan.id, reminder_type):
                    loans_to_remind.append((loan, reminder_type, reminder_config))
        
        return loans_to_remind
    
    def _notification_already_sent(self, loan_id: int, reminder_type: str) -> bool:
        """Verifica se una notifica è già stata inviata per questo prestito e tipo"""
        notification = db.session.query(ReminderNotification).filter(
            and_(
                ReminderNotification.loan_id == loan_id,
                ReminderNotification.reminder_type == reminder_type
            )
        ).first()
        
        return notification is not None
    
    def send_reminder(self, loan: Loan, reminder_type: str, reminder_config: Dict) -> bool:
        """Invia un singolo promemoria"""
        try:
            # Verifica se non è già stato inviato
            if self._notification_already_sent(loan.id, reminder_type):
                self.logger.info(f"Promemoria {reminder_type} già inviato per loan {loan.id}")
                return True
            
            # Ottieni i dati necessari
            borrower = loan.borrower
            product = loan.product
            
            # Invia l'email
            send_email(
                subject=reminder_config.get('subject', 'Promemoria scadenza prestito'),
                recipient=borrower.email,
                template=reminder_config.get('template', 'backend/reminder_default'),
                borrower=borrower,
                product=product,
                loan=loan,
                reminder_type=reminder_type,
                days_before=reminder_config.get('days_before', 0),
                due_date=loan.end_date.strftime('%d/%m/%Y')
            )
            
            # Registra la notifica nel database
            notification = ReminderNotification(
                loan_id=loan.id,
                reminder_type=reminder_type,
                recipient_email=borrower.email
            )
            db.session.add(notification)
            db.session.commit()
            
            self.logger.info(
                f"Promemoria {reminder_type} inviato per loan {loan.id} a {borrower.email}"
            )
            return True
            
        except Exception as e:
            self.logger.error(
                f"Errore nell'invio promemoria {reminder_type} per loan {loan.id}: {str(e)}"
            )
            db.session.rollback()
            return False
    
    def process_all_reminders(self, force: bool = False) -> Dict[str, int]:
        """Processa tutti i promemoria necessari
        
        Args:
            force: Se True, bypassa il controllo dell'orario per test/debug
        """
        if not force and not self.should_send_reminders_now():
            self.logger.info("Non è il momento di inviare promemoria")
            return {'processed': 0, 'sent': 0, 'errors': 0}
        
        loans_to_remind = self.get_loans_needing_reminders()
        
        stats = {'processed': 0, 'sent': 0, 'errors': 0}
        
        for loan, reminder_type, reminder_config in loans_to_remind:
            stats['processed'] += 1
            
            if self.send_reminder(loan, reminder_type, reminder_config):
                stats['sent'] += 1
            else:
                stats['errors'] += 1
        
        self.logger.info(
            f"Promemoria processati: {stats['processed']}, inviati: {stats['sent']}, errori: {stats['errors']}"
        )
        
        return stats
    
    def cleanup_old_notifications(self, days_old: int = 30) -> int:
        """Pulisce le notifiche vecchie per mantenere il database ordinato"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        
        deleted_count = db.session.query(ReminderNotification).filter(
            ReminderNotification.sent_at < cutoff_date
        ).delete()
        
        db.session.commit()
        
        self.logger.info(f"Rimosse {deleted_count} notifiche vecchie")
        return deleted_count