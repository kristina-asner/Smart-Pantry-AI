# 🥑 Smart Pantry AI

**Smart Inventory Management with AI-Powered Insights**

Smart Pantry AI is a full-stack web application designed to help users manage their home food inventory, reduce waste, and optimize nutrition. The app tracks expiration dates, predicts consumption patterns using Machine Learning, and suggests recipes based on real-time stock using Google's Gemini AI.

## 🚀 Features
*   **Secure Authentication:** User login/signup system with encrypted passwords (bcrypt) and persistent sessions using cookies.
*   **AI Receipt Scanner:** Automatically add items to your pantry by scanning grocery receipts using Computer Vision.
*   **Smart Forecast:** Linear Regression models predict when an item will run out based on your consumption history.
*   **AI Chef:** Get personalized, high-protein recipe suggestions based on your current pantry contents, powered by Gemini 3.1 Flash-Lite.
*   **Interactive Analytics:** Visual consumption charts using Plotly to track your food usage.
*   **Shopping List Integration:** Automatic alerts and one-click "Move to Shopping List" for out-of-stock items.

## 🛠️ Tech Stack
*   **Frontend:** Streamlit
*   **Backend:** Python
*   **Database:** MongoDB Atlas (NoSQL)
*   **AI/ML:** Google Gemini API (GenAI), Scikit-learn
*   **Data Viz:** Plotly, Pandas

## 📦 Installation & Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/kristina-asner/Smart-Pantry-AI.git
   cd Smart-Pantry-AI
