from django.db import models
from django.contrib.postgres.fields import ArrayField


class VacancyCategory(models.TextChoices):
    DOT_NET = 'NET', '.NET'
    ACCOUNT_MANAGER = 'Account Manager', 'Account Manager'
    AI_ML = 'AI/ML', 'AI/ML'
    ANALYST = 'Analyst', 'Аналітик'
    ANDROID = 'Android', 'Android'
    ANIMATOR = 'Animator', 'Аніматор'
    ARCHITECT = 'Architect', 'Архітектор'
    ARTIST = 'Artist', 'Художник'
    ASSISTANT = 'Assistant', 'Асистент'
    BIG_DATA = 'Big Data', 'Big Data'
    BLOCKCHAIN = 'Blockchain', 'Блокчейн'
    C_PLUS_PLUS = 'C++', 'C++'
    C_LEVEL = 'C-level', 'C-level'
    COPYWRITER = 'Copywriter', 'Копірайтер'
    DATA_ENGINEER = 'Data Engineer', 'Data Engineer'
    DATA_SCIENCE = 'Data Science', 'Data Science'
    DBA = 'DBA', 'DBA'
    DESIGN = 'Design', 'Дизайн'
    DEVOPS = 'DevOps', 'DevOps'
    EMBEDDED = 'Embedded', 'Embedded'
    ENGINEERING_MANAGER = 'Engineering Manager', 'Engineering Manager'
    ERLANG = 'Erlang', 'Erlang'
    ERP_CRM = 'ERP/CRM', 'ERP/CRM'
    FINANCE = 'Finance', 'Фінанси'
    FLUTTER = 'Flutter', 'Flutter'
    FRONT_END = 'Front End', 'Front End'
    GOLANG = 'Golang', 'Golang'
    HARDWARE = 'Hardware', 'Hardware'
    HR = 'HR', 'HR'
    IOS_MACOS = 'iOS/macOS', 'iOS/macOS'
    JAVA = 'Java', 'Java'
    LEGAL = 'Legal', 'Юриспруденція'
    MARKETING = 'Marketing', 'Маркетинг'
    NODE_JS = 'Node.js', 'Node.js'
    OFFICE_MANAGER = 'Office Manager', 'Office Manager'
    OTHER = 'Other', 'Інше'
    PHP = 'PHP', 'PHP'
    PRODUCT_MANAGER = 'Product Manager', 'Product Manager'
    PROJECT_MANAGER = 'Project Manager', 'Project Manager'
    PYTHON = 'Python', 'Python'
    QA = 'QA', 'QA'
    REACT_NATIVE = 'React Native', 'React Native'
    RUBY = 'Ruby', 'Ruby'
    RUST = 'Rust', 'Rust'
    SALES = 'Sales', 'Продажі'
    SALESFORCE = 'Salesforce', 'Salesforce'
    SAP = 'SAP', 'SAP'
    SCALA = 'Scala', 'Scala'
    SCRUM_MASTER = 'Scrum Master', 'Scrum Master'
    SECURITY = 'Security', 'Безпека'
    SEO = 'SEO', 'SEO'
    SUPPORT = 'Support', 'Підтримка'
    SYSADMIN = 'SysAdmin', 'Сисадмін'
    TECHNICAL_WRITER = 'Technical Writer', 'Technical Writer'
    UNITY = 'Unity', 'Unity'
    UNREAL_ENGINE = 'Unreal Engine', 'Unreal Engine'


class Country(models.TextChoices):
    UKRAINE = 'UA', 'Україна'
    EU = 'EU', 'Країни ЄС'


class City(models.TextChoices):
    KYIV = 'Kyiv', 'Київ'
    ODESSA = 'Odessa', 'Одеса'
    KHARKIV = 'Kharkiv', 'Харків'
    DNEPR = 'Dnepr', 'Дніпро'
    LVIV = 'Lviv', 'Львів'
    ZAPORIZHZHIA = 'Zaporizhzhia', 'Запоріжжя'
    KRYVYI_RIH = 'Kryvyi Rih', 'Кривий Ріг'
    MYKOLAIV = 'Mykolaiv', 'Миколаїв'
    MARIUPOL = 'Mariupol', 'Маріуполь'
    LUGANSK = 'Lugansk', 'Луганськ'
    VINNYTSIA = 'Vinnytsia', 'Вінниця'
    SIMFEROPOL = 'Simferopol', 'Сімферополь'
    SEVASTOPOL = 'Sevastopol', 'Севастополь'
    KHMELENYTSKYI = 'Khmelnytskyi', 'Хмельницький'
    CHERNIHIV = 'Chernihiv', 'Чернігів'
    CHERKASY = 'Cherkasy', 'Черкаси'
    SUMY = 'Sumy', 'Суми'
    RIVNE = 'Rivne', 'Рівне'
    POLTAVA = 'Poltava', 'Полтава'
    KROPYVNYTSKYI = 'Kropyvnytskyi', 'Кропивницький'
    TERNOPIL = 'Ternopil', 'Тернопіль'
    UZHHOROD = 'Uzhhorod', 'Ужгород'
    LVIV_REGION = 'Lviv Region', 'Львівська область'
    IVANO_FRANKIVSK = 'Ivano-Frankivsk', 'Івано-Франківськ'
    CHERNIVTSI = 'Chernivtsi', 'Чернівці'
    REMOTE = 'Remote', 'Віддалено'


class Currency(models.TextChoices):
    UAH = 'UAH', '₴'
    USD = 'USD', '$'
    EUR = 'EUR', '€'


class EnglishLevel(models.TextChoices):
    A1 = 'A1', 'A1'
    A2 = 'A2', 'A2'
    B1 = 'B1', 'B1'
    B2 = 'B2', 'B2'
    C1 = 'C1', 'C1'
    C2 = 'C2', 'C2'
    NO_MATTER = 'NO_MATTER', 'Не має значення'


class Vacancy(models.Model):
    class Meta:
        app_label = 'vacancy'

    title = models.CharField(max_length=255, verbose_name="Назва вакансії")
    link = models.URLField(blank=True, null=True, verbose_name="Посилання на вакансію")
    level = models.CharField(max_length=50, blank=True, null=True, verbose_name="Рівень кандидата")
    categories = ArrayField(models.CharField(max_length=100), verbose_name="Категорії", default=list, blank=True)
    countries = ArrayField(models.CharField(max_length=50), verbose_name="Країни", default=list, blank=True)
    cities = ArrayField(models.CharField(max_length=50), verbose_name="Міста", default=list, blank=True)
    location = models.TextField(blank=True, null=True, verbose_name="Локація")
    is_remote = models.BooleanField(default=False, help_text="Чи є вакансія повністю віддаленою?")
    is_hybrid = models.BooleanField(default=False, help_text="Чи є вакансія гібридною?")
    languages = models.TextField(blank=True, null=True, verbose_name="Мови")
    skills = ArrayField(models.CharField(max_length=100), blank=True, default=list, verbose_name="Навички")
    responsibilities = ArrayField(models.TextField(), blank=True, default=list, verbose_name="Обов'язки")
    description = models.TextField(verbose_name="Опис вакансії")
    salary_min = models.PositiveIntegerField(blank=True, null=True, verbose_name="Мінімальна зарплата")
    salary_max = models.PositiveIntegerField(blank=True, null=True, verbose_name="Максимальна зарплата")
    salary_currency = models.CharField(max_length=3, choices=Currency.choices, blank=True, null=True,
                                       verbose_name="Валюта зарплати")
    date = models.DateTimeField(auto_now_add=True, verbose_name="Дата додавання")

    def __str__(self):
        return self.title

    @property
    def salary_range(self):
        if self.salary_min is not None and self.salary_max is not None and self.salary_currency:
            return f"{self.salary_min}-{self.salary_max} {self.get_salary_currency_display()}"
        elif self.salary_min is not None and self.salary_currency:
            return f"від {self.salary_min} {self.get_salary_currency_display()}"
        elif self.salary_max is not None and self.salary_currency:
            return f"до {self.salary_max} {self.get_salary_currency_display()}"
        return None

    @property
    def location(self):
        parts = []
        if self.countries:
            parts.extend([Country(c).label for c in self.countries])
        if self.cities:
            parts.extend([City(c).label for c in self.cities])
        return ", ".join(parts) if parts else "Не вказано"
