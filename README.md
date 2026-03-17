# 📊 PhonePe Transaction Insights

Analyzed PhonePe transaction, user, and insurance data using SQL and Streamlit. Built interactive dashboards with state/district insights, growth trends, and category analysis. Includes maps and KPIs to identify top performers and growth opportunities across regions.

---

## 📌 Project Overview

This project analyzes PhonePe digital payment data to understand transaction trends, user engagement, and insurance adoption across India. The dataset was cloned from GitHub, processed into structured tables, and visualized using an interactive Streamlit dashboard.

---

## ⚙️ Workflow / Architecture

GitHub Dataset

↓

VS Code (Cloning & Extraction)

↓

Data Cleaning & Transformation

↓

Structured into 9 Tables

↓

MySQL Database (phonepe)

↓

Streamlit Application

↓

Interactive Dashboard (Home + 5 Scenarios)


---

## 🗂️ Database Tables

- aggregated_transaction  
- aggregated_user  
- aggregated_insurance  
- map_transaction  
- map_user  
- map_insurance  
- top_transaction  
- top_user  
- top_insurance  

---

## 🧠 Application Structure
streamlit_app.py → Navigation Controller
Home_Page.py → Overview Dashboard
Scenario_1.py → Transaction Analysis
Scenario_2.py → Device & User Engagement
Scenario_3.py → Insurance Growth Analysis
Scenario_4.py → User Engagement Strategy
Scenario_5.py → Insurance Engagement Analysis


---

## 🚀 Key Features

- 📍 State & district-level analysis  
- 📈 Growth trends (quarter & yearly)  
- 🧾 Payment category insights  
- 🛡️ Insurance penetration analysis  
- 📊 KPI-driven dashboards  
- 🗺️ Interactive maps and visualizations  

---

## 🛠️ Tech Stack

- Python (Pandas, Plotly)  
- Streamlit  
- MySQL  
- VS Code  

---

## ▶️ Run the App

```bash
streamlit run streamlit_app.py
