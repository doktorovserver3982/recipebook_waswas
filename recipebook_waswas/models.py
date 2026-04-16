from django.contrib.auth.models import AbstractUser
from django.db import models
import uuid
from django.contrib.auth.models import User
from django.conf import settings
from django.db.models.signals import post_save
from django.contrib.auth.models import User
from django.dispatch import receiver
class UserFridge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='fridge_items'
    )

    ingredient = models.ForeignKey(
        'Ingredient',
        on_delete=models.CASCADE,
        related_name='in_fridges'
    )

    quantity = models.FloatField(null=True, blank=True)
    unit = models.CharField(max_length=20, null=True, blank=True)

    expires_at = models.DateField(null=True, blank=True)

    added_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together=('user', 'ingredient')
    def __str__(self):
        return f"{self.user} — {self.ingredient.name}"
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    monthly_budget = models.IntegerField(null=True, blank=True)

    @receiver(post_save, sender=User)
    def create_user_profile(sender, instance, created, **kwargs):
        if created:
            UserProfile.objects.create(user=instance)
class Recipe(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    steps = models.JSONField()
    cook_time_minutes = models.IntegerField()
    servings = models.IntegerField()
    image_url = models.URLField(blank=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def get_total_cost(self):
        total=0

        ingredients=self.recipeingredient_set.all()

        for item in ingredients:
            total+=item.quantity * item.ingredient.price_per_unit

        return round(total, 2)

    def get_cost_per_serving(self):
        if self.servings:
            return round(self.get_total_cost() / self.servings, 2)
        return 0


class SavedRecipe(models.Model):
    user = models.ForeignKey(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='saved_recipes'
    )

    recipe = models.ForeignKey(
        'Recipe',
        on_delete=models.CASCADE,
        related_name='saved_by'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'recipe')

class Ingredient(models.Model):
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=20)
    price_per_unit = models.FloatField()


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(Recipe, on_delete=models.CASCADE)
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    quantity = models.FloatField()