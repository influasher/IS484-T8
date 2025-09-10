import os
import sys

# Add the Backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '../../..'))

from app import create_app, db
from app.models.entity import Entity

def seed_entities():
    app = create_app()
    
    with app.app_context():
        # Check if entities already exist
        existing_entities = Entity.query.count()
        if existing_entities > 0:
            print(f"Database already has {existing_entities} entities.")
            print("Run 'python clear_entities.py' first to clear existing entities.")
            return
        
        # Define the entities to seed
        entities_to_seed = [
            'Tesla',
            'TSMC', 
            'Apple',
            'HSBC',
            'Aramco'
        ]
        
        print(f"Seeding {len(entities_to_seed)} entities...")
        
        try:
            for entity_name in entities_to_seed:
                entity = Entity(name=entity_name)
                db.session.add(entity)
            
            db.session.commit()
            print(f"Successfully seeded {len(entities_to_seed)} entities!")
            
            # List the seeded entities
            for entity_name in entities_to_seed:
                print(f"  ✓ {entity_name}")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding entities: {e}")

if __name__ == '__main__':
    seed_entities()