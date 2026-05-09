# 🛒 SmartPantry AI: MLOps Inventory & Nutrition Predictor

**SmartPantry** is an intelligent inventory management system designed for fitness enthusiasts and students. It automates the tracking of household groceries using AI-powered receipt scanning and predicts depletion dates using machine learning, ensuring you never run out of essential protein or supplies.

---

## 🛠️ Tech Stack
*   **Frontend:** Streamlit (Python-based Web Framework)
*   **Backend:** Python 3.10
*   **Database:** MongoDB Atlas (NoSQL)
*   **ML & Vision:** AWS Textract (OCR), Scikit-learn (Forecasting)
*   **Cloud Infrastructure:** AWS (S3, Lambda)
*   **DevOps/MLOps:** GitHub Actions, Model Monitoring, Data Versioning

---

## 🌟 Key Features
- **OCR Receipt Ingestion:** Upload grocery receipts to automatically update stock levels.
- **Dynamic Forecasting:** ML engine that learns your consumption patterns to predict "Days Remaining" for each item.
- **Smart Shopping List:** Context-aware list that prioritizes items based on urgency and nutritional goals.
- **Nutrition Dashboard:** Real-time visibility into available macros (Protein/Calories) in your current inventory.

---

## 📂 Project Structure
```text
SmartPantry/
├── docs/               # Full Product & Technical Documentation
│   └── requirements.md # Detailed system specifications
├── src/                # Source code (Logic, UI, Database connections)
├── data/               # Sample receipts and synthetic data
├── tests/              # Unit tests for ML models and API
└── README.md           # Main project overview