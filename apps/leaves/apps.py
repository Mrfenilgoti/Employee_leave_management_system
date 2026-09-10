from django.apps import AppConfig  # 👈 Ensure this import is here

class LeavesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.leaves'  # 👈 Change this from 'leaves' to 'apps.leaves'
