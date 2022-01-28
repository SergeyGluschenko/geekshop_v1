import random

from django.conf import settings
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from basketapp.models import Basket

from .models import Contact, Product, ProductCategory


def main(request):
    title = "главная"
    products = Product.objects.filter(is_active=True, category__is_active=True)[:3]
    content = {"title": title, "products": products, "media_url": settings.MEDIA_URL}
    return render(request, "mainapp/index.html", content)


def get_basket(user):
    if user.is_authenticated:
        return Basket.objects.filter(user=user)
    else:
        return []


def get_hot_product():
    products = Product.objects.filter(is_active=True, category__is_active=True)
    return random.sample(list(products), 1)[0]


def get_same_products(hot_product):
    same_products = Product.objects.filter(category=hot_product.category, is_active=True).exclude(pk=hot_product.pk)[:3]
    return same_products


def products(request, pk=None, page=1):
    title = "продукты"
    links_menu = ProductCategory.objects.filter(is_active=True)
    basket = get_basket(request.user)

    if pk is not None:
        if pk == '0':
            category = {"pk": 0, "name": "все"}
            products = Product.objects.filter(is_active=True, category__is_active=True).order_by("price")
        else:
            category = get_object_or_404(ProductCategory, pk=pk)
            products = Product.objects.filter(category__pk=pk, is_active=True, category__is_active=True).order_by(
                "price"
            )

        paginator = Paginator(products, 2)
        try:
            products_paginator = paginator.page(page)
        except PageNotAnInteger:
            products_paginator = paginator.page(1)
        except EmptyPage:
            products_paginator = paginator.page(paginator.num_pages)

        content = {
            "title": title,
            "links_menu": links_menu,
            "category": category,
            "products": products_paginator,
            "media_url": settings.MEDIA_URL,
            "basket": basket,
        }
        return render(request, "mainapp/products_list.html", content)
    hot_product = get_hot_product()
    same_products = get_same_products(hot_product)
    content = {
        "title": title,
        "links_menu": links_menu,
        "same_products": same_products,
        "media_url": settings.MEDIA_URL,
        "basket": basket,
        "hot_product": hot_product,
    }
    return render(request, "mainapp/products.html", content)


def product(request, pk):
    title = "продукты"
    content = {
        "title": title,
        "links_menu": ProductCategory.objects.filter(is_active=True),
        "product": get_object_or_404(Product, pk=pk),
        "basket": get_basket(request.user),
        "media_url": settings.MEDIA_URL,
    }
    return render(request, "mainapp/product.html", content)


from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import HttpResponseRedirect, get_object_or_404, render
from django.template.loader import render_to_string
from django.urls import reverse


from basketapp.models import Basket
from mainapp.models import Product



@login_required
def basket(request):
    title = "корзина"
    basket_items = Basket.objects.filter(user=request.user).order_by("product__category")
    content = {"title": title, "basket_items": basket_items, "media_url": settings.MEDIA_URL}
    return render(request, "basketapp/basket.html", content)


@login_required
def basket_add(request, pk):
    if "login" in request.META.get("HTTP_REFERER"):
        return HttpResponseRedirect(reverse("products:product", args=[pk]))

    product = get_object_or_404(Product, pk=pk)
    basket = Basket.objects.filter(user=request.user, product=product).first()

    if not basket:
        basket = Basket(user=request.user, product=product)

    basket.quantity += 1
    basket.save()

    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))

  
@login_required
def basket_remove(request, pk):
    basket_record = get_object_or_404(Basket, pk=pk)
    basket_record.delete()
    return HttpResponseRedirect(request.META.get("HTTP_REFERER"))


@login_required
def basket_edit(request, pk, quantity):
    if request.is_ajax():
        print(f"{pk} - {quantity}")
        new_basket_item = Basket.objects.get(pk=int(pk))

        if quantity > 0:
            new_basket_item.quantity = quantity
            new_basket_item.save()
        else:
            new_basket_item.delete()

        basket_items = Basket.objects.filter(user=request.user).order_by("product__category")

        content = {"basket_items": basket_items, "media_url": settings.MEDIA_URL}

        result = render_to_string("basketapp/includes/inc_basket_list.html", content)

        return JsonResponse({"result": result})


def contact(request):
    title = "о нас"
    visit_date = timezone.now()
    locations = Contact.objects.all()
    content = {"title": title, "visit_date": visit_date, "locations": locations}
    return render(request, "mainapp/contact.html", content)