import yfinance as yf
import matplotlib.pyplot as plt
import pandas as pd
import re
from fpdf import FPDF
from datetime import datetime
import os
import logging
import traceback
from collections import Counter


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure upload folder for temporary PDF files
UPLOAD_FOLDER = "temp_pdfs"
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)


def sanitize_text(text):
    """Replace unsupported characters with ASCII equivalents"""
    return text.encode("ascii", "ignore").decode()  # Removes non-ASCII characters


def generate_pdf(
    entity_name,
    entity_scores,
    sentiment_history,
    news_items,
    output_filename="report.pdf",
):
    try:
        output_path = os.path.join(UPLOAD_FOLDER, output_filename)
        pdf = FPDF()
        pdf.set_auto_page_break(auto=True, margin=15)
        page_width = pdf.w - 20

        def get_sentiment_visuals(sentiment):
            # String-based logic
            if isinstance(sentiment, str):
                if sentiment in ["bullish", "Bullish"]:
                    return (0, 200, 0)
                elif sentiment in ["bearish", "Bearish"]:
                    return (255, 0, 0)
                elif sentiment == "neutral":
                    return (255, 204, 0)
            try:
                sentiment_score = float(sentiment)
                if sentiment_score > 0:
                    return (0, 200, 0)
                elif sentiment_score < 0:
                    return (255, 0, 0)
                else:
                    return (255, 204, 0)
            except (ValueError, TypeError):
                return (128, 128, 128)

        # Add the first page
        pdf.add_page()  # Ensure a page is added before any content

        # Set the title
        pdf.set_font("Arial", "B", 16)
        pdf.cell(0, 10, f"{entity_name} Report", ln=True, align="C")
        pdf.ln(3)

        # 1.  Entity Name
        entity_name = f"Entity Name: {entity_name}"  # Replace with dynamic data
        pdf.set_font("Arial", "B", 14)
        pdf.cell(0, 10, entity_name, ln=True)
        pdf.ln(2)

        # Set font
        pdf.set_font("Arial", "B", 12)

        # Column widths
        col_widths = [70, 50]  # Adjust as needed

        # Header Row
        pdf.set_fill_color(200, 200, 200)  # Light gray background for header
        pdf.set_text_color(0, 0, 0)  # Black text
        pdf.cell(col_widths[0], 10, "Metric", border=1, fill=True, align="C")
        pdf.cell(col_widths[1], 10, "Value", border=1, fill=True, align="C")
        pdf.ln()  # Move to the next line

        # Data Rows
        pdf.set_fill_color(255, 255, 255)  # White background for data rows

        # Sentiment Classification
        sentiment = entity_scores["classification"].title()
        sentiment_color = get_sentiment_visuals(sentiment)
        pdf.set_text_color(0, 0, 0)  # Black for label
        pdf.cell(col_widths[0], 10, "Sentiment Classification", border=1, align="L")
        pdf.set_text_color(*sentiment_color)
        pdf.cell(col_widths[1], 10, sentiment, border=1, align="C")
        pdf.ln()

        # Average Sentiment
        avg_sentiment = round(entity_scores["avg_score"], 2)
        avg_sentiment_color = get_sentiment_visuals(avg_sentiment)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(col_widths[0], 10, "Average Sentiment", border=1, align="L")
        pdf.set_text_color(*avg_sentiment_color)
        pdf.cell(col_widths[1], 10, str(avg_sentiment), border=1, align="C")
        pdf.ln()

        # Simple Sentiment
        simple_avg = round(entity_scores["simple_average"], 2)
        simple_avg_color = get_sentiment_visuals(simple_avg)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(col_widths[0], 10, "Simple Sentiment", border=1, align="L")
        pdf.set_text_color(*simple_avg_color)
        pdf.cell(col_widths[1], 10, str(simple_avg), border=1, align="C")
        pdf.ln()

        # Time-decay Sentiment
        time_decay = round(entity_scores["time_decay"], 2)
        time_decay_color = get_sentiment_visuals(time_decay)
        pdf.set_text_color(0, 0, 0)
        pdf.cell(col_widths[0], 10, "Time-decay Sentiment", border=1, align="L")
        pdf.set_text_color(*time_decay_color)
        pdf.cell(col_widths[1], 10, str(time_decay), border=1, align="C")
        pdf.ln()

        # Reset text color
        pdf.set_text_color(0, 0, 0)
        pdf.ln(2)

        # 3. Related Sectors
        # Initialize counters for regions and sectors
        region_counter = Counter()
        sector_counter = Counter()

        def clean_data(data):
            if not data:  # Check if data is empty or None
                return []

            # Remove leading/trailing spaces and normalize multiple spaces
            cleaned_data = [item.strip() for item in data]

            # Split multi-region or multi-sector entries by commas or semicolons, and strip spaces
            split_data = []
            for item in cleaned_data:
                # Use regex to split by comma or semicolon, and remove leading/trailing spaces
                split_data.extend([i.strip() for i in re.split("[,;]", item)])

            return split_data

        def unique_data(cleaned):
            # Use set to ensure uniqueness
            return list(set(cleaned))

        for news in news_items.get("news", []):
            regions = news.get("regions", [])
            sectors = news.get("sectors", [])

            clean_regions = clean_data(regions)
            clean_sectors = clean_data(sectors)

            # Ensure unique regions and sectors for each news item (using set to avoid duplicates within a news item)
            unique_regions = set(clean_regions)
            unique_sectors = set(clean_sectors)

            # Update counters with unique regions and sectors
            region_counter.update(unique_regions)
            sector_counter.update(unique_sectors)

        # Order  common regions and sectors
        top_5_regions = [region for region, count in region_counter.most_common(5)]
        top_5_sectors = [sector for sector, count in sector_counter.most_common(5)]

        print("Top 5 Regions:", top_5_regions)  # Debugging line
        print("Top 5 Sectors:", top_5_sectors)  # Debugging line

        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Related Region & Sectors:", ln=True)

        # Set background color for the header
        pdf.set_fill_color(200, 200, 200)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(page_width, 10, "Region(s):", border=1, ln=True, align="L", fill=True)

        # Reset to normal font and remove background for data
        pdf.set_fill_color(255, 255, 255)  # White background for actual text
        pdf.set_font("Arial", "", 12)
        regions_list_str = ", ".join(top_5_regions) if top_5_regions else "None"
        pdf.multi_cell(page_width, 10, regions_list_str, border=1)

        # Bold "Sector(s):"
        # Set background color for the header
        pdf.set_fill_color(200, 200, 200)
        pdf.set_font("Arial", "B", 12)
        pdf.cell(page_width, 10, "Sector(s):", border=1, ln=True, align="L", fill=True)

        # Reset to normal font and remove background for data
        pdf.set_fill_color(255, 255, 255)  # White background for actual text
        pdf.set_font("Arial", "", 12)
        sectors_list_str = ", ".join(top_5_sectors) if top_5_sectors else "None"
        pdf.multi_cell(page_width, 10, sectors_list_str, border=1)

        # Generate the first chart (price history chart)
        entity_ticker = entity_scores[
            "ticker"
        ]  # Get the ticker symbol from entity_scores
        ticker = yf.Ticker(entity_ticker)  # Use the correct ticker symbol
        hist_data = ticker.history(period="1mo")  # Get 1 month of price data

        if hist_data.empty:
            raise ValueError(f"No historical data available for {entity_name}.")

        # Generate the price history chart
        plt.figure(figsize=(6, 4))
        plt.plot(
            hist_data.index,
            hist_data["Close"],
            label="Closing Price",
            color="blue",
            marker="o",
        )  # Adding markers to the line
        plt.title(f"Price History of {entity_name}")
        plt.xlabel("Date")
        plt.ylabel("Closing Price (USD)")
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the plot as an image
        chart_filename = os.path.join(UPLOAD_FOLDER, f"{entity_name}_price_history.png")
        plt.savefig(chart_filename)
        plt.close()

        current_y = pdf.get_y()  # Get current Y position
        page_height = pdf.h - 20  # PDF page height (excluding margin)

        # Calculate available space for two charts and the gaps between them
        remaining_space = (
            page_height - current_y - 20
        )  # Adjust for some space at the bottom
        chart_height = remaining_space / 1.7  # Divide the space between two charts
        x_position = (
            page_width - chart_height * 2
        ) / 2  # Calculate X position to center the chart

        # Embed the first chart (top chart)
        pdf.set_xy(x_position + 5, current_y)  # Set position for the first chart
        pdf.image(
            chart_filename,
            x=x_position + 5,
            y=pdf.get_y() + 5,
            w=chart_height * 2,
            h=chart_height,
        )  # Place chart below title
        pdf.ln(chart_height + 2)  # Move down after the first chart (spacing)

        # Generate the second chart (e.g., news sentiment chart, or any other chart)
        sentiment_history_data = [
            entry["sentiment_score"] for entry in sentiment_history["sentiment_history"]
        ]
        dates = [entry["date"] for entry in sentiment_history["sentiment_history"]]
        formatted_dates = [date.strftime("%d-%m") for date in dates]

        print("Sentiment History Data:", sentiment_history_data)  # Debugging line
        print("Dates:", formatted_dates)  # Debugging line

        hist_data = pd.DataFrame(
            sentiment_history_data, index=formatted_dates, columns=["Sentiment Score"]
        )

        # For simplicity, using the same chart again (can be replaced with another chart)
        plt.figure(figsize=(6, 4))
        plt.plot(
            hist_data.index,
            hist_data["Sentiment Score"],
            label="Sentiment Score",
            color="black",
        )

        for i in range(len(hist_data)):
            color = "green" if hist_data["Sentiment Score"].iloc[i] >= 0 else "red"
            plt.scatter(
                hist_data.index[i], hist_data["Sentiment Score"].iloc[i], color=color
            )
        plt.title(f"Sentiment History of {entity_name}")

        plt.xlabel("Date")
        plt.ylabel("Sentiment Score")
        plt.xticks(rotation=45)
        plt.tight_layout()

        # Save the second chart as an image
        second_chart_filename = os.path.join(
            UPLOAD_FOLDER, f"{entity_name}_price_history_second.png"
        )
        plt.savefig(second_chart_filename)
        plt.close()

        # Embed the second chart (bottom chart)
        pdf.set_xy(x_position + 5, pdf.get_y())  # Set position for the second chart
        pdf.image(
            second_chart_filename,
            x=x_position + 5,
            y=pdf.get_y() + 5,
            w=chart_height * 2,
            h=chart_height,
        )  # Place chart below title

        # Page 2: Relevant News
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, sanitize_text("Relevant News"), ln=True, align="C")
        pdf.ln(10)

        pdf.set_font("Arial", size=12)
        i = 0
        for news in news_items.get("news", []):
            i += 1
            pdf.set_fill_color(245, 245, 245)
            pdf.set_font("Arial", "B", 12)

            page_width = pdf.w - 20

            title_text = sanitize_text(f"{i}. {news['title']}")
            sentiment = news.get("sentiment", "Not provided")
            score = news.get("score", "N/A")

            if isinstance(score, (int, float)):
                score = f"{score:.2f}"

            sentiment_label = f"{sentiment} | {score}"

            if sentiment == "Positive" or sentiment == "bullish":
                pill_color = (0, 200, 0)
            elif sentiment == "Negative" or sentiment == "bearish":
                pill_color = (255, 0, 0)
            elif sentiment == "Neutral" or sentiment == "neutral":
                pill_color = (255, 204, 0)
            else:
                pill_color = (128, 128, 128)

            pdf.set_font("Arial", "B", 10)
            sentiment_width = pdf.get_string_width(sentiment_label) + 10
            title_width = page_width - sentiment_width - 5

            # Title - Use multi_cell to allow the title to wrap if necessary
            pdf.set_font("Arial", "B", 12)
            pdf.multi_cell(title_width, 10, title_text, align="L", fill=False)

            # Position the sentiment pill next to the title
            pdf.set_xy(
                pdf.get_x() + title_width, pdf.get_y() - 10
            )  # Move to the correct X and Y position

            # Fake pill with padding
            pdf.set_fill_color(*pill_color)
            pdf.set_text_color(255, 255, 255)
            pdf.cell(
                sentiment_width,
                10,
                f"  {sentiment_label}  ",
                border=1,
                ln=1,
                align="C",
                fill=True,
            )

            # Reset colors
            pdf.set_text_color(0, 0, 0)
            pdf.set_fill_color(245, 245, 245)
            pdf.ln(5)

            # Summary
            pdf.set_font("Arial", size=11)
            summary = news.get("summary", "No summary available")
            pdf.multi_cell(0, 8, f"Summary: {sanitize_text(summary)}", 0, "L")
            pdf.ln(1)

            # Publisher & Date
            publisher = news.get("publisher", "Unknown")
            published_date = news.get("published_date", "Unknown")
            meta_info = f"Publisher: {publisher} | Date: {published_date}"
            pdf.set_font("Arial", "I", 10)
            pdf.multi_cell(0, 8, sanitize_text(meta_info), 0, "L")

            # URL
            url = news.get("url", "No URL available")
            pdf.set_text_color(0, 0, 255)
            pdf.multi_cell(0, 8, sanitize_text(url), 0, "L")
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Arial", size=12)
            pdf.ln(5)

            # regions
            regions = news.get("regions", [])
            clean_regions = clean_data(regions)
            unique_regions = unique_data(clean_regions)
            if unique_regions:
                sanitized_regions = [sanitize_text(region) for region in unique_regions]
                pdf.set_font("Arial", "I", 10)

                # Start a new line for tags
                pdf.ln(1)

                # Join the tags with commas and ensure they fit within the page width
                regions_text = ", ".join(sanitized_regions)

                # Split the tags into multiple lines if they overflow the page width
                max_regions_width = pdf.w - 30  # Account for page margins
                if pdf.get_string_width(regions_text) >= max_regions_width:
                    # Use multi_cell to wrap the tags text
                    pdf.multi_cell(0, 8, f"Region(s): {regions_text}", 0, "L")
                else:
                    # Otherwise, just use cell to print the tags in one line
                    pdf.cell(0, 8, f"Region(s): {regions_text}", ln=True, align="L")

                pdf.ln(1)  # Add some spacing after tags

            # sectors
            sectors = news.get("sectors", [])
            clean_sectors = clean_data(sectors)
            unique_sectors = unique_data(clean_sectors)
            if unique_sectors:
                sanitized_sectors = [sanitize_text(sector) for sector in unique_sectors]
                pdf.set_font("Arial", "I", 10)

                # Start a new line for tags
                pdf.ln(1)

                # Join the tags with commas and ensure they fit within the page width
                sectors_text = ", ".join(sanitized_sectors)
                max_sectors_width = pdf.w - 30  # Account for page margins
                if pdf.get_string_width(sectors_text) > max_sectors_width:
                    # Use multi_cell to wrap the tags text
                    pdf.multi_cell(0, 8, f"Sector(s): {sectors_text}", 0, "L")
                else:
                    # Otherwise, just use cell to print the tags in one line
                    pdf.cell(0, 8, f"Sector(s): {sectors_text}", ln=True, align="L")

                pdf.ln(5)  # Add some spacing after tags

        # Footer with timestamp
        pdf.set_y(-25)
        pdf.set_font("Arial", "I", 10)
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        pdf.cell(0, 10, sanitize_text(f"Report generated on: {timestamp}"), 0, 1, "C")

        # Save PDF
        pdf.output(output_path, "F")
        logging.info(f"PDF successfully created: {output_path}")

        return output_path
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}\n{traceback.format_exc()}")
        raise
