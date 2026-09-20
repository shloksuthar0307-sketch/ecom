import os

filepath = 'ecommerce/settings.py'
with open(filepath, 'r') as f:
    content = f.read()

# 1. Update DEBUG
content = content.replace("DEBUG = True", "DEBUG = 'RENDER' not in os.environ")

# 2. Update ALLOWED_HOSTS
if "ALLOWED_HOSTS = []" in content:
    content = content.replace(
        "ALLOWED_HOSTS = []",
        """ALLOWED_HOSTS = []
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME')
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)"""
    )

# 3. Add Whitenoise middleware
if "whitenoise.middleware.WhiteNoiseMiddleware" not in content:
    content = content.replace(
        "'django.middleware.security.SecurityMiddleware',",
        "'django.middleware.security.SecurityMiddleware',\n    'whitenoise.middleware.WhiteNoiseMiddleware',"
    )

# 4. Add Database configuration for production
if "import dj_database_url" not in content:
    # Find DATABASES dict
    import re
    db_pattern = r"(DATABASES = \{\s*'default': \{.*?\s*\}\s*\})"
    replacement = """DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

import dj_database_url
db_from_env = dj_database_url.config(conn_max_age=500)
if db_from_env:
    DATABASES['default'].update(db_from_env)"""
    content = re.sub(db_pattern, replacement, content, flags=re.DOTALL)

with open(filepath, 'w') as f:
    f.write(content)

print("settings.py updated successfully!")
