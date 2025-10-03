from fpdf import FPDF
import matplotlib.pyplot as plt
import os
import logging
from datetime import datetime
from app.services.recommendation_service import get_client_recommendations
from app.services.portfolio_service import get_client_portfolio_health, get_client_portfolio_summary
from app.models.user import User

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "..", "..", "temp_pdfs")
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def sanitize_text(text):
    """Replace unsupported characters with ASCII equivalents"""
    if text is None:
        return ""
    return str(text).encode("ascii", "ignore").decode()


def get_risk_color(risk_level):
    """Get color based on risk level"""
    risk_colors = {
        'LOW': (0, 200, 0),
        'MODERATE': (255, 204, 0),
        'HIGH': (255, 0, 0)
    }
    return risk_colors.get(risk_level, (128, 128, 128))


def get_sentiment_color(sentiment_score):
    """Get color based on sentiment score"""
    if sentiment_score > 20:
        return (0, 200, 0)
    elif sentiment_score > -20:
        return (255, 204, 0)
    else:
        return (255, 0, 0)


def generate_recommendation_pdf(client_id, output_filename=None):
    """Generate comprehensive recommendation PDF for a client"""
    try:
        client = User.query.get(client_id)
        if not client or not client.is_client():
            raise ValueError("Client not found or invalid")

        if not output_filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            output_filename = f"{client.email}_recommendations_{timestamp}.pdf"

        output_path = os.path.abspath(os.path.join(UPLOAD_FOLDER, output_filename))
        logger.info(f"PDF output path: {output_path}")

        recommendations = get_client_recommendations(client_id, limit=10)
        health_data = get_client_portfolio_health(client_id)
        portfolio_summary = get_client_portfolio_summary(client_id)

        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        page_width = pdf.w - 20

        # Cover Page
        pdf.add_page()
        pdf.set_font("Arial", "B", 20)
        pdf.cell(0, 20, "Investment Recommendations Report", ln=True, align="C")
        pdf.ln(5)

        pdf.set_font("Arial", "B", 16)
        client_name = f"{client.first_name} {client.last_name}"
        pdf.cell(0, 10, f"Client: {client_name}", ln=True, align="C")
        pdf.ln(10)

        timestamp = datetime.now().strftime("%B %d, %Y at %I:%M %p")
        pdf.set_font("Arial", "", 12)
        pdf.cell(0, 10, f"Generated on: {timestamp}", ln=True, align="C")
        pdf.ln(20)

        # Executive Summary
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Executive Summary", ln=True)
        pdf.ln(5)

        pdf.set_font("Arial", "", 11)

        buy_recs = [r for r in recommendations if r['action'] == 'BUY']
        sell_recs = [r for r in recommendations if r['action'] == 'SELL']

        summary_text = f"""
This report provides personalized investment recommendations based on current market sentiment,
portfolio analysis, and your risk preferences. We have identified {len(buy_recs)} buying
opportunities and {len(sell_recs)} positions that may require attention.

Portfolio Health Score: {health_data.get('overall_health_score', 0):.1f}/100
Total Portfolio Value: ${portfolio_summary.get('total_portfolio_value', 0):,.2f}
"""
        pdf.multi_cell(0, 6, sanitize_text(summary_text.strip()))

        # Portfolio Health Section
        _add_portfolio_health_section(pdf, health_data, page_width)

        # Recommendations Section
        _add_recommendations_section(pdf, recommendations, page_width)

        # Risk Disclaimer
        _add_risk_disclaimer(pdf)

        pdf.output(output_path, "F")
        logger.info(f"Recommendation PDF successfully created: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Recommendation PDF generation error: {str(e)}")
        raise


def _add_portfolio_health_section(pdf, health_data, page_width):
    """Add portfolio health analysis section"""
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Portfolio Health Analysis", ln=True)
    pdf.ln(5)

    # Health Score
    health_score = health_data.get('overall_health_score', 0)
    pdf.set_font("Arial", "B", 12)
    pdf.cell(60, 10, "Overall Health Score:", align="L")

    # Color based on health score
    if health_score >= 80:
        color = (0, 200, 0)
    elif health_score >= 60:
        color = (255, 204, 0)
    else:
        color = (255, 0, 0)

    pdf.set_text_color(*color)
    pdf.cell(30, 10, f"{health_score:.1f}/100", ln=True, align="L")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # Cash Analysis
    cash_info = health_data.get('cash_analysis', {})
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 8, "Cash Position Analysis", ln=True)
    pdf.set_font("Arial", "", 10)

    cash_details = f"""Available Cash: ${cash_info.get('available_cash', 0):,.2f}
Cash Percentage: {cash_info.get('cash_percent', 0):.1f}%
Minimum Required: {cash_info.get('min_required_percent', 10):.1f}%
Status: {cash_info.get('status', 'Unknown').replace('_', ' ').title()}"""

    pdf.multi_cell(0, 5, sanitize_text(cash_details))
    pdf.ln(3)

    # Recommendations
    recommendations = health_data.get('recommendations', [])
    if recommendations:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 8, "Health Recommendations:", ln=True)
        pdf.set_font("Arial", "", 10)

        for i, rec in enumerate(recommendations[:5], 1):
            pdf.multi_cell(0, 5, f"{i}. {sanitize_text(rec)}")
        pdf.ln(5)


def _add_recommendations_section(pdf, recommendations, page_width):
    """Add investment recommendations section"""
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Investment Recommendations", ln=True)
    pdf.ln(5)

    # Buy Recommendations
    buy_recs = [r for r in recommendations if r['action'] == 'BUY']
    if buy_recs:
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Buy Recommendations", ln=True)
        pdf.ln(3)

        for i, rec in enumerate(buy_recs, 1):
            _add_recommendation_item(pdf, rec, i)

    # Sell Recommendations
    sell_recs = [r for r in recommendations if r['action'] == 'SELL']
    if sell_recs:
        if buy_recs:  # Add page break if we had buy recommendations
            pdf.add_page()

        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, "Sell Recommendations", ln=True)
        pdf.ln(3)

        for i, rec in enumerate(sell_recs, 1):
            _add_recommendation_item(pdf, rec, i)


def _add_recommendation_item(pdf, rec, index):
    """Add individual recommendation item"""
    # Header with entity name and action
    pdf.set_font("Arial", "B", 12)
    pdf.set_fill_color(240, 240, 240)

    action_color = (0, 150, 0) if rec['action'] == 'BUY' else (200, 0, 0)

    header_text = f"{index}. {rec['entity_name']} ({rec['ticker']}) - {rec['action']}"
    pdf.cell(0, 8, sanitize_text(header_text), ln=True, fill=True)
    pdf.ln(2)

    # Recommendation details
    pdf.set_font("Arial", "", 10)

    details = f"""Confidence: {rec['recommendation_confidence']:.0%}
Sentiment Score: {rec['sentiment_score']:.1f}
Risk Level: {rec['risk_level']}"""

    if rec.get('suggested_amount'):
        details += f"\nSuggested Amount: ${rec['suggested_amount']:,.2f}"

    if rec.get('suggested_allocation_percent'):
        details += f"\nSuggested Allocation: {rec['suggested_allocation_percent']:.1f}%"

    pdf.multi_cell(0, 5, sanitize_text(details))
    pdf.ln(2)

    # Reasoning
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 5, "Reasoning:", ln=True)
    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, sanitize_text(rec.get('reasoning', 'No reasoning provided')))
    pdf.ln(5)


def _add_risk_disclaimer(pdf):
    """Add risk disclaimer section"""
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Important Risk Disclaimer", ln=True)
    pdf.ln(5)

    disclaimer_text = """
This report is generated based on algorithmic analysis of market sentiment and portfolio data.
All investment recommendations are suggestions only and should not be considered as financial advice.

Key Considerations:
• Past performance does not guarantee future results
• All investments carry risk of loss
• Market conditions can change rapidly
• Consider your personal financial situation before acting
• Consult with a qualified financial advisor before making investment decisions

The sentiment analysis and recommendations are based on publicly available information and
automated analysis. Human judgment and additional research should always be applied before
making any investment decisions.

This system is designed to assist relationship managers in providing better service to clients
but does not replace professional financial advice or human oversight.
"""

    pdf.set_font("Arial", "", 10)
    pdf.multi_cell(0, 5, sanitize_text(disclaimer_text.strip()))

    # Footer with timestamp
    pdf.set_y(-25)
    pdf.set_font("Arial", "I", 8)
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    pdf.cell(0, 10, f"Report generated on: {timestamp}", 0, 1, "C")


def generate_client_recommendation_report(client_id):
    """Convenience function to generate recommendation report"""
    return generate_recommendation_pdf(client_id)