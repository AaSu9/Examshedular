import os
import django

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'padsala_project.settings')
django.setup()

from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def create_social_app():
    # 1. Ensure the default site exist or use ID 1
    site, created = Site.objects.get_or_create(id=1, defaults={'domain': 'aashish22.pythonanywhere.com', 'name': 'Padsala'})
    
    # 2. Check if Google app exists
    if not SocialApp.objects.filter(provider='google').exists():
        app = SocialApp.objects.create(
            provider='google',
            name='Google Login',
            client_id='PLACEHOLDER_CLIENT_ID',
            secret='PLACEHOLDER_SECRET',
        )
        app.sites.add(site)
        print("Successfully created Google SocialApp placeholder. You can now edit it in the /admin/")
    else:
        print("Google SocialApp already exists.")

if __name__ == "__main__":
    create_social_app()
