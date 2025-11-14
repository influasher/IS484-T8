import uuid
from flask import Blueprint, request
from flask_jwt_extended import jwt_required, get_jwt_identity
from sqlalchemy import func
from datetime import datetime, timedelta
import logging
import json
import csv
import io
from flask import send_file
import subprocess
import threading
import os

from app.models.active_learning import LabelingQueue, UserVote, AggregatedLabel, UserStats, QueueStatus, SentimentVote, ModelRun, FinalSentiment
from app.models.user import User 
from app.utils.helpers import format_response
from app import db 

logger = logging.getLogger(__name__)

active_learning_bp = Blueprint("active_learning", __name__)

MIN_VOTES_FOR_FINALIZATION = 3

def to_uuid_safe(value):
    """Convert to UUID or return None, without throwing."""
    if not value:
        return None
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except ValueError:
        return None

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
            
        user_uuid = to_uuid_safe(current_user_id)
        if not user_uuid:
            return format_response(None, "Invalid user id in token", 400)

        current_user = User.query.filter(User.id == user_uuid).first()

        if not current_user:
            return format_response(None, "User not found", 404)

        queue_item_id = data.get('queue_item_id')
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
            
            existing_vote = UserVote.query.filter(
                UserVote.queue_item_id == queue_item_id,
                UserVote.user_id == current_user.id
            ).first()
            
            if existing_vote:
                return format_response(None, "User has already voted on this item", 400)
        
        # For non-queued items, fetch from News and populate fields
        else:
            news_id = session_info.get('news_id')
            if news_id:
                from app.models.news import News
                
                news_uuid = to_uuid_safe(news_id)
                if not news_uuid:
                    return format_response(None, "Invalid news ID format", 400)
                news_article = News.query.filter_by(id=news_uuid).first()    
                            
                if not news_article:
                    return format_response(None, "News article not found", 404)
                
                # Check for duplicate vote - use string representation for comparison
                existing_user_vote = db.session.query(UserVote).join(LabelingQueue).filter(
                    LabelingQueue.news_id == str(news_id),
                    UserVote.user_id == current_user.id,
                    LabelingQueue.model_type == "user_feedback"
                ).first()
                
                if existing_user_vote:
                    return format_response(None, "You have already provided feedback for this news article", 400)
                
                # Rebuild features from News data
                finbert_score = float(news_article.finbert_score or 0.0)
                llm_score = float(news_article.second_model_score or 0.0)
                
                # Reconstruct model results for feature building
                finbert_result = {
                    'numerical_score': finbert_score / 100.0,  # Scale back to -1 to 1
                    'classification': 'positive' if finbert_score > 10 else ('negative' if finbert_score < -10 else 'neutral'),
                    'detailed_scores': {
                        'positive': max(0, finbert_score / 100.0),
                        'negative': max(0, -finbert_score / 100.0),
                        'neutral': 1.0 - abs(finbert_score / 100.0)
                    }
                }
                
                llm_result = {
                    'numerical_score': llm_score / 100.0,
                    'classification': 'positive' if llm_score > 10 else ('negative' if llm_score < -10 else 'neutral'),
                    'detailed_scores': {
                        'positive': max(0, llm_score / 100.0),
                        'negative': max(0, -llm_score / 100.0),
                        'neutral': 1.0 - abs(llm_score / 100.0)
                    }
                }
                
                # Build features using the same feature builder
                from app.services.sentiment.features import SentimentFeatureBuilder
                
                feature_builder = SentimentFeatureBuilder()
                text = news_article.summary or news_article.title or news_article.content[:500]
                
                features, feature_names = feature_builder.build_single_sample_features(
                    finbert_result, 
                    llm_result, 
                    text,
                    model_type='gemini'  # or detect from news_article if stored
                )
                
                # Convert to serializable format
                features_json = features.tolist() if hasattr(features, 'tolist') else list(features[0])
                feature_names_json = list(feature_names)
                
                queue_item = LabelingQueue(
                    news_id=str(news_id),  # Store as string for consistency
                    text=text,
                    finbert_score=finbert_score,
                    llm_score=llm_score,
                    model_type="user_feedback",
                    disagreement_score=abs(finbert_score - llm_score),
                    uncertainty_score=1.0 - (news_article.confidence or 0.5),
                    sampling_reason="User provided feedback",
                    priority=5,
                    status=QueueStatus.PENDING,
                    
                    # Properly populated features
                    features_json=features_json,
                    feature_names_json=feature_names_json,
                    
                    # Store existing metadata if available
                    finbert_confidence=float(news_article.confidence or 0.5),
                    llm_confidence=float(news_article.confidence or 0.5),
                    both_confident=(news_article.confidence or 0) > 0.6,
                    is_financial_heavy=False,
                    final_combined_score=float(news_article.score or 0.0)
                )
                
                db.session.add(queue_item)
                db.session.flush()
                queue_item_id = queue_item.id
            else:
                return format_response(None, "News ID is required for feedback", 400)
        
        # Create vote
        vote = UserVote(
            queue_item_id=queue_item_id,
            user_id=current_user.id,
            vote=SentimentVote(vote_value.lower()),
            session_info=session_info,
            news_id=str(session_info.get('news_id')) if session_info.get('news_id') else None  # Store as string
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
        
        # Auto-finalize user feedback immediately
        if not data.get('queue_item_id'): 
            _try_finalize_item(queue_item_id, force=True)
        else:
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
        logger.error(f"Unexpected error in submit_vote: {str(e)}", exc_info=True)
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

@active_learning_bp.route("/export", methods=["GET"])
def export_labeled_data():
    """Export labeled data as CSV for meta-classifier training"""
    try:
        # Get all completed labeling items with aggregated labels
        completed_items = db.session.query(
            LabelingQueue.id,
            LabelingQueue.news_id,
            LabelingQueue.text,
            LabelingQueue.finbert_score,
            LabelingQueue.llm_score,
            LabelingQueue.model_type,
            LabelingQueue.disagreement_score,
            LabelingQueue.uncertainty_score,
            LabelingQueue.features_json,
            LabelingQueue.feature_names_json,
            AggregatedLabel.final_label,
            AggregatedLabel.vote_count,
            AggregatedLabel.agreement_rate
        ).join(
            AggregatedLabel,
            LabelingQueue.id == AggregatedLabel.queue_item_id
        ).filter(
            LabelingQueue.status == QueueStatus.COMPLETED
        ).all()
        
        if not completed_items:
            return format_response(None, "No labeled data available for export", 404)
        
        # Create CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Header row
        header = [
            'queue_id', 'news_id', 'finbert_score', 'llm_score', 'model_type',
            'disagreement_score', 'uncertainty_score', 'vote_count', 'agreement_rate',
            'human_label', 'features', 'feature_names'
        ]
        writer.writerow(header)
        
        # Data rows
        for item in completed_items:
            # Convert enum to string
            human_label = item.final_label.value  # 'bullish', 'bearish', 'neutral'
            
            # Serialize features as JSON strings
            features_json = json.dumps(item.features_json) if item.features_json else '[]'
            feature_names_json = json.dumps(item.feature_names_json) if item.feature_names_json else '[]'
            
            writer.writerow([
                item.id,
                item.news_id,
                item.finbert_score,
                item.llm_score,
                item.model_type,
                item.disagreement_score,
                item.uncertainty_score,
                item.vote_count,
                item.agreement_rate,
                human_label,
                features_json,
                feature_names_json
            ])
        
        # Prepare file for download
        output.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"labeled_data_{timestamp}.csv"
        
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=filename
        )
        
    except Exception as e:
        logger.error(f"Failed to export labeled data: {str(e)}")
        return format_response(None, f"Failed to export data: {str(e)}", 500)

@active_learning_bp.route("/export/stats", methods=["GET"])
def get_export_stats():
    """Get statistics about available labeled data"""
    try:
        # Count completed items
        total_completed = LabelingQueue.query.filter(
            LabelingQueue.status == QueueStatus.COMPLETED
        ).count()
        
        # Count by label
        label_distribution = db.session.query(
            AggregatedLabel.final_label,
            func.count(AggregatedLabel.id)
        ).group_by(AggregatedLabel.final_label).all()
        
        # Last export time (track via ModelRun table)
        last_model_run = ModelRun.query.order_by(ModelRun.created_at.desc()).first()
        
        # New samples since last training
        if last_model_run:
            new_samples = db.session.query(func.count(AggregatedLabel.id)).filter(
                AggregatedLabel.finalized_at > last_model_run.created_at
            ).scalar()
        else:
            new_samples = total_completed
        
        result = {
            'total_completed': total_completed,
            'label_distribution': {
                label.value: count for label, count in label_distribution
            },
            'new_samples_since_last_training': new_samples,
            'last_training_date': last_model_run.created_at.isoformat() if last_model_run else None,
            'ready_for_retraining': new_samples >= 20  # Threshold
        }
        
        return format_response(result, "Export stats fetched successfully", 200)
        
    except Exception as e:
        return format_response(None, f"Failed to fetch export stats: {str(e)}", 500)

@active_learning_bp.route("/training-history", methods=["GET"])
def get_training_history():
    """Get historical training runs"""
    try:
        # Get all model runs ordered by most recent first
        model_runs = ModelRun.query.order_by(ModelRun.created_at.desc()).all()
        
        results = []
        for run in model_runs:
            results.append({
                'id': run.id,
                'model_version': run.model_version,
                'created_at': run.created_at.isoformat(),
                'training_samples': run.training_samples,
                'performance_metrics': run.performance_metrics,
                'is_active': run.is_active,
                'artifact_path': run.artifact_path
            })
        
        return format_response(results, "Training history fetched successfully", 200)
        
    except Exception as e:
        return format_response(None, f"Failed to fetch training history: {str(e)}", 500)

@active_learning_bp.route("/trigger-retrain", methods=["POST"])
def trigger_retrain():
    """
    Trigger meta-classifier retraining job
    This runs the training script in a background thread
    """
    try:
        # Check if enough data is available - call the function directly to get stats
        total_completed = LabelingQueue.query.filter(
            LabelingQueue.status == QueueStatus.COMPLETED
        ).count()
        
        # Last export time (track via ModelRun table)
        last_model_run = ModelRun.query.order_by(ModelRun.created_at.desc()).first()
        
        # New samples since last training
        if last_model_run:
            new_samples = db.session.query(func.count(AggregatedLabel.id)).filter(
                AggregatedLabel.finalized_at > last_model_run.created_at
            ).scalar()
        else:
            new_samples = total_completed
        
        ready_for_retraining = new_samples >= 20
        
        if not ready_for_retraining:
            return format_response(
                None, 
                f"Not enough labeled data. Need 20+ samples, currently have {new_samples}",
                400
            )
        
        # Path to training script
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '..',
            'jobs',
            'meta_classifier_training.py'
        )
        
        if not os.path.exists(script_path):
            return format_response(None, f"Training script not found at {script_path}", 500)
        
        # Run training in background thread to avoid timeout
        def run_training():
            try:
                logger.info(f"Starting meta-classifier training job: {script_path}")
                result = subprocess.run(
                    ['python', script_path],
                    capture_output=True,
                    text=True,
                    timeout=600  # 10 minute timeout
                )
                
                if result.returncode == 0:
                    logger.info("Training job completed successfully")
                    logger.info(f"Output: {result.stdout}")
                else:
                    logger.error(f"Training job failed with code {result.returncode}")
                    logger.error(f"Error: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                logger.error("Training job timed out after 10 minutes")
            except Exception as e:
                logger.error(f"Error running training job: {str(e)}")
        
        # Start training in background
        training_thread = threading.Thread(target=run_training, daemon=True)
        training_thread.start()
        
        return format_response(
            {'status': 'training_started'},
            "Retraining job started in background. Check server logs for progress.",
            200
        )
        
    except Exception as e:
        logger.error(f"Failed to trigger retraining: {str(e)}")
        return format_response(None, f"Failed to trigger retraining: {str(e)}", 500)

@active_learning_bp.route("/delete-model/<int:model_id>", methods=["POST"])
def delete_model(model_id):
    """
    Delete an old model file and database record
    WARNING: Cannot delete the active model
    """
    try:
        model_run = ModelRun.query.filter_by(id=model_id).first()
        
        if not model_run:
            return format_response(None, "Model not found", 404)
        
        if model_run.is_active:
            return format_response(None, "Cannot delete the active model", 400)
        
        # Delete model file if it exists
        if model_run.artifact_path and os.path.exists(model_run.artifact_path):
            try:
                os.remove(model_run.artifact_path)
                logger.info(f"Deleted model file: {model_run.artifact_path}")
            except Exception as e:
                logger.warning(f"Failed to delete model file: {str(e)}")
        
        # Delete database record
        db.session.delete(model_run)
        db.session.commit()
        
        return format_response(
            {'deleted_model_id': model_id},
            "Model deleted successfully",
            200
        )
        
    except Exception as e:
        db.session.rollback()
        return format_response(None, f"Failed to delete model: {str(e)}", 500)

@active_learning_bp.route("/purge-old-models", methods=["POST"])
def purge_old_models():
    """
    Purge all inactive models older than a specified number of days
    Keeps only the active model and recent inactive models
    """
    data = request.get_json() or {}
    keep_days = data.get('keep_days', 30)  
    
    try:
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        
        # Find old inactive models
        old_models = ModelRun.query.filter(
            ModelRun.is_active == False,
            ModelRun.created_at < cutoff_date
        ).all()
        
        deleted_count = 0
        for model in old_models:
            # Delete model file if it exists
            if model.artifact_path and os.path.exists(model.artifact_path):
                try:
                    os.remove(model.artifact_path)
                    logger.info(f"Deleted model file: {model.artifact_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete model file: {str(e)}")
            
            # Delete database record
            db.session.delete(model)
            deleted_count += 1
        
        db.session.commit()
        
        return format_response(
            {'deleted_count': deleted_count},
            "Old models purged successfully",
            200
        )
        
    except Exception as e:
        db.session.rollback()
        return format_response(None, f"Failed to purge old models: {str(e)}", 500)

# Archive and clear labeled data
@active_learning_bp.route("/archive-labels", methods=["POST"])
@jwt_required()
def archive_labels():
    """
    Archive completed labels to CSV and optionally clear from database
    Useful after model training to free up database space
    """
    data = request.get_json() or {}
    clear_after_archive = data.get('clear_after_archive', False)
    
    try:
        # Get all completed items
        completed_items = db.session.query(
            LabelingQueue.id,
            LabelingQueue.news_id,
            LabelingQueue.text,
            LabelingQueue.finbert_score,
            LabelingQueue.llm_score,
            LabelingQueue.model_type,
            LabelingQueue.disagreement_score,
            LabelingQueue.uncertainty_score,
            LabelingQueue.created_at,
            LabelingQueue.updated_at,
            AggregatedLabel.final_label,
            AggregatedLabel.vote_count,
            AggregatedLabel.agreement_rate,
            AggregatedLabel.finalized_at
        ).join(
            AggregatedLabel,
            LabelingQueue.id == AggregatedLabel.queue_item_id
        ).filter(
            LabelingQueue.status == QueueStatus.COMPLETED
        ).all()
        
        if not completed_items:
            return format_response(None, "No completed labels to archive", 404)
        
        # Create archive
        archives_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            '..',
            'archives',
            'labeled_data'
        )
        os.makedirs(archives_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = os.path.join(archives_dir, f'labels_archive_{timestamp}.csv')
        
        # Write to CSV
        import csv
        with open(archive_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow([
                'queue_id', 'news_id', 'text', 'finbert_score', 'llm_score',
                'model_type', 'disagreement_score', 'uncertainty_score',
                'final_label', 'vote_count', 'agreement_rate',
                'created_at', 'updated_at', 'finalized_at'
            ])
            
            for item in completed_items:
                writer.writerow([
                    item.id,
                    item.news_id,
                    item.text[:500],  # Truncate long text
                    item.finbert_score,
                    item.llm_score,
                    item.model_type,
                    item.disagreement_score,
                    item.uncertainty_score,
                    item.final_label.value,
                    item.vote_count,
                    item.agreement_rate,
                    item.created_at.isoformat(),
                    item.updated_at.isoformat(),
                    item.finalized_at.isoformat()
                ])
        
        logger.info(f"Archived {len(completed_items)} labels to {archive_path}")
        
        # Optionally clear from database
        cleared_count = 0
        if clear_after_archive:
            # Delete aggregated labels (cascades to votes due to FK)
            for item in completed_items:
                aggregated = AggregatedLabel.query.filter_by(queue_item_id=item.id).first()
                if aggregated:
                    db.session.delete(aggregated)
                
                # Delete queue item
                queue_item = LabelingQueue.query.filter_by(id=item.id).first()
                if queue_item:
                    db.session.delete(queue_item)
                    cleared_count += 1
            
            db.session.commit()
            logger.info(f"Cleared {cleared_count} completed labels from database")
        
        return format_response({
            'archived_count': len(completed_items),
            'cleared_count': cleared_count,
            'archive_path': archive_path
        }, "Labels archived successfully", 200)
        
    except Exception as e:
        db.session.rollback()
        logger.error(f"Failed to archive labels: {str(e)}")
        return format_response(None, f"Failed to archive labels: {str(e)}", 500)

# Clear all user votes
@active_learning_bp.route("/reset-votes", methods=["POST"])
@jwt_required()
def reset_votes():
    """
    Reset all user votes and statistics
    WARNING: This is irreversible! Use with caution.
    """
    data = request.get_json() or {}
    confirm = data.get('confirm', False)
    
    if not confirm:
        return format_response(
            None, 
            "Must provide 'confirm': true to reset votes",
            400
        )
    
    try:
        # Count before deletion
        vote_count = UserVote.query.count()
        stats_count = UserStats.query.count()
        
        # Delete all votes
        UserVote.query.delete()
        
        # Reset user stats
        UserStats.query.update({
            'total_votes': 0,
            'gold_standard_correct': 0,
            'gold_standard_total': 0,
            'reliability_score': 1.0
        })
        
        db.session.commit()
        
        logger.warning(f"Reset {vote_count} votes and {stats_count} user stats")
        
        return format_response({
            'votes_deleted': vote_count,
            'stats_reset': stats_count
        }, "Votes reset successfully", 200)
        
    except Exception as e:
        db.session.rollback()
        return format_response(None, f"Failed to reset votes: {str(e)}", 500)

# Clear pending queue MIGHT REMOVE ON FRONTEND TOO AND THIS
@active_learning_bp.route("/clear-queue", methods=["POST"])
@jwt_required()
def clear_queue():
    """
    Clear all pending items from labeling queue
    Useful for removing stale/irrelevant items
    """
    data = request.get_json() or {}
    confirm = data.get('confirm', False)
    older_than_days = data.get('older_than_days', None)
    
    if not confirm:
        return format_response(
            None,
            "Must provide 'confirm': true to clear queue",
            400
        )
    
    try:
        query = LabelingQueue.query.filter(LabelingQueue.status == QueueStatus.PENDING)
        
        # Optional: Only clear old items
        if older_than_days:
            cutoff_date = datetime.now() - timedelta(days=older_than_days)
            query = query.filter(LabelingQueue.created_at < cutoff_date)
        
        count = query.count()
        query.delete()
        db.session.commit()
        
        logger.info(f"Cleared {count} pending queue items")
        
        return format_response({
            'cleared_count': count
        }, "Queue cleared successfully", 200)
        
    except Exception as e:
        db.session.rollback()
        return format_response(None, f"Failed to clear queue: {str(e)}", 500)
