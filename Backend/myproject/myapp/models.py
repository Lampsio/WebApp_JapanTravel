from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models

class CustomUserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('The Email field must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        return self.create_user(email, password, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):
    USER_TYPE_CHOICES = (
        ('User', 'User'),
        ('Guide', 'Guide'),
    )

    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=30, blank=True)
    last_name = models.CharField(max_length=30, blank=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    user_type = models.CharField(max_length=5, choices=USER_TYPE_CHOICES)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class UserProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    city = models.CharField(max_length=100, blank=True, null=True)

class GuideProfile(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE)
    language = models.CharField(max_length=100, default='English')
    bio = models.TextField(null=True, blank=True)

class Reservation(models.Model):
    STATUS_CHOICES = (
        ('Scheduled', 'Scheduled'),
        ('Canceled', 'Canceled'),
        ('Completed', 'Completed'),
    )

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_reservations', limit_choices_to={'user_type': 'User'})
    guide = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='guide_reservations', limit_choices_to={'user_type': 'Guide'})
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    number_of_people = models.PositiveIntegerField(null=False,default=1)
    additional_info = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Scheduled')
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f'Reservation from {self.user.email} with {self.guide.email}'
    
class Rating(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ratings_given')
    guide = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='ratings_received')
    description = models.TextField()
    rating = models.IntegerField(choices=[(i, i) for i in range(1, 6)])
    is_public = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user} rated {self.guide} - {self.rating}/5"
