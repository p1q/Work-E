from django.db import models
from users.models import User
from vacancy.models import Vacancy


class Match(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='matches')
    vacancy = models.ForeignKey(Vacancy, on_delete=models.CASCADE, related_name='matches')
    score = models.FloatField(help_text="Загальний відсоток співпадіння")
    skills_match = models.FloatField(help_text="Відсоток співпадіння навичок")
    tools_match = models.FloatField(help_text="Відсоток співпадіння інструментів")
    responsibilities_match = models.FloatField(help_text="Відсоток співпадіння обов'язків")
    languages_match = models.FloatField(help_text="Відсоток співпадіння мов")
    location_match = models.FloatField(help_text="Відсоток співпадіння локації")
    salary_match = models.FloatField(help_text="Відсоток співпадіння зарплати")
    match_quality = models.CharField(max_length=20, help_text="Якість співпадіння (Low, Medium, High)")

    def __str__(self):
        return f"Match {self.user} - {self.vacancy} ({self.score:.2f}%)"

    def save(self, *args, **kwargs):
        if self.score >= 80:
            self.match_quality = 'High'
        elif self.score >= 50:
            self.match_quality = 'Medium'
        else:
            self.match_quality = 'Low'
        super().save(*args, **kwargs)
