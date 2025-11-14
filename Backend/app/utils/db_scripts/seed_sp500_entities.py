#!/usr/bin/env python3
"""
S&P 500 Companies Seeder
Inserts top 100 S&P 500 companies into the entity table with name, ticker, summary, and sector.
Sentiment scores (confidence_score, time_decay, simple_average) are left NULL and will be calculated by the sentiment aggregator.
"""

import os
import sys
import requests
import yfinance as yf
from datetime import datetime

# Add the Backend directory to Python path
sys.path.append(os.path.join(os.path.dirname(__file__), "../../.."))

from app import create_app, db
from app.models.entity import Entity

# Allowed sectors from frontend
ALLOWED_SECTORS = [
    "Information Technology",
    "Financials",
    "Health Care",
    "Consumer Staples",
    "Industrials",
    "Materials",
    "Communication Services",
    "Consumer Discretionary",
    "Utilities",
    "Energy",
    "Real Estate",
]

# GICS sector mapping to frontend sectors
SECTOR_MAPPING = {
    "Information Technology": "Information Technology",
    "Financials": "Financials",
    "Health Care": "Health Care",
    "Healthcare": "Health Care",
    "Consumer Staples": "Consumer Staples",
    "Industrials": "Industrials",
    "Materials": "Materials",
    "Communication Services": "Communication Services",
    "Consumer Discretionary": "Consumer Discretionary",
    "Utilities": "Utilities",
    "Energy": "Energy",
    "Real Estate": "Real Estate"
}


def map_sector(gics_sector):
    """Map GICS sector to allowed sectors"""
    return SECTOR_MAPPING.get(gics_sector, None)


def get_sp500_companies():
    """
    Fetch S&P 500 companies list from Wikipedia and get additional data from yfinance
    Returns top 100 companies by market cap from allowed sectors only
    """
    print("Fetching S&P 500 companies list from Wikipedia...")

    try:
        # Get S&P 500 companies list from Wikipedia
        import pandas as pd

        # Wikipedia has a table of S&P 500 companies
        url = "https://en.wikipedia.org/wiki/List_of_S%26P_500_companies"

        # Use headers to avoid 403 blocking
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

        tables = pd.read_html(url, header=0, storage_options={'User-Agent': headers['User-Agent']})

        # Find the correct table (first one is usually the current companies)
        sp500_df = None
        for i, table in enumerate(tables):
            print(f"Table {i}: {table.shape} - columns: {list(table.columns)[:3]}...")
            if len(table.columns) >= 3 and table.shape[0] > 400:  # S&P 500 should have ~500 companies
                sp500_df = table
                print(f"Using table {i} as the S&P 500 companies table")
                break

        if sp500_df is None:
            raise ValueError("Could not find S&P 500 companies table in Wikipedia")

        print(f"Found table with {len(sp500_df.columns)} columns: {list(sp500_df.columns)}")

        # Handle different column structures dynamically
        if len(sp500_df.columns) >= 3:
            # Ensure we have at least Symbol, Security, GICS_Sector
            sp500_df = sp500_df.rename(columns={
                sp500_df.columns[0]: 'Symbol',
                sp500_df.columns[1]: 'Security',
                sp500_df.columns[2]: 'GICS_Sector'
            })
        else:
            raise ValueError(f"Wikipedia table structure unexpected: {list(sp500_df.columns)}")

        print(f"Found {len(sp500_df)} S&P 500 companies")

        companies = []
        processed_count = 0
        skipped_sector_count = 0

        for _, row in sp500_df.iterrows():
            ticker = row['Symbol']
            name = row['Security']
            gics_sector = row['GICS_Sector']

            # Map to allowed sectors
            mapped_sector = map_sector(gics_sector)

            if mapped_sector is None:
                print(f"Skipping {ticker} - sector '{gics_sector}' not in allowed sectors")
                skipped_sector_count += 1
                continue

            if processed_count >= 100:  # Limit to top 100
                break

            print(f"Processing {ticker} ({name}) - {mapped_sector}...")

            try:
                # Get additional data from yfinance
                stock = yf.Ticker(ticker)
                info = stock.info

                # Get company summary/description
                summary = info.get('longBusinessSummary', '')
                if not summary:
                    summary = info.get('description', f"{name} is a {mapped_sector} company listed in the S&P 500 index.")

                # Limit summary length for database
                if len(summary) > 500:
                    summary = summary[:500] + "..."

                # Get market cap to sort by size later
                market_cap = info.get('marketCap', 0)

                companies.append({
                    'name': name,
                    'ticker': ticker,
                    'summary': summary,
                    'sector': [mapped_sector],  # Store as array as per Entity model
                    'market_cap': market_cap
                })

                processed_count += 1

            except Exception as e:
                print(f"Error fetching data for {ticker}: {e}")
                # Add basic info even if yfinance fails
                companies.append({
                    'name': name,
                    'ticker': ticker,
                    'summary': f"{name} is a {mapped_sector} company listed in the S&P 500 index.",
                    'sector': [mapped_sector],
                    'market_cap': 0
                })
                processed_count += 1
                continue

        print(f"Skipped {skipped_sector_count} companies due to sector restrictions")

        # Sort by market cap (largest first) and take top 100
        companies.sort(key=lambda x: x['market_cap'], reverse=True)
        top_100 = companies[:100]

        print(f"Successfully processed {len(top_100)} companies from allowed sectors")
        return top_100

    except Exception as e:
        print(f"Error fetching S&P 500 companies: {e}")
        # Fallback to manual list of major S&P 500 companies
        return get_fallback_sp500_companies()


def get_fallback_sp500_companies():
    """
    Fallback list of major S&P 500 companies in case API fetching fails
    Only includes companies from allowed sectors
    """
    print("Using fallback list of major S&P 500 companies...")

    fallback_companies = [
        {'ticker': 'AAPL', 'name': 'Apple Inc.', 'sector': ['Information Technology']},
        {'ticker': 'MSFT', 'name': 'Microsoft Corporation', 'sector': ['Information Technology']},
        {'ticker': 'GOOGL', 'name': 'Alphabet Inc. Class A', 'sector': ['Communication Services']},
        {'ticker': 'AMZN', 'name': 'Amazon.com Inc.', 'sector': ['Consumer Discretionary']},
        {'ticker': 'NVDA', 'name': 'NVIDIA Corporation', 'sector': ['Information Technology']},
        {'ticker': 'TSLA', 'name': 'Tesla Inc.', 'sector': ['Consumer Discretionary']},
        {'ticker': 'META', 'name': 'Meta Platforms Inc.', 'sector': ['Communication Services']},
        {'ticker': 'BRK.B', 'name': 'Berkshire Hathaway Inc. Class B', 'sector': ['Financials']},
        {'ticker': 'V', 'name': 'Visa Inc.', 'sector': ['Financials']},
        {'ticker': 'JPM', 'name': 'JPMorgan Chase & Co.', 'sector': ['Financials']},
        {'ticker': 'JNJ', 'name': 'Johnson & Johnson', 'sector': ['Health Care']},
        {'ticker': 'WMT', 'name': 'Walmart Inc.', 'sector': ['Consumer Staples']},
        {'ticker': 'PG', 'name': 'Procter & Gamble Company', 'sector': ['Consumer Staples']},
        {'ticker': 'UNH', 'name': 'UnitedHealth Group Incorporated', 'sector': ['Health Care']},
        {'ticker': 'HD', 'name': 'Home Depot Inc.', 'sector': ['Consumer Discretionary']},
        {'ticker': 'MA', 'name': 'Mastercard Incorporated', 'sector': ['Financials']},
        {'ticker': 'BAC', 'name': 'Bank of America Corporation', 'sector': ['Financials']},
        {'ticker': 'XOM', 'name': 'Exxon Mobil Corporation', 'sector': ['Energy']},
        {'ticker': 'LLY', 'name': 'Eli Lilly and Company', 'sector': ['Health Care']},
        {'ticker': 'ABBV', 'name': 'AbbVie Inc.', 'sector': ['Health Care']},
    ]

    # Add basic summaries using yfinance if available
    companies = []
    for company_data in fallback_companies:
        try:
            ticker = company_data['ticker']
            stock = yf.Ticker(ticker)
            info = stock.info

            summary = info.get('longBusinessSummary', '')
            if not summary:
                summary = f"{company_data['name']} is a {company_data['sector'][0]} company."

            if len(summary) > 500:
                summary = summary[:500] + "..."

            companies.append({
                'name': company_data['name'],
                'ticker': ticker,
                'summary': summary,
                'sector': company_data['sector'],
                'market_cap': info.get('marketCap', 0)
            })

        except Exception as e:
            print(f"Error fetching fallback data for {ticker}: {e}")
            companies.append({
                'name': company_data['name'],
                'ticker': company_data['ticker'],
                'summary': f"{company_data['name']} is a {company_data['sector'][0]} company.",
                'sector': company_data['sector'],
                'market_cap': 0
            })

    return companies


def seed_sp500_entities():
    """
    Main function to seed S&P 500 entities into the database
    """
    app = create_app()

    with app.app_context():
        print(f"S&P 500 Entities Seeder")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Allowed sectors: {', '.join(ALLOWED_SECTORS)}")
        print("=" * 60)

        # Get S&P 500 companies data
        companies = get_sp500_companies()

        if not companies:
            print("❌ Failed to fetch S&P 500 companies data")
            return

        print(f"\n📊 Ready to seed {len(companies)} S&P 500 companies")

        # Check for existing entities to avoid duplicates
        existing_tickers = set()
        existing_entities = Entity.query.filter(Entity.ticker.isnot(None)).all()
        for entity in existing_entities:
            existing_tickers.add(entity.ticker)

        print(f"Found {len(existing_tickers)} existing entities with tickers")

        # Filter out companies that already exist
        new_companies = []
        skipped_companies = []

        for company in companies:
            if company['ticker'] in existing_tickers:
                skipped_companies.append(company)
            else:
                new_companies.append(company)

        print(f"📈 {len(new_companies)} new companies to add")
        print(f"⏭️  {len(skipped_companies)} companies already exist (skipped)")

        if not new_companies:
            print("\n✅ All S&P 500 companies already exist in the database")
            return

        # Show sector distribution
        sector_counts = {}
        for company in new_companies:
            sector = company['sector'][0] if company['sector'] else 'Unknown'
            sector_counts[sector] = sector_counts.get(sector, 0) + 1

        print(f"\n📊 Sector distribution:")
        for sector, count in sorted(sector_counts.items()):
            print(f"  {sector}: {count} companies")

        # Insert new companies
        print(f"\n🚀 Starting insertion of {len(new_companies)} companies...")

        try:
            success_count = 0

            for company in new_companies:
                try:
                    entity = Entity(
                        name=company['name'],
                        ticker=company['ticker'],
                        summary=company['summary'],
                        sector=company['sector'],
                        # Sentiment fields left NULL - will be calculated by EntitySentimentAggregator
                        sentiment_score=None,
                        finbert_score=None,
                        gemini_score=None,
                        open_ai_score=None,
                        confidence_score=None,
                        time_decay=None,
                        simple_average=None,
                        classification=None,
                        asset_type='stock'  # All S&P 500 companies are stocks
                    )

                    db.session.add(entity)
                    success_count += 1
                    sector_name = company['sector'][0] if company['sector'] else 'Unknown'
                    print(f"✅ Added {company['ticker']} - {company['name']} ({sector_name})")

                except Exception as e:
                    print(f"❌ Failed to add {company['ticker']} - {company['name']}: {e}")
                    continue

            # Commit all changes
            db.session.commit()

            print(f"\n🎉 SUCCESS!")
            print(f"Successfully added {success_count} S&P 500 companies to the database")
            print(f"Skipped {len(skipped_companies)} existing companies")

            if skipped_companies:
                print(f"\nSkipped existing companies:")
                for company in skipped_companies[:10]:  # Show first 10
                    print(f"  - {company['ticker']} ({company['name']})")
                if len(skipped_companies) > 10:
                    print(f"  ... and {len(skipped_companies) - 10} more")

            print(f"\n📝 Note: Sentiment scores (confidence_score, time_decay, simple_average)")
            print(f"    will be calculated by the Entity Sentiment Job when it runs.")

        except Exception as e:
            db.session.rollback()
            print(f"\n💥 Error during insertion: {e}")
            print("Database changes have been rolled back")


if __name__ == "__main__":
    seed_sp500_entities()