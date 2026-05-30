# 🚀 Phase 5 - Quick Start Guide

## Current Status
✅ **Phase 1 COMPLETE**: Django-React hybrid setup done

## Next Steps (Phase 2)

### 1️⃣ Install Dependencies
```bash
cd /home/minato/projet/frontend
npm install
```

### 2️⃣ Build React App
```bash
npm run build
```

This generates files in `/web/static/dist/`:
```
web/static/dist/
├── js/
│   ├── main-*.js
│   ├── vendor-*.js
│   └── ...
├── css/
│   └── main-*.css
└── assets/
    └── ...
```

### 3️⃣ Test in Django
```bash
cd /home/minato/projet

# Activate virtual env
source mon_env/bin/activate

# Collect static files
python manage.py collectstatic --noinput

# Run server
python manage.py runserver
```

Then visit: **http://localhost:8000**

### 4️⃣ Or Use Development Setup
```bash
cd /home/minato/projet
./start-dev.sh
```

This runs:
- **React (Vite)** on http://localhost:5173
- **Django** on http://localhost:8000
- Both auto-reload on file changes

---

## 🔍 What Should Happen

1. **React compiles** → `/web/static/dist/`
2. **Django loads** → Serves `templates/base.html`
3. **React boots** → Injects into `<div id="root">`
4. **CSRF token** → Auto-included in requests
5. **Session** → Django sessionid cookie used

---

## 🧪 Test It Works

### Via Django Shell
```bash
python manage.py shell

from django.contrib.auth.models import User
user = User.objects.create_user('testuser', 'test@example.com', 'password')
# Now login with testuser/password on the web app
```

### API Test
```bash
curl -X GET http://localhost:8000/api/v1/auth/current-user/ \
  -H "Cookie: sessionid=YOUR_SESSION_ID"
```

---

## 📁 Key Paths

| Path | Purpose |
|------|---------|
| `/home/minato/projet/frontend` | React source code |
| `/home/minato/projet/web/static/dist` | Built React (after npm build) |
| `/home/minato/projet/templates/base.html` | Django template with React root |
| `/home/minato/projet/web/views.py` | Django views |
| `/home/minato/projet/config/urls.py` | URL routing |

---

## 🐛 Troubleshooting

**React not loading?**
```bash
# Check if build exists
ls /home/minato/projet/web/static/dist/js/
```

**CSRF token error?**
Check that `templates/base.html` has:
```html
<meta name="csrf-token" content="{{ csrf_token }}">
```

**Session not working?**
- Ensure login is working (Django admin)
- Check sessionid cookie in browser DevTools
- Verify `credentials: 'same-origin'` in api/client.ts

---

## 📚 Documentation

- **PHASE5_FRONTEND_SETUP.md** - Detailed setup guide
- **PHASE5_COMPLETION.txt** - Comprehensive summary
- **frontend/DOCUMENTATION.md** - React components guide
- **MOBILE_API_REFERENCE.md** - API endpoints

---

## ✅ Phase 2 Checklist

- [ ] `npm install` completed
- [ ] `npm run build` generated files
- [ ] `/web/static/dist/` contains js/css
- [ ] Django loads without errors
- [ ] React appears at http://localhost:8000
- [ ] CSRF token in page source
- [ ] Can login to Django admin
- [ ] API endpoints respond (check CSRF auto-includes)

---

## 🎯 Ready for Phase 3?

Once Phase 2 is complete:
1. Adapt React components to use Django API
2. Connect ProfileSimulationModal to real Django users
3. Replace mock data with API calls
4. Test role-based permissions

---

**Status**: Phase 1 ✅ Complete | Phase 2 🔄 Next | Phase 3-5 ⏳ Pending

