from flask import flash
from flask import session

def flash_message(message, category='info'):
    icon_map = {
        'info': 'info',
        'success': 'success',
        'warning': 'warning',
        'danger': 'error',
        'error': 'error'
    }
    icon = icon_map.get(category, 'info')
    session['flash_message'] = (icon, message)