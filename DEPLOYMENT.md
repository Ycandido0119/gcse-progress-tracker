# GCSE Progress Tracker - Deployment Guide

## Pre-Deployment Checklist

1. ✅ All code committed to GitHub
2. ✅ Production settings configured
3. ✅ Requirements.txt updated
4. ✅ Build script created
5. ✅ .gitignore configured

## Deployment to Render.com

### Step 1: Prepare Your Repository

```bash
# Copy production files
cp /path/to/settings.py config/settings.py
cp /path/to/requirements.txt requirements.txt
cp /path/to/build.sh build.sh
chmod +x build.sh

# Add and commit
git add .
git commit -m "feat: Add production deployment configuration"
git push origin main
```

### Step 2: Create Render Account

1. Go to https://render.com
2. Click "Get Started for Free"
3. Sign up with GitHub
4. Authorize Render to access your repositories

### Step 3: Create PostgreSQL Database

1. From Render Dashboard, click "New +"
2. Select "PostgreSQL"
3. Configure:
   - Name: `gcse-tracker-db`
   - Database: `gcse_tracker`
   - User: `gcse_user`
   - Region: Choose closest to you
   - Plan: **Free**
4. Click "Create Database"
5. Wait for database to be ready (~2 minutes)
6. **Copy the Internal Database URL** (starts with `postgresql://`)

### Step 4: Create Web Service

1. From Render Dashboard, click "New +"
2. Select "Web Service"
3. Connect your GitHub repository
4. Configure:
   - Name: `gcse-progress-tracker`
   - Region: Same as database
   - Branch: `main`
   - Root Directory: (leave blank)
   - Runtime: **Python 3**
   - Build Command: `./build.sh`
   - Start Command: `gunicorn config.wsgi:application`
   - Plan: **Free**

### Step 5: Set Environment Variables

Click "Advanced" and add these environment variables:

**Required:**
```
SECRET_KEY = [Click "Generate" to create a secure key]
DEBUG = False
ALLOWED_HOSTS = your-app-name.onrender.com
DATABASE_URL = [Paste the Internal Database URL from Step 3]
ANTHROPIC_API_KEY = [Your Anthropic API key]
SITE_URL = https://your-app-name.onrender.com
CSRF_TRUSTED_ORIGINS = https://your-app-name.onrender.com
```

**Optional (Email - can add later):**
```
EMAIL_BACKEND = django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST = smtp.gmail.com
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = your-email@gmail.com
EMAIL_HOST_PASSWORD = your-app-password
```

### Step 6: Deploy!

1. Click "Create Web Service"
2. Render will:
   - Clone your repository
   - Install dependencies
   - Run migrations
   - Collect static files
   - Start the server
3. Wait for deployment (~5-10 minutes)
4. Look for "Your service is live 🎉"

### Step 7: Create Superuser

1. Go to your service dashboard
2. Click "Shell" tab
3. Run:
```bash
python manage.py createsuperuser
```
4. Follow prompts to create admin account

### Step 8: Test Your App

1. Click the URL (https://your-app-name.onrender.com)
2. You should see the login page!
3. Test:
   - ✅ Login page loads
   - ✅ Can create account
   - ✅ Can login
   - ✅ Dashboard loads
   - ✅ Can add subjects
   - ✅ All features work

## Post-Deployment

### Create User Accounts

**For your brother (student):**
1. Go to: https://your-app.onrender.com/admin/
2. Login with superuser credentials
3. Create new User: `student_brother`
4. Create UserProfile with role='student'

**For parents:**
1. Create User account
2. Create UserProfile with role='parent'
3. Link to student account

### Monitor Your App

1. Check logs in Render dashboard
2. Monitor for errors
3. Check database usage

### Free Tier Limitations

**Render Free Tier:**
- ⚠️ App sleeps after 15 minutes of inactivity
- ⚠️ First request after sleep takes ~30 seconds
- ✅ 750 hours/month (enough for one app)
- ✅ 90 days of data retention

**PostgreSQL Free Tier:**
- ✅ 256 MB storage
- ✅ 90 days of data retention
- ⚠️ Database expires after 90 days (backup data!)

### Upgrading (Optional)

To keep app always running:
- Upgrade to Starter ($7/month)
- No sleep, better performance
- Consider after testing

## Troubleshooting

### Build Fails
- Check build logs in Render
- Verify requirements.txt
- Check Python version

### Database Connection Error
- Verify DATABASE_URL is correct
- Check database is running
- Ensure same region

### Static Files Not Loading
- Run `python manage.py collectstatic`
- Check STATIC_ROOT setting
- Verify WhiteNoise middleware

### App Not Accessible
- Check ALLOWED_HOSTS includes your domain
- Verify CSRF_TRUSTED_ORIGINS
- Check service is running

## Backup Strategy

### Database Backups (Important!)

Since free tier deletes after 90 days:

```bash
# Backup database (run monthly)
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql

# Or use Render's backup feature (paid plans)
```

### Code Backups
- ✅ GitHub repository (automatic)
- ✅ Keep local copy

## Maintenance

### Update Application

```bash
# Make changes locally
git add .
git commit -m "Update: description"
git push origin main
```

Render will automatically deploy!

### Run Management Commands

Use Render Shell:
```bash
python manage.py migrate
python manage.py createsuperuser
python manage.py collectstatic
python manage.py send_progress_alerts
```

## Custom Domain (Optional)

1. Buy domain (Namecheap, Google Domains)
2. In Render, add custom domain
3. Update DNS records
4. SSL certificate added automatically

## Support

- Render Docs: https://render.com/docs
- Django Docs: https://docs.djangoproject.com
- Community: Render Discord

---

🎉 **Congratulations! Your app is now live!**

Share the URL with your brother and let him start tracking his GCSE progress!