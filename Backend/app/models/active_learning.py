from sqlalchemy import Column, Integer, String, Text, Float, DateTime, Boolean, JSON, ForeignKey, Enum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app import db
import enum
import uuid

class QueueStatus(enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress" 
    COMPLETED = "completed"
    SKIPPED = "skipped"

class SentimentVote(enum.Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"
    NEUTRAL = "neutral"

class FinalSentiment(enum.Enum):
    BULLISH = "bullish"
    BEARISH = "bearish"  
    NEUTRAL = "neutral"

class LabelingQueue(db.Model):
    __tablename__ = "labeling_queue"
    
    id = Column(Integer, primary_key=True, index=True)
    news_id = Column(String(50), nullable=True)
    text = Column(Text, nullable=False)
    finbert_score = Column(Float, nullable=False)
    llm_score = Column(Float, nullable=False)
    model_type = Column(String(20), nullable=False)  # 'openai', 'gemini', or 'user_feedback'
    disagreement_score = Column(Float, nullable=False)
    uncertainty_score = Column(Float, nullable=False)
    sampling_reason = Column(String(100), nullable=False)
    priority = Column(Integer, nullable=False)  # 1=highest, 5=lowest
    status = Column(Enum(QueueStatus), nullable=False, default=QueueStatus.PENDING)
    features_json = Column(JSON, nullable=True) 
    feature_names_json = Column(JSON, nullable=True) 
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=False)
    
    # Relationships
    votes = relationship("UserVote", back_populates="queue_item", cascade="all, delete-orphan")
    aggregated_label = relationship("AggregatedLabel", back_populates="queue_item", uselist=False)

class UserVote(db.Model):
    __tablename__ = "user_votes"
    
    id = Column(Integer, primary_key=True, index=True)
    queue_item_id = Column(Integer, ForeignKey("labeling_queue.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), nullable=False) 
    vote = Column(Enum(SentimentVote), nullable=False)  # bullish/bearish/neutral
    vote_time = Column(DateTime, server_default=func.now(), nullable=False)
    session_info = Column(JSON, nullable=True) # Feedback source, news id, timestamp, highpriority?
    
    # Relationships
    queue_item = relationship("LabelingQueue", back_populates="votes")

class AggregatedLabel(db.Model):
    __tablename__ = "aggregated_labels"
    
    id = Column(Integer, primary_key=True, index=True)
    queue_item_id = Column(Integer, ForeignKey("labeling_queue.id", ondelete="CASCADE"), nullable=False, unique=True)
    final_label = Column(Enum(FinalSentiment), nullable=False)  # Final consensus label
    vote_count = Column(Integer, nullable=False)
    agreement_rate = Column(Float, nullable=False)  # Percentage of votes that agreed
    aggregation_method = Column(String(50), nullable=False, default="majority")
    finalized_at = Column(DateTime, server_default=func.now(), nullable=False)
    
    # Relationships  
    queue_item = relationship("LabelingQueue", back_populates="aggregated_label")

class UserStats(db.Model):
    __tablename__ = "user_stats"
    
    user_id = Column(UUID(as_uuid=True), ForeignKey("user.id"), primary_key=True)
    total_votes = Column(Integer, default=0, nullable=False)
    gold_standard_correct = Column(Integer, default=0, nullable=False)
    gold_standard_total = Column(Integer, default=0, nullable=False) 
    reliability_score = Column(Float, default=1.0, nullable=False) 
    last_active = Column(DateTime, server_default=func.now(), nullable=False)

class ModelRun(db.Model):
    __tablename__ = "model_runs"
    
    id = Column(Integer, primary_key=True, index=True)
    model_version = Column(String(50), nullable=False)
    artifact_path = Column(String(500), nullable=True)  # Path to model artifacts
    training_samples = Column(Integer, nullable=False)
    performance_metrics = Column(JSON, nullable=True)  # Store accuracy, F1, etc.
    created_at = Column(DateTime, server_default=func.now(), nullable=False)
    is_active = Column(Boolean, default=False, nullable=False)  # Current active model
