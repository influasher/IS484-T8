import React from "react";
import {
  Box,
  Chip,
  Tooltip,
  Grid,
} from "@mui/material";
import Entity from "./Entity";
import EntityPrice from "../ui/EntityPrice";
import "../../styles/App.css";
import ReportButton from "../ui/export";
import SendPDF from "../ui/SendReport";

const EntityHeader = ({ data }) => {
  const getColor = (sentimentType) => {
    if (sentimentType > 0) return "success";
    if (sentimentType < 0) return "error";
    return "default";
  };

  const EntityName = data ? data.data.name : "N/A";
  const stockID = data ? data.data.id : "N/A";
  const EntityTicker = data ? data.data.ticker : "N/A";

  const sentimentTypes = {
    AvgSentiment: data ? parseFloat(data.data.sentiment_score).toFixed(1) : 0,
    simpleAverage: data ? parseFloat(data.data.simple_average).toFixed(1) : 0,
    TimeDecay: data ? parseFloat(data.data.time_decay).toFixed(1) : 0,
  };

  return (
    <>
      {/* Top Row for Entity and Price & Buttons */}
      <Grid container alignItems="center" justifyContent="space-between">
        {/* Entity on the left */}
        <Grid item>
          <Entity EntityTicker={EntityTicker} />
        </Grid>

        {/* Buttons on the right */}
        <Grid item>
          <Box sx={{ display: "flex", gap: 2 }}>
            <ReportButton EntityName={EntityName} />
            <SendPDF EntityName={EntityName} />
          </Box>
        </Grid>
      </Grid>

      <Grid container alignItems="start">
        <Grid item>
          <EntityPrice id={stockID} />
        </Grid>
      </Grid>

      {/* Sentiment Scores in a Centered Row */}
      <Grid container alignItems="center" justifyContent="space-around">
        <Grid item>
          <Tooltip
            title="Weighted combination of multiple NLP models' sentiment predictions with confidence factored in."
            arrow
            placement="top"
          >
            <Chip
              label={`Confidence Weighted Sentiment Score: ${sentimentTypes.AvgSentiment}`}
              color={getColor(sentimentTypes.AvgSentiment)}
              sx={styles.badge}
            />
          </Tooltip>
        </Grid>

        <Grid item>
          <Tooltip
            title="Direct average of all article sentiment scores without weighting or adjustments."
            arrow
            placement="top"
          >
            <Chip
              label={`Simple Average: ${sentimentTypes.simpleAverage}`}
              color={getColor(sentimentTypes.simpleAverage)}
              sx={styles.badge}
            />
          </Tooltip>
        </Grid>

        <Grid item>
          <Tooltip
            title="Recent articles weighted more heavily than older ones to reflect current market sentiment."
            arrow
            placement="top"
          >
            <Chip
              label={`Time Decay: ${sentimentTypes.TimeDecay}`}
              color={getColor(sentimentTypes.TimeDecay)}
              sx={styles.badge}
            />
          </Tooltip>
        </Grid>
      </Grid>
    </>
  );
};

const styles = {
  badge: {
    fontSize: "1rem",
    padding: "6px 12px",
    borderRadius: "20px",
    fontWeight: "500",
    cursor: "pointer",
    "&:hover": {
      transform: "scale(1.02)",
      transition: "transform 0.2s ease",
    },
  },
};

export default EntityHeader;
