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
        
        # Define the entities to seed with their tickers and summaries
        entities_to_seed = [
            {
                'name': 'Tesla',
                'ticker': 'TSLA',
                'summary': 'Electric vehicle and clean energy company led by Elon Musk, focusing on sustainable transportation and energy solutions.'
            },
            {
                'name': 'TSMC', 
                'ticker': 'TSM',
                'summary': 'Taiwan Semiconductor Manufacturing Company, the world\'s largest contract chip manufacturer and semiconductor foundry.'
            },
            {
                'name': 'Apple',
                'ticker': 'AAPL',
                'summary': 'Multinational technology company known for consumer electronics, software, and digital services including iPhone, Mac, and App Store.'
            },
            {
                'name': 'HSBC',
                'ticker': 'HSBC',
                'summary': 'British multinational investment bank and financial services holding company, one of the largest banks in the world.'
            },
            {
                'name': 'Aramco',
                'ticker': '2222.SR',
                'summary': 'Saudi Arabian multinational petroleum and natural gas company, one of the world\'s largest oil producers.'
            }
        ]
        
        print(f"Seeding {len(entities_to_seed)} entities...")
        
        try:
            for entity_data in entities_to_seed:
                entity = Entity(
                    name=entity_data['name'],
                    ticker=entity_data['ticker'],
                    summary=entity_data['summary']
                )
                db.session.add(entity)
            
            db.session.commit()
            print(f"Successfully seeded {len(entities_to_seed)} entities!")
            
            # List the seeded entities
            for entity_data in entities_to_seed:
                print(f"  {entity_data['name']} ({entity_data['ticker']})")
                
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding entities: {e}")

if __name__ == '__main__':
    seed_entities()