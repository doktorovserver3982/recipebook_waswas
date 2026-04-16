from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST

from .models import Recipe, SavedRecipe, Ingredient
from .models import UserFridge
from django.db.models import Q
from .models import Recipe
from django.contrib.auth.decorators import login_required
from django.db.models import Q

def search_results(request):
    query=request.GET.get('q')
    max_time=request.GET.get('time')
    max_price=request.GET.get('max_price')
    ingredients=request.GET.getlist('ingredients')
    use_fridge=request.GET.get('ingredients_from_fridge')
    sort=request.GET.get('sort')

    all_ingredients=Ingredient.objects.all()
    ingredient_names=request.GET.getlist('ingredients')
    recipes = Recipe.objects.filter(status='published')\
        .prefetch_related('recipeingredient_set__ingredient')

    # it HAS TO BE before the fridge filter at least for now because I don't want to bother figuring this out yet
    if max_time:
        recipes = recipes.filter(cook_time_minutes__lte=max_time)

    # Поиск
    if query:
        recipes = recipes.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query)
        )

    if ingredient_names:
        ingredient_objs=Ingredient.objects.filter(
            name__in=ingredient_names
        )

        ingredient_ids=set(str(i.id) for i in ingredient_objs)

        filtered_recipes=[]

        for recipe in recipes:
            recipe_ids=set(
                str(ri.ingredient_id)
                for ri in recipe.recipeingredient_set.all()
            )

            if ingredient_ids.issubset(recipe_ids):
                filtered_recipes.append(recipe)

        recipes=filtered_recipes
    if use_fridge and request.user.is_authenticated:
        user_ingredients=set(
            UserFridge.objects.filter(user=request.user)
            .values_list('ingredient_id', flat=True)
        )

        filtered_recipes=[]

        for recipe in recipes:
            recipe_ingredients=recipe.recipeingredient_set.all()

            # берём только обязательные ингредиенты
            required_ingredients=[
                ri.ingredient_id
                for ri in recipe_ingredients
                if not getattr(ri, 'is_optional', False)
            ]
            match_count=sum(
                1 for ing in required_ingredients
                if ing in user_ingredients
            )

            ratio=match_count / len(required_ingredients)

            if ratio >= 0.7:  # 70% совпадение
                filtered_recipes.append(recipe)

        recipes=filtered_recipes

    recipes = list(recipes)

    # 🔥 ФИЛЬТР ПО ЦЕНЕ
    if max_price:
        try:
            max_price = float(max_price)
            recipes = [
                r for r in recipes
                if r.get_total_cost() <= max_price
            ]
        except ValueError:
            pass

    # Сортировка
    if sort == 'cheap':
        recipes.sort(key=lambda r: r.get_total_cost())
    elif sort == 'time':
        recipes.sort(key=lambda r: r.cook_time_minutes)
    if request.GET.get('ingredients_from_fridge') and not request.user.is_authenticated:
        recipes=[]
    saved_ids=[]

    if request.user.is_authenticated:
        saved_ids=list(
            request.user.saved_recipes.values_list('recipe_id', flat=True)
        )
    return render(request, 'search_results.html', {
        'recipes': recipes,
        'count': len(recipes),
        'max_price': max_price,
        'all_ingredients': all_ingredients,
        'saved_ids': saved_ids
    })
def home(request):
    query = request.GET.get('q')

    if query:
        recipes = Recipe.objects.filter(
            title__icontains=query,
            status='published'
        )
    else:
        recipes = Recipe.objects.filter(status='published')[:6]
    if request.GET.get('cheap'):
        recipes=sorted(
            recipes,
            key=lambda r: r.get_total_cost()
        )[:10]
    saved_ids=[]

    if request.user.is_authenticated:
        saved_ids=list(
            request.user.saved_recipes.values_list('recipe_id', flat=True)
        )

    return render(request, 'home.html', {
        'recipes': recipes,
        'saved_ids': saved_ids
    })


def save_recipe(request, recipe_id):
    if request.method == 'POST':
        SavedRecipe.objects.create(
            user=request.user,
            recipe_id=recipe_id
        )
    return redirect('home')

from .models import Recipe, RecipeIngredient


def recipe_page(request, recipe_id):
    recipe = Recipe.objects.get(id=recipe_id)
    ingredients = RecipeIngredient.objects.filter(recipe=recipe)
    saved_ids=[]

    if request.user.is_authenticated:
        saved_ids=list(
            request.user.saved_recipes.values_list('recipe_id', flat=True)
        )
    return render(request, 'recipe_page.html', {
        'recipe': recipe,
        'ingredients': ingredients,
        'total_cost': recipe.get_total_cost(),
        'cost_per_serving': recipe.get_cost_per_serving(),
        'saved_ids': saved_ids
    })

from django.shortcuts import render, redirect
from .forms import RegisterForm


def register(request):
    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('/accounts/login/')
    else:
        form = RegisterForm()

    return render(request, 'register.html', {'form': form})

@login_required
def fridge(request):
    items = UserFridge.objects.filter(user=request.user)

    all_ingredients = Ingredient.objects.all()

    return render(request, 'fridge.html', {
        'items': items,
        'all_ingredients': all_ingredients
    })
@login_required
def add_to_fridge(request):
    ingredient_id = request.POST.get('ingredient_id')
    quantity = float(request.POST.get('quantity') or 0)

    ingredient = Ingredient.objects.get(id=ingredient_id)

    obj, created = UserFridge.objects.get_or_create(
        user=request.user,
        ingredient=ingredient
    )

    if not created:
        # если уже есть — увеличиваем количество
        obj.quantity = (obj.quantity or 0) + float(quantity or 0)
    else:
        obj.quantity = quantity

    obj.save()

    return redirect('fridge')

@require_POST
@login_required
def remove_from_fridge(request, item_id):
    item = UserFridge.objects.get(id=item_id, user=request.user)
    item.delete()

    return redirect('fridge')

from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, get_object_or_404
from .models import SavedRecipe, Recipe


@login_required
def toggle_save_recipe(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    obj, created = SavedRecipe.objects.get_or_create(
        user=request.user,
        recipe=recipe
    )

    if not created:
        # уже есть → удалить (toggle)
        obj.delete()

    return redirect(request.META.get('HTTP_REFERER', '/'))

@login_required
def favorites(request):
    saved = SavedRecipe.objects.filter(user=request.user)\
        .select_related('recipe')\
        .prefetch_related('recipe__recipeingredient_set__ingredient')

    recipes = [s.recipe for s in saved]

    return render(request, 'favorites.html', {
        'recipes': recipes
    })