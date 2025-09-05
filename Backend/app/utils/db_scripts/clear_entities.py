import os
import sys

# Add the Backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from app import create_app, db
from app.models.entity import Entity

def clear_entities():
    app = create_app()
    
    with app.app_context():
        # Count existing entities
        entity_count = Entity.query.count()
        
        if entity_count == 0:
            print("No entities found in database.")
            return
        
        print(f"Found {entity_count} entities in database.")
        
        try:
            # Delete all entities
            Entity.query.delete()
            db.session.commit()
            print(f"Successfully deleted all {entity_count} entities from database.")
        except Exception as e:
            db.session.rollback()
            print(f"Error clearing entities: {e}")

if __name__ == '__main__':
    clear_entities()