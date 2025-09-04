from app import create_app, db
from app.models.news import News

def clear_news():
    app = create_app()
    
    with app.app_context():
        # Check if news exist
        news_count = News.query.count()
        
        if news_count == 0:
            print("No news articles found in database.")
            return
        
        print(f"Found {news_count} news articles in database.")
        
        # Clear all news
        try:
            News.query.delete()
            db.session.commit()
            print(f"Successfully deleted all {news_count} news articles from database.")
        except Exception as e:
            db.session.rollback()
            print(f"Error deleting news articles: {e}")

if __name__ == '__main__':
    clear_news()