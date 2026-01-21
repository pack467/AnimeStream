import os
import django
import pandas as pd

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.contrib.auth.models import User

EXCEL_PATH = "Tabel Akun User.xlsx"  # taruh file excel ini selevel manage.py

df = pd.read_excel(EXCEL_PATH)

created_count = 0
updated_count = 0
skipped_count = 0

for _, row in df.iterrows():
    username = str(row.get("Nama User", "")).strip()
    email = str(row.get("Email", "")).strip()
    password = str(row.get("Password", "")).strip()

    if not username or username.lower() == "nan":
        skipped_count += 1
        continue

    user, created = User.objects.get_or_create(
        username=username,
        defaults={"email": email if email.lower() != "nan" else ""},
    )

    # update email kalau ada
    if email and email.lower() != "nan" and user.email != email:
        user.email = email

    # set password dari excel (update juga kalau user sudah ada)
    if password and password.lower() != "nan":
        user.set_password(password)

    user.save()

    if created:
        created_count += 1
    else:
        updated_count += 1

print("=== IMPORT SELESAI ===")
print("Created:", created_count)
print("Updated:", updated_count)
print("Skipped:", skipped_count)
