import React from "react";
import {
  Card,
  CardContent,
  Typography,
  Link as MuiLink,
  Box,
} from "@mui/material";
import SentimentScore from "../ui/Sentimentscore";
import { Link } from "react-router-dom";

// Main News Component
const NewsCard = ({ news }) => {
  return (
    <Card
      sx={{
        p: 2,
        border: "1px solid #ddd",
        borderRadius: "12px",
        backgroundColor: "#fff",
        boxShadow: "0 4px 8px rgba(0, 0, 0, 0.1)",
        transition: "transform 0.3s ease, box-shadow 0.3s ease",
        width: "100%",
        height: "100%",
        display: "flex",
        flexDirection: "column",
        minHeight: "250px", // Reduced from 400px
        "&:hover": {
          transform: "translateY(-2px)",
          boxShadow: "0 8px 16px rgba(0, 0, 0, 0.15)",
        },
      }}
    >
      <CardContent sx={{ p: 0, "&:last-child": { pb: 0 }, flexGrow: 1 }}>
        {/* News Header */}
        <Box sx={{ mb: 1 }}>
          {" "}
          {/* Reduced from mb: 2 */}
          <Typography variant="h6" sx={{ mb: 0.5 }}>
            {" "}
            {/* Reduced from mb: 1 */}
            <MuiLink
              component={Link}
              to="/Individualnewspage"
              state={{ id: news.id, title: news.title }}
              sx={{
                fontSize: "clamp(0.9rem, 2vw, 1.2rem)",
                fontWeight: "bold",
                color: "#1976d2",
                textDecoration: "none",
                "&:hover": {
                  textDecoration: "underline",
                },
              }}
              onClick={() => {
                setSelectedNews(news);
                console.log("Selected News:", news);
              }}
            >
              {news.title}
            </MuiLink>
          </Typography>
          {/* Sentiment Score - aligned to right like in entities */}
          <Box sx={{ display: "flex", justifyContent: "flex-end", mb: 0.5 }}>
            {" "}
            {/* Reduced from mb: 1 */}
            <SentimentScore
              score={news.score}
              sentiment={news.sentiment}
              confidence={news.confidence}
              finbertScore={news.finbert_score}
              secondModelScore={news.gemini_score}
              showDetails={false}
            />
          </Box>
        </Box>

        {/* Publisher and Date */}
        <Typography variant="body2" sx={{ mb: 0.5, color: "#666" }}>
          {" "}
          {/* Reduced from mb: 1 */}
          <strong>Publisher:</strong> {news.publisher}
        </Typography>

        <Typography variant="body2" sx={{ mb: 1, color: "#666" }}>
          {" "}
          {/* Reduced from mb: 2 */}
          <strong>Date:</strong> {new Date(news.published_date).toDateString()}
        </Typography>

        {/* Summary with text clamping like entities */}
        <Typography
          variant="body2"
          sx={{
            fontSize: "clamp(0.8rem, 1.5vw, 1rem)",
            color: "#555555",
            overflow: "hidden",
            textOverflow: "ellipsis",
            display: "-webkit-box",
            WebkitLineClamp: 5, // Increased from 4 to use the saved space
            WebkitBoxOrient: "vertical",
            lineHeight: 1.4, // Slightly tighter line height
          }}
        >
          {news.summary?.length > 300
            ? `${news.summary.slice(0, 300)}...`
            : news.summary}
        </Typography>
      </CardContent>
    </Card>
  );
};

export default NewsCard;
