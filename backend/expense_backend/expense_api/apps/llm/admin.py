from django.contrib import admin
from expense_api.apps.llm.models import User, Category
# # Register your models here.
admin.site.register(User)
admin.site.register(Category)

