# AniMEStream - Installation Guide

Panduan instalasi project **AniMEStream** (Django) dari awal hingga siap digunakan.

---

## 📋 Requirements

- **Python 3.11+**
- **Git**
- **SQLite** (default, tidak perlu install)

---

## 🚀 Quick Start

### 1. Clone Repository
```bash
git clone <repo-url>
cd animestream
```

### 2. Setup Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

Atau install manual:
```bash
pip install Django pandas openpyxl numpy
```

### 4. Database Migration
```bash
python manage.py makemigrations
python manage.py migrate
```

### 5. Create Superuser (Optional)
```bash
python manage.py createsuperuser
```

### 6. Import Data dari Excel

**Import Anime:**
```bash
python manage.py import_excel_to_db --mode meta --file "Tabel_Anime.xlsx"
```

**Import Ratings:**
```bash
python manage.py import_excel_to_db --mode ratings --file "Data_setelah_pra-processing.xlsx" --create-users
```

### 7. Run Server
```bash
python manage.py runserver
```

Buka browser: `http://127.0.0.1:8000/`

---

## 📁 Project Structure

```
animestream/
├── templates/
│   ├── pages/
│   │   └── search.html
│   ├── home/
│   │   └── home.html
│   ├── watch/
│   │   └── watch.html
│   └── auth/
│       └── login.html
├── static/
│   ├── styles/
│   ├── script/
│   └── images/
├── main/
├── accounts/
└── config/
```

---

## 🔧 Troubleshooting

### TemplateDoesNotExist Error
Pastikan file template ada di `templates/pages/search.html`

### API Search Error (500)
Periksa field model `Anime`:
- Gunakan `year_release` (bukan `year`)
- Gunakan `total_episode` (bukan `episodes`)

### Genre Filter Tidak Akurat
Field `genre` berupa string CSV. Pastikan query menggunakan regex atau split-compare.

---

## 📝 Important URLs

- **Search Page:** `/search/`
- **API Search:** `/api/search/`
- **Home:** `/home/`
- **Watch:** `/watch/<id>/`

---

## ⚙️ Production Notes

- Gunakan `.env` untuk menyimpan `SECRET_KEY` dan kredensial database
- Jangan commit file database SQLite dan dataset Excel ke repository
- Untuk production, gunakan **Gunicorn/Uvicorn + Nginx**

---

## 📦 Generate Requirements

```bash
pip freeze > requirements.txt
```

---

**✅ Setup Complete!** Project siap dijalankan.