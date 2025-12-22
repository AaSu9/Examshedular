# 🌐 Deploy to PythonAnywhere (FREE - No Credit Card)

Your app will be accessible from **ANY phone, ANYWHERE** with a URL like:
`https://yourusername.pythonanywhere.com`

---

## 📋 Step-by-Step Instructions

### 1️⃣ Create PythonAnywhere Account
1. Go to: https://www.pythonanywhere.com
2. Click **"Pricing & signup"**
3. Choose **"Create a Beginner account"** (100% FREE)
4. Sign up with email (no card needed!)

### 2️⃣ Upload Your Code

**Option A: From GitHub (Recommended)**
1. Your code is already on GitHub: `https://github.com/AaSu9/Examshedular.git`
2. In PythonAnywhere, open a **Bash console** (from Dashboard)
3. Run these commands:
   ```bash
   git clone https://github.com/AaSu9/Examshedular.git
   cd Examshedular
   ```

**Option B: Manual Upload**
1. Click **"Files"** tab
2. Upload all your project files

### 3️⃣ Set Up Web App

1. Go to **"Web"** tab
2. Click **"Add a new web app"**
3. Choose **"Manual configuration"** (not wizard)
4. Select **Python 3.10**

### 4️⃣ Configure WSGI File

1. In the Web tab, find **"Code"** section
2. Click on the **WSGI configuration file** link (e.g., `/var/www/yourusername_pythonanywhere_com_wsgi.py`)
3. **Delete everything** and replace with:

```python
import sys
import os

# Add your project directory to the sys.path
project_home = '/home/yourusername/Examshedular'  # ← Change 'yourusername'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Import your Flask app
from app import app as application
```

4. Click **"Save"**

### 5️⃣ Set Up Static Files

In the Web tab, under **"Static files"**:
- URL: `/static/`
- Directory: `/home/yourusername/Examshedular/static`  ← Change 'yourusername'

### 6️⃣ Install Dependencies

1. Open a **Bash console**
2. Navigate to your project:
   ```bash
   cd Examshedular
   ```
3. Install packages:
   ```bash
   pip3.10 install --user Flask nepali-datetime
   ```

### 7️⃣ Initialize Database

In the same Bash console:
```bash
python3.10 db_init.py
```

### 8️⃣ Launch Your App! 🚀

1. Go back to the **Web** tab
2. Click the big green **"Reload"** button
3. Your app is now live at: `https://yourusername.pythonanywhere.com`

---

## 📱 Install on ANY Phone

1. Open the URL on **any phone** (Android/iPhone)
2. In **Chrome**: Menu → "Add to Home Screen"
3. In **Safari**: Share → "Add to Home Screen"
4. Done! The app works like a native app 🎉

---

## 🔧 Troubleshooting

**If you see errors:**
1. Check the **Error log** in the Web tab
2. Make sure all paths have YOUR username (not `yourusername`)
3. Ensure database file `padsala.db` exists in your project folder

**Need help?** Let me know the error message!

---

## ⚡ Your GitHub Repo
Already pushed! https://github.com/AaSu9/Examshedular.git
