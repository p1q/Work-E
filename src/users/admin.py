from django.contrib import admin
from .models import User, PersonalInfo, Experience, Education, Course, Language

admin.site.register(User)
admin.site.register(PersonalInfo)
admin.site.register(Experience)
admin.site.register(Education)
admin.site.register(Course)
admin.site.register(Language)
