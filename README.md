# Team3Application

_For Neueda Training 2025_

![Team Banner](https://github.com/user-attachments/assets/3f40d274-93ca-4c32-b6e6-7743bedc8a26)
![App Screenshot](https://github.com/user-attachments/assets/f3bbbcd3-0a31-466f-a61a-2c9706b7338c)

---

## 🚀 Overview

Team3Application is a financial analytics dashboard that leverages AI and real-time data to provide actionable insights, news summaries, and quantitative analysis for stocks.  
Built with Python, Flask, and modern data science tools.

---

## 🛠️ Features

- 📈 Stock price analysis & linear regression
- 📰 AI-powered news summarization
- 🤖 Junior AI analyst recommendations
- 💡 Data-driven investment reasoning
- 💰 DCF fair value estimation

---

## 🌟 What Makes This Application Complex & Cool

This project stands out for its integration of advanced AI and data science techniques:

- **AI-Powered News Summarization:**  
  Uses Hugging Face Transformers (PyTorch backend) to generate concise, investor-focused news summaries. This leverages neural networks trained on vast datasets, providing context-aware, human-like text generation.

- **Prompt Engineering:**  
  Carefully crafted prompts guide the summarization model to produce actionable, relevant insights for investors, not just generic summaries. This demonstrates the power of prompt engineering in extracting domain-specific value from large language models.

- **Quantitative Analysis:**  
  Implements linear regression and DCF (Discounted Cash Flow) models for price prediction and valuation, blending classic finance with modern machine learning.

- **PyTorch & Neural Networks:**  
  The summarization pipeline runs on models built with PyTorch, a leading deep learning framework. This allows the app to harness state-of-the-art neural networks for natural language understanding.

- **Seamless Integration:**  
  Combines real-time data (via Yahoo Finance and NewsAPI), AI-driven insights, and interactive visualizations in a single, user-friendly dashboard.

**In summary:**  
This application is not just a CRUD app or static dashboard—it’s a showcase of how modern AI (transformers, neural networks, prompt engineering) can be combined with traditional finance and web development to deliver real, actionable intelligence for users.

---

## 🏁 Getting Started

### 1. Clone the Repository

```sh
git clone https://github.com/yourusername/Team3Application.git
cd Team3Application/flask-app
```

### 2. Install Dependencies

```sh
pip install -r requirements.txt
```

### 3. Get Your NewsAPI Key

- Sign up at [https://newsapi.org/](https://newsapi.org/) to get a free API key.

### 4. Create a `.env` File

In the `flask-app` directory, create a file named `.env` and add your API key:

```
NEWSAPI_KEY=your_api_key_here
```

You may add other secrets or configuration variables as needed.

### 5. Run the Application

```sh
python app.py
```

---

## 📋 Notes

- **Keep your `.env` file private!**  
  It is excluded from version control via `.gitignore`.
- If you encounter issues with missing modules, ensure all dependencies are installed and your Python environment is activated.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change.

---

## 📄 License

This project is for educational purposes.

---

_Developed by Team 3 for Neueda Training 2025_
