from django.apps import AppConfig

class LlmConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'expense_api.apps.llm'  # ✅ full dotted path

