# 🚀 Project Name

A hybrid backend project using **Django** and **FastAPI**.

* Django → Admin panel, ORM, core backend
* FastAPI → High-performance APIs

---

## 📁 Project Structure

```
project/
│
├── django_app/      # Django project
├── fastapi_app/     # FastAPI app
├── requirements.txt
├── .gitignore
└── README.md
```

---

## ⚙️ Setup Instructions

### 1️⃣ Clone the repository

```bash
git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name
```

---

### 2️⃣ Create virtual environment

```bash
python -m venv venv
```

Activate it:

* Windows:

```bash
venv\Scripts\activate
```

* Mac/Linux:

```bash
source venv/bin/activate
```

---

### 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## ▶️ Running the Project

### 🔹 Run Django Server

```bash
python manage.py migrate
python manage.py runserver
```

👉 Django will run at:
http://127.0.0.1:8000/

---

### 🔹 Run FastAPI Server

```bash
uvicorn main:app --reload
```

👉 FastAPI will run at:
http://127.0.0.1:8001/

👉 API Docs:
http://127.0.0.1:8001/docs

---

## 🔐 Environment Variables

Create a `.env` file in the root directory:

```
SECRET_KEY=your_secret_key
DEBUG=True
```

---

## 📦 Requirements

Main dependencies:

* Django
* FastAPI
* Uvicorn
* Pydantic

Install all using:

```bash
pip install -r requirements.txt
```

---

## 🧠 Notes

* Do not commit:

  * `venv/`
  * `.env`
  * `__pycache__/`

* Make sure migrations are handled properly in Django

---

## 🤝 Contributing

1. Fork the repo
2. Create a new branch
3. Commit your changes
4. Push and create a PR

---

## 📄 License

This project is licensed under the MIT License.

---

## 👨‍💻 Author

Your Name
