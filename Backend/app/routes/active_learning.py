import uuid
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from datetime import datetime
import logging
import json

from app.models.active_learning import LabelingQueue, UserVote, AggregatedLabel, UserStats, QueueStatus, SentimentVote, ModelRun, FinalSentiment
from app.models.user import User 
from app.utils.helpers import format_response
from app import db 

logger = logging.getLogger(__name__)

active_learning_bp = Blueprint("active_learning", __name__)

MIN_VOTES_FOR_FINALIZATION = 3

@active_learning_bp.route("/enqueue", methods=["POST"])
def enqueue_item():
    """Add single item to labeling queue"""
    data = request.get_json()

    try:
        queue_item = LabelingQueue(
            news_id=data.get('news_id'),
            text=data.get('text'),
            finbert_score=data.get('finbert_score'),
            llm_score=data.get('llm_score'),
            model_type=data.get('model_type'),
            disagreement_score=data.get('disagreement_score'),
            uncertainty_score=data.get('uncertainty_score'),
            sampling_reason=data.get('sampling_reason'),
            priority=data.get('priority'),
            status=QueueStatus.PENDING,
            features_json=data.get('features_json'),
            feature_names_json=data.get('feature_names_json')
        )
        
        db.session.add(queue_item)
        db.session.commit()
        
        result = {
            'id': queue_item.id,
            'news_id': queue_item.news_id,
            'text': queue_item.text,
            'finbert_score': queue_item.finbert_score,
            'llm_score': queue_item.llm_score,
            'model_type': queue_item.model_type,
            'disagreement_score': queue_item.disagreement_score,
            'uncertainty_score': queue_item.uncertainty_score,
            'sampling_reason': queue_item.sampling_reason,
            'priority': queue_item.priority,
            'status': queue_item.status.value,
            'created_at': queue_item.created_at.isoformat()
        }
        
        return format_response(result, "Item enqueued successfully", 201)
        
    except Exception as e:
        db.session.rollback()
        return format_response(None, f"Failed to enqueue item: {str(e)}", 500)

@active_learning_bp.route("/enqueue/batch", methods=["POST"])
def enqueue_batch():
    """Add multiple items to labeling queue"""
    data = request.get_json()
    items = data.get('items', [])
    
    try:
        queue_items = []
        
        for item_data in items:
            queue_item = LabelingQueue(
                news_id=item_data.get('news_id'),
                text=item_data.get('text'),
                finbert_score=item_data.get('finbert_score'),
                llm_score=item_data.get('llm_score'),
                model_type=item_data.get('model_type'),
                disagreement_score=item_data.get('disagreement_score'),
                uncertainty_score=item_data.get('uncertainty_score'),
                sampling_reason=item_data.get('sampling_reason'),
                priority=item_data.get('priority'),
                status=QueueStatus.PENDING,
                features_json=item_data.get('features_json'),
                feature_names_json=item_data.get('feature_names_json')
            )
            queue_items.append(queue_item)
        
        db.session.add_all(queue_items)
        db.session.commit()
        
        results = []
        for item in queue_items:
            results.append({
                'id': item.id,
                'news_id': item.news_id,
                'text': item.text,
                'priority': item.priority,
                'status': item.status.value,
                'created_at': item.created_at.isoformat()
            })
            
        return format_response(results, "Items enqueued successfully", 201)
        
    except Exception as e:
        db.session.rollback()
        return format_response(None, f"Failed to enqueue batch: {str(e)}", 500)

@active_learning_bp.route("/pending", methods=["GET"])
def get_pending_items():
    """Get pending items for annotation, sorted by priority"""
    limit = request.args.get('limit', 10, type=int)
    priority_filter = request.args.get('priority_filter', type=int)
    
    # Validate limit
    if limit < 1 or limit > 100:
        return format_response(None, "Limit must be between 1 and 100", 400)
    
    try:
        query = LabelingQueue.query.filter(LabelingQueue.status == QueueStatus.PENDING)
        
        if priority_filter and 1 <= priority_filter <= 5:
            query = query.filter(LabelingQueue.priority == priority_filter)
        
        # Order by priority (1=highest), then by disagreement_score (highest first)
        pending_items = query.order_by(
            LabelingQueue.priority.asc(),
            LabelingQueue.disagreement_score.desc(),
            LabelingQueue.created_at.asc()
        ).limit(limit).all()
        
        results = []
        for item in pending_items:
            vote_count = UserVote.query.filter(UserVote.queue_item_id == item.id).count()
            results.append({
                'id': item.id,
                'news_id': item.news_id,
                'text': item.text,
                'finbert_score': item.finbert_score,
                'llm_score': item.llm_score,
                'model_type': item.model_type,
                'disagreement_score': item.disagreement_score,
                'uncertainty_score': item.uncertainty_score,
                'sampling_reason': item.sampling_reason,
                'priority': item.priority,
                'status': item.status.value,
                'created_at': item.created_at.isoformat(),
                'vote_count': vote_count
            })
        
        return format_response(results, "Pending items fetched successfully", 200)
        
    except Exception as e:
        return format_response(None, f"Failed to fetch pending items: {str(e)}", 500)

@active_learning_bp.route("/vote", methods=["POST"])
@jwt_required()
def submit_vote():
    """Submit a user vote - handles BOTH queued and non-queued items"""
    try:
        data = request.get_json()
        
        if not data:
            return format_response(None, "No data provided", 400)
        
        current_user_id = get_jwt_identity()
        if not current_user_id:
            return format_response(None, "No user identity in token", 401)
            
        current_user = User.query.filter(User.id == uuid.UUID(current_user_id)).first()

        if not current_user:
            return format_response(None, "User not found", 404)

        queue_item_id = data.get('queue_item_id')  # Can be null for non-queued items
        vote_value = data.get('vote')
        session_info = data.get('session_info', {})
        
        if not vote_value:
            return format_response(None, "Missing required field: vote", 400)
        
        valid_votes = ['bullish', 'bearish', 'neutral']
        if vote_value not in valid_votes:
            return format_response(None, f"Invalid vote. Must be one of: {valid_votes}", 400)
        
        # Handle queued items (high priority cases)
        if queue_item_id:
            queue_item = LabelingQueue.query.filter(LabelingQueue.id == queue_item_id).first()
            if not queue_item:
                return format_response(None, "Queue item not found", 404)
            
            if queue_item.status != QueueStatus.PENDING:
                return format_response(None, "Queue item is not available for voting", 400)
            
            # Check if user already voted on this queued item
            existing_vote = UserVote.query.filter(
                UserVote.queue_item_id == queue_item_id,
                UserVote.user_id == current_user.id
            ).first()
            
            if existing_vote:
                return format_response(None, "User has already voted on this item", 400)
        
        # For non-queued items, create a simple queue entry for tracking
        else:
            news_id = session_info.get('news_id')
            if news_id:
                # Check if we already have a queue item for this news article + user combination
                existing_user_vote = db.session.query(UserVote).join(LabelingQueue).filter(
                    LabelingQueue.news_id == str(news_id),
                    UserVote.user_id == current_user.id,
                    LabelingQueue.model_type == "user_feedback"
                ).first()
                
                if existing_user_vote:
                    return format_response(None, "You have already provided feedback for this news article", 400)
                
                # Create a simple queue entry for non-priority feedback
                queue_item = LabelingQueue(
                    news_id=str(news_id),  # Ensure it's stored as string
                    text="General user feedback",  # Placeholder
                    finbert_score=0.0,  # Placeholder
                    llm_score=0.0,     # Placeholder
                    model_type="user_feedback",
                    disagreement_score=0.0,
                    uncertainty_score=0.0,
                    sampling_reason="User provided feedback",
                    priority=5,  # Lowest priority
                    status=QueueStatus.PENDING
                )
                db.session.add(queue_item)
                db.session.flush()  # Get ID
                queue_item_id = queue_item.id
            else:
                return format_response(None, "News ID is required for feedback", 400)
        
        # ensure enum uses lowercase string values defined in SentimentVote
        vote = UserVote(
            queue_item_id=queue_item_id,
            user_id=current_user.id,
            vote=SentimentVote(vote_value.lower()),
            session_info=session_info,
            news_id=session_info.get('news_id')  # Extract and store
        )
        
        db.session.add(vote)
        
        # Update user stats
        user_stats = UserStats.query.filter(UserStats.user_id == current_user.id).first()
        if not user_stats:
            user_stats = UserStats(user_id=current_user.id, total_votes=1)
            db.session.add(user_stats)
        else:
            user_stats.total_votes += 1
            user_stats.last_active = datetime.now()
        
        db.session.commit()
        
        # Auto-finalize single-vote items (non-priority)
        if not data.get('queue_item_id'): 
            _try_finalize_item(queue_item_id, force=True)
        else:
            # Check if high-priority item should be finalized
            vote_count = UserVote.query.filter(UserVote.queue_item_id == queue_item_id).count()
            if vote_count >= MIN_VOTES_FOR_FINALIZATION:
                _try_finalize_item(queue_item_id)
        
        result = {
            'id': vote.id,
            'queue_item_id': vote.queue_item_id,
            'user_id': str(vote.user_id),
            'vote': vote.vote.value,
            'vote_time': vote.vote_time.isoformat(),
            'was_high_priority': bool(data.get('queue_item_id'))
        }
        
        return format_response(result, "Vote submitted successfully", 201)
        
    except ValueError as e:
        logger.error(f"Value error in submit_vote: {str(e)}")
        db.session.rollback()
        return format_response(None, f"Invalid data format: {str(e)}", 400)
    except Exception as e:
        logger.error(f"Unexpected error in submit_vote: {str(e)}")
        db.session.rollback()
        return format_response(None, f"Failed to submit vote: {str(e)}", 500)

@active_learning_bp.route("/aggregate/<int:queue_item_id>", methods=["GET"])
def get_aggregated_result(queue_item_id):
    """Get aggregated results for a queue item"""
    try:
        aggregated = AggregatedLabel.query.filter(AggregatedLabel.queue_item_id == queue_item_id).first()
        
        if not aggregated:
            return format_response(None, "Aggregated result not found", 404)
        
        result = {
            'id': aggregated.id,
            'queue_item_id': aggregated.queue_item_id,
            'final_label': aggregated.final_label.value,
            'vote_count': aggregated.vote_count,
            'agreement_rate': aggregated.agreement_rate,
            'aggregation_method': aggregated.aggregation_method,
            'finalized_at': aggregated.finalized_at.isoformat()
        }
        
        return format_response(result, "Aggregated result fetched successfully", 200)
        
    except Exception as e:
        return format_response(None, f"Failed to fetch aggregated result: {str(e)}", 500)

@active_learning_bp.route("/finalize/<int:queue_item_id>", methods=["POST"])
def finalize_item(queue_item_id):
    """Manually finalize labeling for an item"""
    try:
        result = _try_finalize_item(queue_item_id, force=True)
        
        if not result:
            return format_response(None, "Cannot finalize item - insufficient votes or already finalized", 400)
        
        response_data = {
            'id': result.id,
            'queue_item_id': result.queue_item_id,
            'final_label': result.final_label.value,
            'vote_count': result.vote_count,
            'agreement_rate': result.agreement_rate,
            'aggregation_method': result.aggregation_method,
            'finalized_at': result.finalized_at.isoformat()
        }
        
        return format_response(response_data, "Item finalized successfully", 200)
        
    except Exception as e:
        return format_response(None, f"Failed to finalize item: {str(e)}", 500)

@active_learning_bp.route("/stats", methods=["GET"])
def get_system_stats():
    """Get system statistics"""
    try:
        pending_count = LabelingQueue.query.filter(LabelingQueue.status == QueueStatus.PENDING).count()
        completed_count = LabelingQueue.query.filter(LabelingQueue.status == QueueStatus.COMPLETED).count()
        total_votes = UserVote.query.count()
        unique_users = db.session.query(func.count(func.distinct(UserVote.user_id))).scalar()
        
        # Average agreement rate for completed items
        avg_agreement = db.session.query(func.avg(AggregatedLabel.agreement_rate)).scalar() or 0.0
        
        # High priority pending items
        high_priority_pending = LabelingQueue.query.filter(
            LabelingQueue.status == QueueStatus.PENDING,
            LabelingQueue.priority <= 2
        ).count()
        
        result = {
            'pending_count': pending_count,
            'completed_count': completed_count,
            'total_votes': total_votes,
            'unique_users': unique_users,
            'avg_agreement_rate': float(avg_agreement),
            'high_priority_pending': high_priority_pending
        }
        
        return format_response(result, "System stats fetched successfully", 200)
        
    except Exception as e:
        return format_response(None, f"Failed to fetch system stats: {str(e)}", 500)

@active_learning_bp.route("/user/<user_id>/stats", methods=["GET"])
@jwt_required()
def get_user_stats(user_id):
    """Get user reliability statistics"""
    try:
        # Convert user_id string to UUID
        user_uuid = uuid.UUID(user_id)
        user_stats = UserStats.query.filter(UserStats.user_id == user_uuid).first()
        
        if not user_stats:
            # Create default stats if user hasn't voted yet
            result = {
                'user_id': user_id,
                'total_votes': 0,
                'gold_standard_correct': 0,
                'gold_standard_total': 0,
                'reliability_score': 1.0,
                'last_active': None
            }
        else:
            result = {
                'user_id': str(user_stats.user_id),
                'total_votes': user_stats.total_votes,
                'gold_standard_correct': user_stats.gold_standard_correct,
                'gold_standard_total': user_stats.gold_standard_total,
                'reliability_score': user_stats.reliability_score,
                'last_active': user_stats.last_active.isoformat() if user_stats.last_active else None
            }
        
        return format_response(result, "User stats fetched successfully", 200)
        
    except ValueError:
        return format_response(None, "Invalid user ID format", 400)
    except Exception as e:
        return format_response(None, f"Failed to fetch user stats: {str(e)}", 500)

@active_learning_bp.route("/users/statistics", methods=["GET"])
@jwt_required()
def get_all_user_statistics():
    """Get statistics for all users with voting activity"""
    try:
        # Get all users who have votes with aggregated statistics
        user_stats_query = db.session.query(
            UserStats.user_id,
            UserStats.total_votes,
            UserStats.gold_standard_correct,
            UserStats.gold_standard_total,
            UserStats.reliability_score,
            UserStats.last_active,
            User.email,
            User.first_name,
            User.last_name
        ).join(User, UserStats.user_id == User.id).all()
        
        results = []
        for stat in user_stats_query:
            # Calculate agreement with majority (simplified - would need more complex logic)
            agreement_rate = 0.85  # Placeholder - need to implement actual calculation
            
            user_data = {
                'user_id': str(stat.user_id),
                'email': stat.email,
                'name': f"{stat.first_name} {stat.last_name}",
                'total_votes': stat.total_votes,
                'gold_standard_correct': stat.gold_standard_correct,
                'gold_standard_total': stat.gold_standard_total,
                'reliability_score': stat.reliability_score,
                'last_active': stat.last_active.isoformat() if stat.last_active else None,
                'agreement_with_majority': agreement_rate
            }
            results.append(user_data)
        
        return format_response(results, "User statistics fetched successfully", 200)
        
    except Exception as e:
        return format_response(None, f"Failed to fetch user statistics: {str(e)}", 500)

@active_learning_bp.route("/analytics/disagreement-patterns", methods=["GET"])
def get_disagreement_patterns():
    """Get analytics on disagreement patterns and model performance"""
    try:
        # Analyze disagreement patterns
        high_disagreement_items = db.session.query(LabelingQueue).filter(
            LabelingQueue.disagreement_score > 0.7
        ).all()
        
        patterns = {
            'total_high_disagreement': len(high_disagreement_items),
            'common_reasons': {},
            'model_performance': {
                'avg_finbert_confidence': 0.75,  # Calculate from actual data
                'avg_llm_confidence': 0.68,     # Calculate from actual data
                'frequent_disagreement_topics': ['earnings', 'guidance', 'market_outlook']
            }
        }
        
        # Count sampling reasons
        for item in high_disagreement_items:
            reason = item.sampling_reason
            patterns['common_reasons'][reason] = patterns['common_reasons'].get(reason, 0) + 1
        
        return format_response(patterns, "Disagreement patterns analyzed successfully", 200)
        
    except Exception as e:
        return format_response(None, f"Failed to analyze patterns: {str(e)}", 500)

@active_learning_bp.route("/votes/news/<news_id>", methods=["GET"])
def get_votes_by_news_id(news_id):
    """Get all votes for a specific news article (for charts)"""
    
    try:
        # Primary attempt: JSON ->> operator (Postgres) to read text value
        votes_with_news_id = UserVote.query.filter(UserVote.news_id == str(news_id)).all()
                
        # If no votes found via JSON operator, perform additional diagnostics / fallback scan
        if not votes_with_news_id:
            # Log counts for visibility
            total_votes = UserVote.query.count()
            
            # Inspect some votes that have session_info to understand structure (limit for safety)
            votes_with_session = UserVote.query.filter(UserVote.session_info.isnot(None)).limit(50).all()
            for i, v in enumerate(votes_with_session[:10]):  # limit verbose output
                try:
                    logger.debug("Sample vote %s session_info: %s", v.id, v.session_info)
                except Exception:
                    logger.debug("Sample vote %s session_info: <unserializable>", v.id)
            
            # Try Python-side scan of session_info for a match (limit to 1000 rows for safety)
            fallback_matches = []
            scanned = 0
            for v in UserVote.query.filter(UserVote.session_info.isnot(None)).limit(1000).all():
                scanned += 1
                si = v.session_info or {}
                # session_info might store news_id as int, str, or nested - handle common cases
                sid = si.get('news_id')
                if sid is None:
                    # try other common key names
                    sid = si.get('id') or si.get('newsId') or si.get('article_id')
                try:
                    if str(sid) == str(news_id):
                        fallback_matches.append(v)
                        continue
                except Exception:
                    pass
                # also check if news_id substring appears anywhere in the serialized session_info
                try:
                    if str(news_id) in json.dumps(si):
                        fallback_matches.append(v)
                except Exception:
                    pass
            if fallback_matches:
                votes_with_news_id = fallback_matches
        
        if not votes_with_news_id:
            queue_items = LabelingQueue.query.filter(LabelingQueue.news_id == str(news_id)).all()
            if queue_items:
                queue_item_ids = [item.id for item in queue_items]
                logger.debug("Queue items (id, news_id): %s", [(q.id, q.news_id, type(q.news_id)) for q in queue_items])
                votes_with_news_id = UserVote.query.filter(UserVote.queue_item_id.in_(queue_item_ids)).all()
                logger.info(f"Found {len(votes_with_news_id)} votes via queue items")
        
        vote_data = []
        for vote in votes_with_news_id:
            vote_data.append({
                'id': vote.id,
                'vote': vote.vote.value,  # 'bullish', 'bearish', 'neutral'
                'vote_time': vote.vote_time.isoformat(),
                'user_id': str(vote.user_id),
                'session_info': vote.session_info  # include for debugging (frontend can ignore)
            })
        
        return format_response(vote_data, "Votes fetched successfully", 200)
        
    except Exception as e:
        # Return empty array instead of error to prevent frontend crashes
        return format_response([], "No votes found", 200)

def _try_finalize_item(queue_item_id, force=False):
    """Internal function to finalize an item if conditions are met"""
    try:
        # Check if already finalized
        existing = AggregatedLabel.query.filter(AggregatedLabel.queue_item_id == queue_item_id).first()
        if existing:
            return existing

        # Get all votes for this item
        votes = UserVote.query.filter(UserVote.queue_item_id == queue_item_id).all()
        if len(votes) < MIN_VOTES_FOR_FINALIZATION and not force:
            return None
        if len(votes) == 0:
            return None

        # Calculate majority vote
        vote_counts = {}
        for vote in votes:
            vote_value = vote.vote.value.lower() 
            vote_counts[vote_value] = vote_counts.get(vote_value, 0) + 1

        # Get majority label
        final_label = max(vote_counts.keys(), key=lambda x: vote_counts[x])
        majority_count = vote_counts[final_label]
        agreement_rate = majority_count / len(votes)

        # Create aggregated result 
        # FinalSentiment enum values are lowercase ('bullish','bearish','neutral')
        aggregated = AggregatedLabel(
            queue_item_id=queue_item_id,
            final_label=FinalSentiment(final_label.lower()), 
            vote_count=len(votes),
            agreement_rate=agreement_rate,
            aggregation_method="majority"
        )

        db.session.add(aggregated)

        # Update queue item status
        queue_item = LabelingQueue.query.filter(LabelingQueue.id == queue_item_id).first()
        if queue_item:
            queue_item.status = QueueStatus.COMPLETED

        db.session.commit()

        return aggregated

    except Exception as e:
        logger.error(f"Error in _try_finalize_item: {str(e)}")
        db.session.rollback()
        return None

# TODO: Implement CSV export for retraining pipeline
# Below is for future sprints retraining purposes
# @active_learning_bp.route("/export", methods=["GET"])
# def export_labeled_data():
#     """Export labeled data as CSV for training"""
#     try:
#         completed_count = LabelingQueue.query.filter(LabelingQueue.status == QueueStatus.COMPLETED).count()
        
#         result = {
#             'total_samples': completed_count,
#             'export_url': '/labeling/download/latest.csv',  # Implement actual file generation
#             'created_at': datetime.now().isoformat()
#         }
        
#         return format_response(result, "Export data prepared successfully", 200)
        
#     except Exception as e:
#         return format_response(None, f"Failed to prepare export: {str(e)}", 500)

# TODO: Implement for retraining pipeline
# @active_learning_bp.route("/retrain-needed", methods=["POST"])
# def check_retrain_needed():
#     """Check if enough new labels exist to trigger retraining"""
#     data = request.get_json() or {}
#     threshold = data.get('threshold', 100)
    
#     try:        
#         # Get count of completed items since last model run
#         last_model_run = db.session.query(func.max(ModelRun.created_at)).scalar()
        
#         if last_model_run:
#             new_labels = db.session.query(func.count(AggregatedLabel.id)).filter(
#                 AggregatedLabel.finalized_at > last_model_run
#             ).scalar()
#         else:
#             new_labels = AggregatedLabel.query.count()
        
#         result = {
#             'retrain_needed': new_labels >= threshold,
#             'new_labels_count': new_labels,
#             'threshold': threshold,
#             'last_model_run': last_model_run.isoformat() if last_model_run else None
#         }
        
#         return format_response(result, "Retrain status checked successfully", 200)
        
#     except Exception as e:
#         return format_response(None, f"Failed to check retrain status: {str(e)}", 500)
