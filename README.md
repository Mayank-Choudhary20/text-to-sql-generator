# Text to SQL Query Generator 🚀

A web-based application that converts **natural language text into SQL queries** using Python and Flask. This project is designed to help users interact with databases without needing deep SQL knowledge, making database querying faster and more intuitive.

---

## 🌐 Live Demo

🔗 **Deployment:**

```
https://text-to-sql-generator.onrender.com
```

> ⚠️ Note: The app is hosted on Free Tier, so the first request may take 30–60 seconds if the service is idle.

---

## 📌 Features

* Convert plain English text into SQL queries
* Simple and clean web interface
* Flask-based backend
* Easily extendable logic for complex SQL generation
* Deployed on cloud (Render)

---

## 🛠️ Tech Stack

* **Backend:** Python, Flask
* **Frontend:** HTML, CSS, Jinja2
* **Deployment:** Render
* **Version Control:** Git & GitHub

---

## 📂 Project Structure

```
text-to-sql-generator/
│
├── app.py                 # Main Flask application
├── texttosql.py           # Text to SQL conversion logic
├── requirements.txt       # Project dependencies
├── templates/
│   └── index.html         # Frontend UI
├── static/                # Static files (CSS, JS if added)
└── README.md              # Project documentation
```

---

## ⚙️ Installation & Setup (Local)

### 1️⃣ Clone the repository

```bash
git clone https://github.com/Mayank-Choudhary20/text-to-sql-generator.git
cd text-to-sql-generator
```

### 2️⃣ Create a virtual environment (recommended)

```bash
python -m venv venv
venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux / Mac
```

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Run the application

```bash
python app.py
```

Open your browser and visit:

```
http://127.0.0.1:5000
```

---

## 🚀 Deployment

This project is deployed using **Render Web Services**.

Key deployment configurations:

* Python version: 3.x
* Uses environment variable `PORT`
* Flask app bound to `0.0.0.0`

---

## 🧠 How It Works

1. User enters a natural language query
2. The input is sent to Flask backend
3. `text_to_sql()` function processes the text
4. SQL query is generated and displayed on UI

---

## 📈 Future Enhancements

* Integrate Speech To SQL QUERY Generator.
* Database connection and execution
* Authentication system
* Improved UI with Bootstrap / React
* NLP-based query parsing using ML models

---

## 👨‍💻 Author

**Mayank Choudhary**
📧 Email: [mayankchoudhari123@gmail.com](mailto:mayankchoudhari123@gmail.com)
🔗 GitHub: [https://github.com/Mayank-Choudhary20](https://github.com/Mayank-Choudhary20)

---

## 📄 License

This project is open-source and available under the **MIT License**.

---

⭐ If you like this project, consider giving it a star on GitHub!
