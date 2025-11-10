from flask import Blueprint, jsonify
from sqlalchemy import func
from app.models.user import User
from app.models.active_learning import UserStats, UserVote, AggregatedLabel
from app import db

analytics_bp = Blueprint("analytics", __name__, url_prefix="/api/analytics")

@analytics_bp.route("/user-statistics", methods=["GET"])
def get_user_statistics():
    """Get statistics for all users including voting behavior and reliability"""
    try:
        # Query user stats joined with user information
        user_data = (
            db.session.query(
                User.id,
                User.email,
                User.first_name,
                User.last_name,
                UserStats.total_votes,
                UserStats.last_active
            )
            .outerjoin(UserStats, User.id == UserStats.user_id)
            .all()
        )

        statistics = []
        for user in user_data:
            # Calculate agreement with majority
            user_votes = (
                db.session.query(UserVote)
                .filter(UserVote.user_id == user.id)
                .all()
            )
            
            agreement_count = 0
            total_comparable = 0
            
            for vote in user_votes:
                aggregated = (
                    db.session.query(AggregatedLabel)
                    .filter(AggregatedLabel.queue_item_id == vote.queue_item_id)
                    .first()
                )
                
                if aggregated:
                    total_comparable += 1
                    if vote.vote.value == aggregated.final_label.value:
                        agreement_count += 1
            
            agreement_rate = agreement_count / total_comparable if total_comparable > 0 else 0
            
            statistics.append({
                "user_id": str(user.id),
                "email": user.email,
                "name": f"{user.first_name} {user.last_name}",
                "total_votes": user.total_votes or 0,
                "last_active": user.last_active.isoformat() if user.last_active else None,
                "agreement_with_majority": agreement_rate
            })
        
        return jsonify(statistics), 200
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500
