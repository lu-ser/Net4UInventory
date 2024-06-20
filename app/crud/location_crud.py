# CRUD for Location
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.models import Location
from app.extensions import db
def create_location(pavilion, room, cabinet):
    new_location = Location(pavilion=pavilion, room=room, cabinet=cabinet)
    db.session.add(new_location)
    db.session.commit()
    return new_location

def update_location(location_id, pavilion=None, room=None, cabinet=None):
    location = Location.query.get(location_id)
    if location:
        location.pavilion = pavilion if pavilion is not None else location.pavilion
        location.room = room if room is not None else location.room
        location.cabinet = cabinet if cabinet is not None else location.cabinet
        db.session.commit()
        return location
    return None

def delete_location(location_id):
    location = Location.query.get(location_id)
    if location:
        db.session.delete(location)
        db.session.commit()
        return True
    return False