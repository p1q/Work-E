from django.db import models


class Vacancy(models.Model):
    class Meta:
        app_label = 'vacancy'

    title = models.CharField(max_length=255)
    link = models.URLField()
    location = models.CharField(max_length=255)
    salary = models.CharField(max_length=255, blank=True, null=True)
    category = models.CharField(max_length=255)
    date = models.DateTimeField()
    description = models.TextField()

    skills = models.TextField(blank=True, null=True)
    tools = models.TextField(blank=True, null=True)
    responsibilities = models.TextField(blank=True, null=True)
    languages = models.TextField(blank=True, null=True)
    location_field = models.TextField(blank=True, null=True)
    salary_range = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.title
