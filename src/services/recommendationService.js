import { apiClient } from './api';

class RecommendationService {
    /**
     * Get recommendations for a specific client
     */
    async getClientRecommendations(clientId, limit = 10) {
        const response = await apiClient.get(`/recommendations/client/${clientId}?limit=${limit}`);
        return response.data;
    }

    /**
     * Get portfolio health assessment for a client
     */
    async getClientPortfolioHealth(clientId) {
        const response = await apiClient.get(`/recommendations/client/${clientId}/health`);
        return response.data;
    }

    /**
     * Get comprehensive report (recommendations + health)
     */
    async getClientComprehensiveReport(clientId, limit = 10) {
        const response = await apiClient.get(`/recommendations/client/${clientId}/report?limit=${limit}`);
        return response.data;
    }

    /**
     * Generate and download PDF recommendation report
     */
    async generateClientPDFReport(clientId, clientName = 'client') {
        const response = await apiClient.get(`/recommendations/client/${clientId}/pdf`, {
            responseType: 'blob'
        });

        // Handle PDF download
        const blob = response.data;
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;

        // Generate filename with current date
        const timestamp = new Date().toISOString().split('T')[0];
        link.download = `${clientName.replace(/\s+/g, '_')}_recommendations_${timestamp}.pdf`;

        // Trigger download
        document.body.appendChild(link);
        link.click();
        link.remove();
        window.URL.revokeObjectURL(url);

        return { success: true, message: 'PDF downloaded successfully' };
    }

    /**
     * Utility method to format recommendation data for display
     */
    formatRecommendationsForDisplay(recommendations) {
        return recommendations.map(rec => ({
            ...rec,
            formattedSentimentScore: rec.sentiment_score?.toFixed(1),
            formattedConfidence: (rec.recommendation_confidence * 100)?.toFixed(0),
            formattedAmount: rec.suggested_amount?.toLocaleString(),
            formattedAllocation: rec.suggested_allocation_percent?.toFixed(1),
            formattedPrice: rec.current_price?.toFixed(2),
            actionColor: rec.action === 'BUY' ? '#4caf50' : '#f44336',
            riskColor: this.getRiskColor(rec.risk_level)
        }));
    }

    /**
     * Get color code for risk level
     */
    getRiskColor(riskLevel) {
        const colors = {
            'LOW': '#4caf50',
            'MODERATE': '#ff9800',
            'HIGH': '#f44336'
        };
        return colors[riskLevel] || '#9e9e9e';
    }

    /**
     * Get color code for portfolio health score
     */
    getHealthScoreColor(score) {
        if (score >= 80) return '#4caf50';
        if (score >= 60) return '#ff9800';
        return '#f44336';
    }

    /**
     * Format portfolio health data for display
     */
    formatPortfolioHealthForDisplay(healthData) {
        if (!healthData) return null;

        return {
            ...healthData,
            healthScoreColor: this.getHealthScoreColor(healthData.overall_health_score),
            formattedHealthScore: healthData.overall_health_score?.toFixed(1),
            cashAnalysis: {
                ...healthData.cash_analysis,
                formattedCash: healthData.cash_analysis?.available_cash?.toLocaleString(),
                formattedPercent: healthData.cash_analysis?.cash_percent?.toFixed(1)
            }
        };
    }
}

// Export singleton instance
export const recommendationService = new RecommendationService();
export default recommendationService;