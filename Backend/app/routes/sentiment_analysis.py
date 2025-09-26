from flask import Blueprint, request
from app.services.sentiment_analysis import get_sentiment
from app.services.sentiment_history_services import create_sentiment_history
from app.services.entities_service import update_entity_sentiment
from app.services.news_services import news_by_ticker
from app.utils.helpers import format_response
from app.models.entity import Entity

sentiment_bp = Blueprint("sentiment", __name__)


@sentiment_bp.route("/analyze", methods=["POST"])
def analyze():
    text = request.get_json().get("text", "")
    result = get_sentiment(text, False)
    return format_response(result, "Sentiment analysis successful", 200)


@sentiment_bp.route("/entity", methods=["POST"])
def analyze_entity():
    # Import locally to avoid circular imports
    from app.services.entity_sentiment_analyzer import EntitySentimentAnalyzer

    # get entity name
    db_entities = Entity.query.all()

    final_result = []

    for entity in db_entities:
        # get news articles
        entity_name = entity.name
        id = entity.id
        ticker = entity.ticker

        # retrieve top 10 news articles for each entity from the database
        articles = []

        news_list = news_by_ticker(
            ticker, page=1, per_page=10, sort_order="desc", filter_time="all"
        )

        if not news_list:
            continue

        if isinstance(news_list, dict):
            news_details = news_list["news"]

        else:
            news_details = news_list

        # news_details = news_list["news"]

        for news in news_details:
            articles.append(
                {
                    "text": news["summary"],
                    "metadata": {
                        "source": news["publisher"],
                        "date": news["published_date"],
                        "title": news["title"],
                    },
                }
            )

        weights = {
            "confidence": True,
            "time_decay": True,
            "decay_factor": 0.9,
            "preferred_method": "combined_weighted",
        }

        # Initialize entity analyzer
        entity_analyzer = EntitySentimentAnalyzer()

        # Generate unified sentiment
        result = entity_analyzer.generate_unified_sentiment_scores(
            entity_name, articles, weights
        )

        print(f"Sentiment analysis for entity {entity_name}: {result}")

        # convert np.float64 to standard Python float
        sentiment_score = float(result["unified_score"])
        confidence_score = float(
            result["aggregation_methods"]["confidence_weighted"]["score"]
        )
        time_decay_score = float(
            result["aggregation_methods"]["time_weighted"]["score"]
        )
        simple_average_score = float(
            result["aggregation_methods"]["simple_average"]["score"]
        )
        classification = result["classification"]

        # Save to database
        sentiment_history = create_sentiment_history(
            entity_id=id, sentiment_score=sentiment_score
        )

        print(
            f"Sentiment history created for entity {entity_name}: {sentiment_history}"
        )

        # Update entity sentiment
        update = update_entity_sentiment(
            ticker=ticker,
            sentiment_score=sentiment_score,
            confidence_score=confidence_score,
            time_decay_score=time_decay_score,
            simple_average_score=simple_average_score,
            classification=classification,
        )

        if update:
            # Append to final result
            final_result.append(
                {
                    "entity_id": id,
                    "entity_name": entity_name,
                    "sentiment_score": sentiment_score,
                    "confidence_score": confidence_score,
                    "time_decay_score": time_decay_score,
                    "simple_average_score": simple_average_score,
                    "classification": classification,
                }
            )

    return format_response(
        final_result, "Sentiment analysis for entities successful", 200
    )
