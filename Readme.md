# AnimeStream
AniMEStream is a Django-based anime streaming &amp; catalog website with search + filter features, watch pages, user ratings, and a recommendation system using the SVD (collaborative filtering) algorithm to predict anime that users are likely to like.


# AniMEStream - Installation Guide

Panduan instalasi project **AniMEStream** (Django) dari awal hingga siap digunakan.

---

## 📋 Requirements

- **Python 3.11 (Disarankan)**
- **Git bash**
- **MySQL**
- **Dbeaver/Navicat**
- **Visual Studio Code**

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

---

## 🔗 Push ke GitHub Repository

### 1. Konfigurasi Git (Pertama Kali)
```bash
git config --global user.name "Nama Anda"
git config --global user.email "email@example.com"
```

### 2. Inisialisasi Git di Project
```bash
git init
git add .
git commit -m "Initial commit"
```

### 3. Hubungkan dengan GitHub Repository
```bash
git remote add origin https://github.com/pack467/AnimeStream.git
git branch -M main
git push -u origin main
```

### 4. Push Perubahan Selanjutnya
```bash
git add .
git commit -m "Deskripsi perubahan"
git push
```

### Troubleshooting Git

**Jika diminta login GitHub:**
1. Buka VSCode Terminal
2. Saat push pertama kali, akan muncul popup login GitHub
3. Pilih **"Sign in with browser"**
4. Authorize VSCode di browser

**Atau gunakan Personal Access Token:**
1. Buka GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Pilih scope: `repo` (full control)
4. Copy token yang dihasilkan
5. Saat git push, gunakan token sebagai password:
   - Username: `pack467`
   - Password: `<paste-token-disini>`

**Menyimpan kredensial (agar tidak login terus):**
```bash
git config --global credential.helper store
```
