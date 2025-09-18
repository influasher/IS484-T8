"""
Entity Sentiment Analyzer - Module for calculating unified entity sentiment

This module provides functionality for analyzing sentiment at the entity level
across multiple articles, using different weighting methods for aggregation:
- Simple average: Equal weight to all articles
- Confidence-weighted: Articles with higher confidence get more weight
- Time-decay weighted: More recent articles get more weight
- Combined weighting: Both confidence and recency affect weight
"""

import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from tqdm import tqdm
from collections import Counter
import time

# Import our core sentiment analyzer
from app.services.sentiment_analysis import SentimentAnalyzer


class EntitySentimentAnalyzer:
    def __init__(self, output_dir="entity_sentiment_results"):
        """
        Initialize the entity sentiment analyzer

        Parameters:
        - output_dir: Directory to store results and visualizations
        """
        self.analyzer = SentimentAnalyzer()
        self.output_dir = output_dir

        # # Create output directory if it doesn't exist
        # if not os.path.exists(output_dir):
        #     os.makedirs(output_dir)

        # Initialize results storage
        self.entity_results = {}
        self.article_results = []

        # Track model disagreements
        self.disagreement_stats = {
            "total_articles": 0,
            "disagreement_count": 0,
            "disagreement_rate": 0.0,
            "disagreement_by_model": {
                "finbert_gemini": 0,
                "finbert_openai": 0,
                "gemini_openai": 0,
                "all_models": 0,
            },
        }

        # Track specific disagreement patterns
        self.disagreement_patterns = []

    def analyze_article(self, article_text, article_metadata=None, run_all_models=True):
        """
        Analyze a single article with all models and record disagreements

        Parameters:
        - article_text: The text content of the article
        - article_metadata: Dictionary with metadata (source, date, title, etc.)
        - run_all_models: Whether to run all three models (FinBERT, Gemini, OpenAI)

        Returns:
        - Dictionary with analysis results
        """
        if article_metadata is None:
            article_metadata = {
                "id": len(self.article_results) + 1,
                "timestamp": datetime.now().isoformat(),
            }

        # Track this article in our stats
        self.disagreement_stats["total_articles"] += 1

        # Run FinBERT (always run this as our baseline)
        finbert_result = self.analyzer.analyze_with_finbert(article_text)

        # Initialize model results
        model_results = {
            "finbert": {
                "classification": finbert_result["classification"],
                "score": finbert_result["numerical_score"],
            }
        }

        # Run Gemini if requested
        gemini_result = None
        if run_all_models:
            try:
                if not self.analyzer.gemini_client:
                    self.analyzer._load_gemini()
                gemini_result = self.analyzer.analyze_with_gemini(article_text)
                model_results["gemini"] = {
                    "classification": gemini_result["classification"],
                    "score": gemini_result["numerical_score"],
                }
            except Exception as e:
                print(f"Error running Gemini: {e}")
                model_results["gemini"] = {"error": str(e)}

        # Run OpenAI if requested
        openai_result = None
        if run_all_models:
            try:
                if not hasattr(self.analyzer, "openai_api_key"):
                    self.analyzer._load_openai()
                openai_result = self.analyzer.analyze_with_openai(article_text)
                model_results["openai"] = {
                    "classification": openai_result["classification"],
                    "score": openai_result["numerical_score"],
                }
            except Exception as e:
                print(f"Error running OpenAI: {e}")
                model_results["openai"] = {"error": str(e)}

        # Create integrated results (with available models)
        integrated_results = {}
        if gemini_result:
            integrated_results["finbert_gemini"] = self.analyzer.weighted_integration(
                finbert_result, gemini_result
            )

        if openai_result:
            integrated_results["finbert_openai"] = self.analyzer.weighted_integration(
                finbert_result, openai_result
            )

        if gemini_result and openai_result:
            integrated_results["gemini_openai"] = self.analyzer.weighted_integration(
                gemini_result, openai_result
            )

        # Check for disagreements (based on classification, not score)
        disagreement = False
        disagreement_models = []

        if (
            gemini_result
            and finbert_result["classification"] != gemini_result["classification"]
        ):
            disagreement = True
            disagreement_models.append("finbert_gemini")
            self.disagreement_stats["disagreement_by_model"]["finbert_gemini"] += 1

        if (
            openai_result
            and finbert_result["classification"] != openai_result["classification"]
        ):
            disagreement = True
            disagreement_models.append("finbert_openai")
            self.disagreement_stats["disagreement_by_model"]["finbert_openai"] += 1

        if (
            gemini_result
            and openai_result
            and gemini_result["classification"] != openai_result["classification"]
        ):
            disagreement = True
            disagreement_models.append("gemini_openai")
            self.disagreement_stats["disagreement_by_model"]["gemini_openai"] += 1

        # Check if all three models disagree with each other
        if (
            gemini_result
            and openai_result
            and finbert_result["classification"] != gemini_result["classification"]
            and finbert_result["classification"] != openai_result["classification"]
            and gemini_result["classification"] != openai_result["classification"]
        ):
            self.disagreement_stats["disagreement_by_model"]["all_models"] += 1

        # If there was a disagreement, update our stats
        if disagreement:
            self.disagreement_stats["disagreement_count"] += 1

            # Record specific disagreement pattern
            self.disagreement_patterns.append(
                {
                    "article_id": article_metadata.get(
                        "id", len(self.article_results) + 1
                    ),
                    "models": disagreement_models,
                    "classifications": {
                        "finbert": finbert_result["classification"],
                        "gemini": (
                            gemini_result["classification"] if gemini_result else None
                        ),
                        "openai": (
                            openai_result["classification"] if openai_result else None
                        ),
                    },
                    "scores": {
                        "finbert": finbert_result["numerical_score"],
                        "gemini": (
                            gemini_result["numerical_score"] if gemini_result else None
                        ),
                        "openai": (
                            openai_result["numerical_score"] if openai_result else None
                        ),
                    },
                }
            )

        # Update disagreement rate
        self.disagreement_stats["disagreement_rate"] = (
            self.disagreement_stats["disagreement_count"]
            / self.disagreement_stats["total_articles"]
        )

        # Compile full result
        result = {
            "metadata": article_metadata,
            "text_sample": article_text[:200] + "...",  # Store a sample of the text
            "model_results": model_results,
            "integrated_results": integrated_results,
            "disagreement": disagreement,
            "disagreement_models": disagreement_models if disagreement else [],
        }

        # Store result
        self.article_results.append(result)

        return result

    def analyze_corpus(self, articles, run_all_models=True):
        """
        Analyze a corpus of articles and compile overall statistics

        Parameters:
        - articles: List of dictionaries, each with 'text' key and optional 'metadata' key
        - run_all_models: Whether to run all available models

        Returns:
        - Dictionary with corpus-level statistics
        """
        results = []

        for i, article in enumerate(tqdm(articles, desc="Analyzing articles")):
            text = article["text"]
            metadata = article.get("metadata", {"id": i + 1})

            result = self.analyze_article(text, metadata, run_all_models)
            results.append(result)

        # Save raw results
        self._save_results("corpus_results.json", results)

        # Generate and save summary statistics
        summary = self._generate_corpus_summary(results)
        self._save_results("corpus_summary.json", summary)

        return summary

    def _generate_corpus_summary(self, results):
        """Generate summary statistics for a corpus of articles"""
        total_articles = len(results)
        disagreement_count = sum(1 for r in results if r["disagreement"])

        # Count by model
        model_counts = {
            "finbert": total_articles,
            "gemini": sum(
                1
                for r in results
                if "gemini" in r["model_results"]
                and isinstance(r["model_results"]["gemini"], dict)
                and "classification" in r["model_results"]["gemini"]
            ),
            "openai": sum(
                1
                for r in results
                if "openai" in r["model_results"]
                and isinstance(r["model_results"]["openai"], dict)
                and "classification" in r["model_results"]["openai"]
            ),
        }

        # Count classifications by model
        classifications = {
            "finbert": Counter(
                [r["model_results"]["finbert"]["classification"] for r in results]
            ),
            "gemini": Counter(
                [
                    r["model_results"]["gemini"]["classification"]
                    for r in results
                    if "gemini" in r["model_results"]
                ]
            ),
            "openai": Counter(
                [
                    r["model_results"]["openai"]["classification"]
                    for r in results
                    if "openai" in r["model_results"]
                ]
            ),
        }

        # Calculate average scores by model
        avg_scores = {
            "finbert": np.mean(
                [r["model_results"]["finbert"]["score"] for r in results]
            ),
            "gemini": np.mean(
                [
                    r["model_results"]["gemini"]["score"]
                    for r in results
                    if "gemini" in r["model_results"]
                    and isinstance(r["model_results"]["gemini"], dict)
                    and "score" in r["model_results"]["gemini"]
                ]
            ),
            "openai": np.mean(
                [
                    r["model_results"]["openai"]["score"]
                    for r in results
                    if "openai" in r["model_results"]
                    and isinstance(r["model_results"]["openai"], dict)
                    and "score" in r["model_results"]["openai"]
                ]
            ),
        }

        summary = {
            "total_articles": total_articles,
            "disagreement_count": disagreement_count,
            "disagreement_rate": (
                disagreement_count / total_articles if total_articles > 0 else 0
            ),
            "model_counts": model_counts,
            "classifications_by_model": {
                k: dict(v) for k, v in classifications.items()
            },
            "avg_scores_by_model": avg_scores,
            "disagreement_by_model_pair": dict(
                self.disagreement_stats["disagreement_by_model"]
            ),
        }

        return summary

    def _save_results(self, filename, data):
        """Save results to a JSON file"""
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w") as f:
            json.dump(data, f, indent=2)
        print(f"Saved results to {filepath}")

    def generate_unified_sentiment_scores(self, entity_name, articles, weights=None):
        """
        Generate unified sentiment scores for a given entity across multiple articles

        Parameters:
        - entity_name: Name of the entity (company, stock, etc.)
        - articles: List of dictionaries with 'text' and 'metadata' keys
        - weights: Configuration for weighting factors (confidence, time decay, etc.)

        Returns:
        - Dictionary with unified sentiment score and related statistics
        """
        if weights is None:
            weights = {"confidence": True, "time_decay": False, "decay_factor": 0.9}

        # Analyze all articles if not already analyzed
        for i, article in enumerate(articles):
            if "analysis" not in article:
                metadata = {
                    "id": i + 1,
                    "entity": entity_name,
                    "date": article.get("metadata", {}).get(
                        "date", datetime.now().isoformat()
                    ),
                    "source": article.get("metadata", {}).get("source", "unknown"),
                }
                # delay the analysis to avoid rate limits
                time.sleep(60 / 15)
                article["analysis"] = self.analyze_article(article["text"], metadata)

        # Extract scores and confidences
        scores = []
        confidences = []
        dates = []

        for article in articles:
            analysis = article["analysis"]

            # Use finbert_gemini integration if available, otherwise fallback
            if "finbert_gemini" in analysis.get("integrated_results", {}):
                integrated = analysis["integrated_results"]["finbert_gemini"]
                scores.append(integrated["numerical_score"])
                confidences.append(integrated["confidence"])
            else:
                # Fallback to finbert
                scores.append(
                    analysis["model_results"]["finbert"]["score"] * 100
                )  # Scale to -100 to +100
                confidences.append(0.7)  # Default confidence

            # Get date if available
            if "date" in article.get("metadata", {}):
                dates.append(article["metadata"]["date"])
            else:
                dates.append(datetime.now().isoformat())

        # Prepare DataFrame for aggregation
        df = pd.DataFrame(
            {"score": scores, "confidence": confidences, "date": pd.to_datetime(dates)}
        )

        # DEBUG - Print raw data
        print("\nDEBUG - Raw Data:")
        print(f"Scores: {df['score'].tolist()}")
        print(f"Confidences: {df['confidence'].tolist()}")
        print(f"Dates: {df['date'].tolist()}")

        # Calculate time weights if requested
        if weights.get("time_decay", False) and len(set(dates)) > 1:
            # Convert to days from most recent
            most_recent = df["date"].max()
            df["days_old"] = (most_recent - df["date"]).dt.days

            # Apply exponential decay
            decay_factor = weights.get("decay_factor", 0.9)
            df["time_weight"] = np.power(decay_factor, df["days_old"])

            # DEBUG - Print time weight calculations
            print("\nDEBUG - Time Weights:")
            print(f"Most recent date: {most_recent}")
            print(f"Days old: {df['days_old'].tolist()}")
            print(f"Decay factor: {decay_factor}")
            print(f"Raw time weights: {df['time_weight'].tolist()}")
        else:
            df["days_old"] = 0
            df["time_weight"] = 1.0

            print("\nDEBUG - Time Weights Disabled or Same Dates:")
            print(f"Using uniform time weights: {df['time_weight'].tolist()}")

        # Calculate different aggregation methods
        aggregations = {}

        # Simple average
        simple_avg = df["score"].mean()
        aggregations["simple_average"] = {
            "score": simple_avg,
            "description": "Simple average of all article scores",
        }

        print(f"\nDEBUG - Simple Average: {simple_avg:.2f}")

        # Confidence-weighted average
        if weights.get("confidence", True):
            # Check if confidences sum to zero to avoid division by zero
            if df["confidence"].sum() > 0:
                # Normalize confidence weights
                confidence_weights = df["confidence"] / df["confidence"].sum()

                # Calculate weighted average
                confidence_weighted_avg = (df["score"] * confidence_weights).sum()

                print("\nDEBUG - Confidence Weighting:")
                print(f"Normalized confidence weights: {confidence_weights.tolist()}")
                print(f"Confidence-weighted average: {confidence_weighted_avg:.2f}")
            else:
                # Fallback to simple average if all confidences are zero
                confidence_weighted_avg = simple_avg
                print("\nDEBUG - All confidences are zero, using simple average")

            aggregations["confidence_weighted"] = {
                "score": confidence_weighted_avg,
                "description": "Scores weighted by model confidence",
            }

        # Time-decay weighted average
        if weights.get("time_decay", False):
            # Check if time weights sum to zero to avoid division by zero
            if df["time_weight"].sum() > 0:
                # Normalize time weights
                time_weights = df["time_weight"] / df["time_weight"].sum()

                # Calculate weighted average
                time_weighted_avg = (df["score"] * time_weights).sum()

                print("\nDEBUG - Time Weighting:")
                print(f"Normalized time weights: {time_weights.tolist()}")
                print(f"Time-weighted average: {time_weighted_avg:.2f}")
            else:
                # Fallback to simple average if all time weights are zero
                time_weighted_avg = simple_avg
                print("\nDEBUG - All time weights are zero, using simple average")

            aggregations["time_weighted"] = {
                "score": time_weighted_avg,
                "description": "Scores weighted by recency",
            }

        # Combined weighting (confidence × time)
        if weights.get("confidence", True) and weights.get("time_decay", False):
            # Calculate combined weights
            combined_weights = df["confidence"] * df["time_weight"]

            # Check if combined weights sum to zero to avoid division by zero
            if combined_weights.sum() > 0:
                # Normalize combined weights
                normalized_combined = combined_weights / combined_weights.sum()

                # Calculate weighted average
                combined_weighted_avg = (df["score"] * normalized_combined).sum()

                print("\nDEBUG - Combined Weighting:")
                print(f"Raw combined weights: {combined_weights.tolist()}")
                print(f"Normalized combined weights: {normalized_combined.tolist()}")
                print(f"Combined weighted average: {combined_weighted_avg:.2f}")
            else:
                # Fallback to simple average if all combined weights are zero
                combined_weighted_avg = simple_avg
                print("\nDEBUG - All combined weights are zero, using simple average")

            aggregations["combined_weighted"] = {
                "score": combined_weighted_avg,
                "description": "Scores weighted by confidence and recency",
            }

        # Determine final unified score based on preferred method
        preferred_method = weights.get("preferred_method", "confidence_weighted")
        if preferred_method not in aggregations:
            preferred_method = list(aggregations.keys())[0]

        unified_score = aggregations[preferred_method]["score"]

        # Determine classification
        if unified_score > 10:
            classification = "bullish"
        elif unified_score < -10:
            classification = "bearish"
        else:
            classification = "neutral"

        # Calculate confidence in the unified score
        # (based on consistency of individual scores and number of articles)
        score_std = df["score"].std()
        article_count = len(df)
        score_range = max(1, df["score"].max() - df["score"].min())

        # Lower std dev and more articles = higher confidence
        confidence_factor = 1 - min(0.7, score_std / score_range)
        confidence_factor *= min(
            1.0, article_count / 5
        )  # More articles = higher confidence
        confidence_factor = max(
            0.3, min(0.95, confidence_factor)
        )  # Bound between 0.3 and 0.95

        result = {
            "entity": entity_name,
            "unified_score": unified_score,
            "classification": classification,
            "confidence": confidence_factor,
            "article_count": article_count,
            "aggregation_methods": aggregations,
            "preferred_method": preferred_method,
            "scores": df["score"].tolist(),
            "confidences": df["confidence"].tolist(),
            "dates": [date.isoformat() for date in df["date"]],
            "std_dev": score_std,
        }

        # Final debug output
        print("\nDEBUG - Final Results:")
        print(f"Unified Score ({preferred_method}): {unified_score:.2f}")
        print(f"Classification: {classification}")
        print(f"Confidence: {confidence_factor:.2f}")
        print("All Aggregation Methods:")
        for method, details in aggregations.items():
            print(f"  - {method}: {details['score']:.2f}")

        # # Save result
        # filename = f"{entity_name.lower().replace(' ', '_')}_unified_sentiment.json"
        # self._save_results(filename, result)

        # Store in entity results
        self.entity_results[entity_name] = result

        return result

    def print_disagreement_report(self):
        """Print a report of model disagreements"""
        if self.disagreement_stats["total_articles"] == 0:
            print("No articles have been analyzed yet.")
            return

        print("\n" + "=" * 50)
        print("MODEL DISAGREEMENT REPORT")
        print("=" * 50)

        print(f"\nTotal articles analyzed: {self.disagreement_stats['total_articles']}")
        print(
            f"Articles with model disagreement: {self.disagreement_stats['disagreement_count']}"
        )
        print(f"Disagreement rate: {self.disagreement_stats['disagreement_rate']:.2%}")

        print("\nDisagreement by model pair:")
        for pair, count in self.disagreement_stats["disagreement_by_model"].items():
            rate = count / self.disagreement_stats["total_articles"]
            print(f"  - {pair}: {count} articles ({rate:.2%})")

        # Show sample of disagreements
        if self.disagreement_patterns:
            print("\nSample of disagreement patterns:")
            sample_size = min(5, len(self.disagreement_patterns))
            for i in range(sample_size):
                pattern = self.disagreement_patterns[i]
                print(f"\nArticle ID: {pattern['article_id']}")
                print("Classifications:")
                for model, classification in pattern["classifications"].items():
                    if classification:
                        print(
                            f"  - {model}: {classification} (score: {pattern['scores'][model]:.2f})"
                        )

        print("\n" + "=" * 50)

    def visualize_disagreement_stats(self, save_path=None):
        """Create visualizations of disagreement statistics"""
        if self.disagreement_stats["total_articles"] == 0:
            print("No articles have been analyzed yet.")
            return

        # Create figure with multiple subplots
        fig, axes = plt.subplots(2, 1, figsize=(10, 12))

        # Plot overall disagreement rate
        axes[0].bar(
            ["Agreement", "Disagreement"],
            [
                1 - self.disagreement_stats["disagreement_rate"],
                self.disagreement_stats["disagreement_rate"],
            ],
            color=["green", "red"],
        )
        axes[0].set_title("Overall Model Agreement vs. Disagreement")
        axes[0].set_ylabel("Proportion of Articles")
        for i, v in enumerate(
            [
                1 - self.disagreement_stats["disagreement_rate"],
                self.disagreement_stats["disagreement_rate"],
            ]
        ):
            axes[0].text(
                i, v / 2, f"{v:.1%}", ha="center", fontweight="bold", color="white"
            )

        # Plot disagreement by model pair
        model_pairs = list(self.disagreement_stats["disagreement_by_model"].keys())
        counts = list(self.disagreement_stats["disagreement_by_model"].values())

        # Calculate rates
        rates = [count / self.disagreement_stats["total_articles"] for count in counts]

        # Sort by rate
        sorted_indices = np.argsort(rates)[::-1]
        sorted_pairs = [model_pairs[i] for i in sorted_indices]
        sorted_rates = [rates[i] for i in sorted_indices]

        axes[1].bar(sorted_pairs, sorted_rates, color="orange")
        axes[1].set_title("Disagreement Rate by Model Pair")
        axes[1].set_ylabel("Disagreement Rate")
        axes[1].set_xlabel("Model Pairs")
        axes[1].tick_params(axis="x", rotation=45)

        for i, v in enumerate(sorted_rates):
            axes[1].text(
                i, v / 2, f"{v:.1%}", ha="center", fontweight="bold", color="black"
            )

        plt.tight_layout()

        # Save if path provided
        if save_path:
            plt.savefig(save_path)
            print(f"Saved visualization to {save_path}")

        plt.show()

    def visualize_entity_sentiment(self, entity_result, save_path=None):
        """
        Visualize unified sentiment for an entity

        Parameters:
        - entity_result: Result dictionary from generate_unified_sentiment_scores
        - save_path: Optional path to save the visualization
        """
        fig, axes = plt.subplots(2, 1, figsize=(10, 10))

        # Plot unified score
        score = entity_result["unified_score"]
        color = "green" if score > 10 else "red" if score < -10 else "gray"

        axes[0].barh(["Unified Sentiment"], [score], color=color)
        axes[0].set_title(f"Unified Sentiment for {entity_result['entity']}")
        axes[0].set_xlim(-100, 100)
        axes[0].axvline(x=0, color="black", linestyle="-", alpha=0.3)
        axes[0].set_xlabel("Sentiment Score (-100 = Bearish, +100 = Bullish)")

        for spine in ["top", "right"]:
            axes[0].spines[spine].set_visible(False)

        # Plot individual article scores
        articles = list(range(1, len(entity_result["scores"]) + 1))
        scores = entity_result["scores"]

        colors = ["green" if s > 10 else "red" if s < -10 else "gray" for s in scores]

        axes[1].bar(articles, scores, color=colors)
        axes[1].set_title(f"Individual Article Scores (n={len(scores)})")
        axes[1].set_xlabel("Article")
        axes[1].set_ylabel("Sentiment Score")
        axes[1].set_ylim(min(min(scores) - 10, -100), max(max(scores) + 10, 100))
        axes[1].axhline(y=0, color="black", linestyle="-", alpha=0.3)

        # Add unified score line
        axes[1].axhline(
            y=score, color="blue", linestyle="--", label=f"Unified Score: {score:.1f}"
        )
        axes[1].legend()

        plt.tight_layout()

        # Save if path provided
        if save_path:
            plt.savefig(save_path)
            print(f"Saved visualization to {save_path}")

        plt.show()

    def create_detailed_visualization(self, entity_name, save_path=None):
        """
        Create a detailed visualization showing all weighting methods

        Parameters:
        - entity_name: Name of the entity to visualize
        - save_path: Optional path to save the visualization
        """
        # Check if entity data exists
        if entity_name not in self.entity_results:
            print(
                f"No data for entity {entity_name}. Please run generate_unified_sentiment_scores first."
            )
            return

        entity_result = self.entity_results[entity_name]

        # Extract data
        scores = entity_result["scores"]
        confidences = entity_result["confidences"]
        dates = [datetime.fromisoformat(d) for d in entity_result["dates"]]

        # Create figure
        fig = plt.figure(figsize=(12, 10))
        gs = fig.add_gridspec(3, 1, height_ratios=[1, 1, 1.5])

        # Article scores subplot
        ax1 = fig.add_subplot(gs[0])
        colors = ["green" if s > 10 else "red" if s < -10 else "gray" for s in scores]
        indices = list(range(1, len(scores) + 1))

        bars = ax1.bar(indices, scores, color=colors)

        # Add confidence as text on bars
        for i, bar in enumerate(bars):
            height = bar.get_height()
            pos_y = height + 5 if height >= 0 else height - 15
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                pos_y,
                f"Conf: {confidences[i]:.2f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

        ax1.set_title(f"Individual Article Scores for {entity_name}", fontsize=14)
        ax1.set_xlabel("Article Number")
        ax1.set_ylabel("Sentiment Score")
        ax1.set_ylim(min(min(scores) - 10, -100), max(max(scores) + 10, 100))
        ax1.axhline(y=0, color="black", linestyle="-", alpha=0.3)
        ax1.set_xticks(indices)

        # Aggregation methods subplot
        ax2 = fig.add_subplot(gs[1])
        methods = []
        values = []

        for method, details in entity_result["aggregation_methods"].items():
            methods.append(method.replace("_", "\n"))
            values.append(details["score"])

        # Highlight preferred method
        colors = [
            (
                "#FFC107"
                if method.replace("\n", "_") == entity_result["preferred_method"]
                else "#4CAF50"
            )
            for method in methods
        ]

        bars = ax2.bar(methods, values, color=colors)

        # Add values on bars
        for bar in bars:
            height = bar.get_height()
            pos_y = height + 2 if height >= 0 else height - 8
            ax2.text(
                bar.get_x() + bar.get_width() / 2,
                pos_y,
                f"{height:.2f}",
                ha="center",
                va="bottom",
            )

        ax2.set_title("Comparison of Aggregation Methods", fontsize=14)
        ax2.set_ylabel("Unified Sentiment Score")
        ax2.set_ylim(min(min(values) - 10, -100), max(max(values) + 10, 100))
        ax2.axhline(y=0, color="black", linestyle="-", alpha=0.3)

        # Create a table to show all weighting factors
        ax3 = fig.add_subplot(gs[2])

        cell_text = []

        # Process dates for display
        most_recent = max(dates)
        days_old = [(most_recent - date).days for date in dates]

        # Calculate weights for display
        decay_factor = 0.9  # Default decay factor
        time_weights = [decay_factor**d for d in days_old]
        time_weights_norm = [w / sum(time_weights) for w in time_weights]

        confidence_weights = [c / sum(confidences) for c in confidences]

        combined_weights = [c * t for c, t in zip(confidences, time_weights)]
        combined_weights_norm = [w / sum(combined_weights) for w in combined_weights]

        # Create table data
        for i in range(len(scores)):
            try:
                article_title = f"Article {i+1}"
                if "title" in entity_result.get("article_data", [{}])[i]:
                    article_title = (
                        entity_result["article_data"][i]["title"][:20] + "..."
                    )
            except (IndexError, KeyError):
                article_title = f"Article {i+1}"

            cell_text.append(
                [
                    article_title,
                    f"{scores[i]:.2f}",
                    f"{confidences[i]:.2f}",
                    f"{confidence_weights[i]:.3f}",
                    f"{days_old[i]}",
                    f"{time_weights_norm[i]:.3f}",
                    f"{combined_weights_norm[i]:.3f}",
                ]
            )

        columns = [
            "Article",
            "Score",
            "Confidence",
            "Conf Weight",
            "Days Old",
            "Time Weight",
            "Combined Weight",
        ]

        # Create table
        table = ax3.table(
            cellText=cell_text, colLabels=columns, loc="center", cellLoc="center"
        )

        # Style the table
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 1.5)

        # Style header
        for (row, col), cell in table.get_celld().items():
            if row == 0:
                cell.set_text_props(fontproperties=dict(weight="bold"))
                cell.set_facecolor("#E0E0E0")

        ax3.set_title("Detailed Weighting Analysis", fontsize=14)
        ax3.axis("off")

        # Final unified result as text
        final_score = entity_result["unified_score"]
        classification = entity_result["classification"]
        confidence = entity_result["confidence"]
        preferred_method = entity_result["preferred_method"]

        result_text = (
            f"UNIFIED {entity_name.upper()} SENTIMENT SCORE: {final_score:.2f}\n"
            f"Classification: {classification.upper()}\n"
            f"Confidence: {confidence:.2f}\n"
            f"Preferred Method: {preferred_method.replace('_', ' ').title()}"
        )

        fig.text(
            0.5,
            0.02,
            result_text,
            ha="center",
            fontsize=14,
            bbox=dict(
                facecolor="#FFF9C4", edgecolor="#FFC107", boxstyle="round,pad=0.5"
            ),
        )

        plt.tight_layout(rect=[0, 0.05, 1, 0.95])

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches="tight")
            print(f"Detailed visualization saved to: {save_path}")

        plt.show()
