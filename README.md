# IS484-T2
News Screener For Relevant Investment Opportunities

## 📝Requirements

1. Python more than `3.10` and less than `3.11`
2. React version equivalent to `18` and above

## Backend 
- navigate to `\Backend\Backend.md` for more information
- To test the routs for backend, navigate to `\POSTMAN`

## Frontend 

📌 Project Overview

This is a React.js application with a clean and modular structure, following best practices for scalability and maintainability. The app is structured into various folders to separate concerns effectively.

---

📂 Folder Structure

```
/src
│── /components       # Reusable UI components
│── /hooks            # Custom React hooks
│── /pages            # Page-level components
│── /services         # API calls and business logic
│── /styles           # Global and component styles
│── /utils            # Helper functions
│── App.js            # Main app component
│── index.js          # Entry point
│── reportWebVitals.js # Performance reporting
│── setupTests.js     # Test setup
```

---

🔧 Installation & Setup

1. Clone the Repository
```
git clone https://github.com/Shangwee/IS484-T2
cd IS484-T2
```

2. Install Dependencies
```
npm install
```

3. Start the Development Server
```
npm start # The application will be available at http://localhost:3000/
```

4. Build for Production
```
npm run build # This will generate an optimized production build in the build/ folder.
```

---

## 📊 Monitoring & Observability

### Azure Monitor Setup

The project includes an automated monitoring setup script for Azure Kubernetes Service (AKS).

**One-time setup:**

```bash
# Set environment variables
export AKS_RESOURCE_GROUP="your-aks-resource-group"
export AZURE_LOCATION="your-region"  # e.g., eastus
export ALERT_EMAIL="your-email@example.com"

# Run the monitoring setup script
chmod +x scripts/setup-monitoring.sh
./scripts/setup-monitoring.sh
```

This script will:
- Create Azure Log Analytics Workspace
- Enable Container Insights for AKS
- Configure log collection from pods
- Set up basic health monitoring

**Verify setup:**
1. Go to Azure Portal > Monitor > Log Analytics Workspaces
2. Confirm "sentifinance-logs" workspace exists
3. Navigate to your AKS cluster > Insights to view metrics

### CI/CD Observability

**Deployment Notifications:**
- GitHub Actions provides deployment summaries in the workflow UI
- Navigate to Actions > CD Workflow > Summary tab for deployment details
- Enable GitHub notifications in Settings > Notifications for workflow alerts

**Code Coverage Reports:**
- Coverage reports are generated for both backend and frontend on every CI run
- Download coverage artifacts from: Actions > CI Workflow > Artifacts section
- Reports include detailed line-by-line coverage analysis

**Accessing Coverage Reports:**
1. Go to GitHub Actions > CI workflow run
2. Scroll to "Artifacts" section at bottom of page
3. Download "backend-coverage-report" or "frontend-coverage-report"
4. Extract and open `htmlcov/index.html` (backend) or `index.html` (frontend) in browser