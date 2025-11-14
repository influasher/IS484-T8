import csv
import os
import sys
from datetime import datetime

# Add the Backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from app import create_app, db
from app.models.news import News


def seed_news():
    app = create_app()

    with app.app_context():
        # Check if news already exist
        existing_news = News.query.count()
        if existing_news > 0:
            print(f"Database already has {existing_news} news articles.")
            print("Run 'python clear_news.py' first to clear existing news.")
            return

        # Path to the CSV file
        csv_path = "old_migrations/db/migration-scripts/news_data_cleaned.csv"

        if not os.path.exists(csv_path):
            print(f"❌ CSV file not found at: {csv_path}")
            return

        print(f"📰 Loading news data from {csv_path}...")

        try:
            with open(csv_path, "r", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                news_count = 0

                for row in reader:
                    # Parse entities if they exist (assuming comma-separated)
                    entities = []
                    if row.get("entities"):
                        entities = [
                            entity.strip().strip("{{}}").strip('"')
                            for entity in row["entities"].split(",")
                            if entity.strip()
                        ]

                    # Parse published_date (adjust format as needed)
                    published_date = None
                    if row.get("published_date"):
                        try:
                            # Try different date formats
                            date_str = row["published_date"].strip()
                            for date_format in [
                                "%Y-%m-%d %H:%M:%S.%f",
                                "%Y-%m-%d %H:%M:%S",
                                "%Y-%m-%d",
                                "%m/%d/%Y",
                            ]:
                                try:
                                    published_date = datetime.strptime(
                                        date_str, date_format
                                    )
                                    break
                                except ValueError:
                                    continue
                        except:
                            published_date = datetime.now()  # Fallback
                    else:
                        published_date = datetime.now()

                    # Create news article
                    news_article = News(
                        publisher=row.get("publisher", "Unknown"),
                        description=row.get("description", ""),
                        published_date=published_date,
                        title=row.get("title", "Untitled"),
                        url=row.get("url", ""),
                        entities=entities if entities else None,
                        sentiment=row.get("sentiment"),
                        summary=row.get("summary"),
                    )

                    db.session.add(news_article)
                    news_count += 1

                    if news_count % 100 == 0:  # Progress indicator
                        print(f"Processed {news_count} articles...")

                db.session.commit()
                print(f"Successfully seeded {news_count} news articles!")

        except Exception as e:
            db.session.rollback()
            print(f"Error seeding news data: {e}")


if __name__ == "__main__":
    seed_news()
