# pyrefly: ignore [missing-import]
from django.contrib import admin
from .models import Department, Program, Teacher, Student, SchoolAdmin

# Register your models here.
admin.site.register(Department)
admin.site.register(Program)
admin.site.register(Teacher)
admin.site.register(Student)
admin.site.register(SchoolAdmin)
