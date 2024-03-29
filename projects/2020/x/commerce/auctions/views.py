from calendar import c, prmonth
from distutils.command.clean import clean
from email.mime import image
from gettext import Catalog
from tracemalloc import start
from unicodedata import category
from xml.etree.ElementTree import Comment
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django import forms
from flask_login import login_required
from django.contrib.auth.decorators import login_required
from django.db.models import Exists, OuterRef
from django.core.exceptions import ObjectDoesNotExist
from numpy import save
from urllib3 import HTTPResponse

from .models import Listing, User, Category, Bid, Watchlist, User_Comment

def index(request):
    return render(request, "auctions/index.html", {
        "listings": Listing.objects.all().order_by("-id"),
    })

def categories(request):
    return render(request, 'auctions/categories.html', {
        'categories': Category.objects.all()
    })

def category_filter(request, cat_id):
    category = Category.objects.get(id=cat_id)
    return render(request, 'auctions/index.html', {
        'listings': Listing.objects.filter(category=category),
        'show_closed': True,
        'category': category
    })


def deactivated(request):
    return render(request, "auctions/deactivated.html", {
        "listings": Listing.objects.all().order_by("-id"),
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")

@login_required(login_url = '/login')
def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")

@login_required(login_url = '/login')
def create(request):
    if request.method == "POST":
        form = CreateListing(request.POST)
        if form.is_valid:
            title = request.POST['title']
            description = request.POST['description']
            starting_bid = request.POST['starting_bid']
            image_url = request.POST['image_url']
            category = Category.objects.get(id = request.POST['category'])
            user = request.user
            new_listing = Listing(title=title, 
                                description=description, 
                                starting_bid=starting_bid, 
                                image=image_url, 
                                category=category, 
                                user=user)
            new_listing.save()
        return HttpResponseRedirect(reverse('index'))
    else:
        return render(request, 'auctions/create.html', {
            'form': CreateListing()
        })

@login_required(login_url = '/login')
def listing(request, listing_id):
    listing = Listing.objects.get(id=listing_id)
    watchlist = Watchlist.objects.filter(user=request.user, listing=listing)
    comments = User_Comment.objects.filter(listing=listing)
    if watchlist:
        in_list = True
    else:
        in_list = False
  
    return render(request, 'auctions/listing.html', {
        'listing': listing,
        'form': idInput(initial={'listing_id': listing_id}),
        "in_list": in_list,
        'bid_form': BidForm(initial={'listing_id': listing_id}),
        'comments': comments,
        'comment_form': CommentForm(initial={'listing_id': listing_id})
    })


@login_required(login_url = '/login')
def watchlist(request):
    if request.method == 'POST':
        watch_form = idInput(request.POST)
        if watch_form.is_valid():
            x = watch_form.cleaned_data
            listing = Listing.objects.get(id=x['listing_id'])

            try:
                it_exists = Exists(Watchlist.objects.get(user=request.user, listing=listing))
            except ObjectDoesNotExist:
                it_exists = False
            if it_exists:
                 return render(request, 'auctions/watchlist.html', {
                 'already': True
                 })
            
            else:
                Watchlist.objects.create(user=request.user, listing=listing)
                return render(request, 'auctions/watchlist.html', {
                'watchlist': Watchlist.objects.all().filter(user = request.user)
                })
        return render(request, 'auctions/error.html', {
            'error': "The form is not valid"
        })
        
    else:
        return render(request, 'auctions/watchlist.html', {
        'watchlist': Watchlist.objects.all().filter(user = request.user)
        })

@login_required(login_url = '/login')
def remove_from_watchlist(request):
    if request.method == 'POST':
        # listing_id = request.POST('value')
        watch_form = idInput(request.POST)
        if watch_form.is_valid():
            x = watch_form.cleaned_data
            listing = Listing.objects.get(id=x['listing_id'])
            Watchlist.objects.filter(user=request.user, listing=listing).delete()
        else:
            return render(request, 'auctions/error.html', {
            'error': "The form is not valid"
        })
    return HttpResponseRedirect(reverse('listing', args=(x['listing_id'],)))

@login_required(login_url = '/login')
def bid(request):
    if request.method == 'POST':
        submitted_bid = BidForm(request.POST)
        if submitted_bid.is_valid():
            bid_amount = submitted_bid.cleaned_data['bid']
            listing_id = submitted_bid.cleaned_data['listing_id']

            # get the listing instance
            listing_instance = Listing.objects.get(id=listing_id)

            # and the values from the instance
            starting_bid = listing_instance.starting_bid
            

            if bid_amount < starting_bid:
                return render(request, 'auctions/error.html', {
                'error': "Your bid is too low"
        })
            else:
                #  else check if there are other bids
                current_bid = listing_instance.bid
                if not current_bid:
                    new_bid = Bid.objects.create(value=bid_amount, user=request.user)
                    new_bid.save()

                    listing_instance.bid = new_bid
                    listing_instance.save()
                    return HttpResponseRedirect(reverse('listing', args=(listing_id,)))

                elif bid_amount <= current_bid.value:
                    return render(request, 'auctions/error.html', {
                    'error': "Your bid is too low"
                })
                else:
                    # create a new bid item from the new hight bid and update the bid in the lisiting model
                    listing_instance.bid = Bid.objects.create(value=bid_amount, user=request.user)
                    listing_instance.save()

                    # delete the old highest bid, to make scalable when we have billions of bids per day
                    current_bid.delete()
                    
                    return HttpResponseRedirect(reverse('listing', args=(listing_id,)))

        else:
            return render(request, 'auctions/error.html', {
                    'error': "Invalid bid"
                })
    else:
        return render(request, 'auctions/error.html', {
                    'error': "Page doesn't exist"
                })

def close_listing(request):
    if request.method == 'POST':
        raw = idInput(request.POST)
        if raw.is_valid():
            cleaned = raw.cleaned_data
            listing_id = cleaned["listing_id"]
            
            # get the model instance of listing and change active
            i = Listing.objects.get(id=listing_id)
            print(f"IS IT ACTIVE?: {i.active}")
            i.active = False
            i.save()
            print(f"AND WHAT ABOUT NOW?: {i.active}")
    return HttpResponseRedirect(reverse('listing', args=(listing_id,)))

def comment(request):
    if request.method == 'POST':
        raw = CommentForm(request.POST)
        if raw.is_valid():
            clean = raw.cleaned_data
            listing_id = clean['listing_id']
            listing = Listing.objects.get(id=listing_id)
            comment = clean['comment']
            i = User_Comment(listing=listing, user=request.user, comment=comment)
            i.save()
            return HttpResponseRedirect(reverse('listing', args=(listing_id,)))
        else:
            return HttpResponse("your comment isn't valid")
    else:
        return HttpResponseRedirect(reverse('index'))


class CreateListing(forms.Form):
    title = forms.CharField(label='Title', max_length=64)
    description = forms.CharField(label="Description", widget=forms.Textarea())
    image_url = forms.URLField(label='Image URL', required=False)
    starting_bid = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'short-input'}), label='Starting bid', max_digits=11, decimal_places=2)
    category = forms.ChoiceField(widget=forms.Select(attrs={'class': 'short-input'}), label='Category', choices=[(x.id, x.category) for x in Category.objects.all()])

class idInput(forms.Form):
    listing_id = forms.IntegerField(widget=forms.HiddenInput())

class BidForm(forms.Form):
    bid = forms.DecimalField(widget=forms.NumberInput(attrs={'class': 'short-input'}), label='', max_digits=11, decimal_places=2)
    listing_id = forms.IntegerField(widget=forms.HiddenInput())

class CommentForm(forms.Form):
    comment = forms.CharField(widget=forms.Textarea(attrs={'class': 'comment-text'}), label='')
    listing_id = forms.IntegerField(widget=forms.HiddenInput())