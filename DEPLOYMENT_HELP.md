# How to Deploy Padsala

## Option 1: Temporary Phone Access (WiFi Only)
1. Ensure your PC and Phone are on the same **WiFi Network**.
2. Run the app on your PC:
   ```bash
   python app.py
   ```
   *(I have already updated the code to listen for your phone)*.

3. Find your PC's IP Address:
   - Open Command Prompt and type `ipconfig`.
   - Look for **IPv4 Address** (e.g., `192.168.1.5`).

4. On your Phone:
   - Visit `http://192.168.1.5:5000` (replace with your IP).
   - Use "Add to Home Screen" to install it.

---

## Option 2: Permanent Free Cloud Deployment (Render.com)
To keep the app running 24/7 so you can access it from anywhere (4G/5G):

1. **Push to GitHub**:
   - Create a repo on GitHub.
   - Run in your project folder:
     ```bash
     git init
     git add .
     git commit -m "Deploy"
     git branch -M main
     git remote add origin <YOUR_GITHUB_REPO_URL>
     git push -u origin main
     ```

2. **Deploy on Render**:
   - Go to [render.com](https://render.com) and sign up.
   - Click **"New +"** -> **"Web Service"**.
   - Connect your GitHub repo.
   - **Settings**:
     - **Runtime**: Python 3
     - **Build Command**: `pip install -r requirements.txt`
     - **Start Command**: `gunicorn app:app`
   - Click **"Create Web Service"**.

3. **Done!**
   - Render will give you a URL like `https://padsala.onrender.com`.
   - Open that on your phone and "Install App".
