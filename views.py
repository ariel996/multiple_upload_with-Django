from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from django.utils.datetime_safe import datetime
from django.utils.translation import gettext as _
from django.views.generic import CreateView
from django.urls import reverse_lazy
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_text
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.template.loader import render_to_string
from django.http import JsonResponse, HttpResponseRedirect
from .filters import AnnounceFilter

from django.utils import translation

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import login as auth_login
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group
from django.core.mail import EmailMessage

from .forms import *
from .models import *
from .decorators import unauthenticated_user, allowed_users, prestataire_only
from .functions import account_activation_token
from django.views import View

from django.contrib import messages

# Create your views here.
def signupPage(request):
    return render(request, 'annonces/signup.html')

@unauthenticated_user
def registerPage(request):
    form = CreateUserForm(request.POST)
    if request.method == 'POST':
        if form.is_valid():
            email_subject = 'Activate your account'
            user = form.save(commit=False)
            user.is_active = False
            user.save()
            Profile.objects.create(user=user)
            current_site = get_current_site(request)
            message = render_to_string('annonces/activate_account.html', {
                'user': user,
                'domain': current_site.domain,
                'uid': urlsafe_base64_encode(force_bytes(user.id)),#.decode(),
                'token': account_activation_token.make_token(user),
            })
            to_email = form.cleaned_data.get('email')
            email = EmailMessage(email_subject, message, to=[to_email])
            email.send()
            username = form.cleaned_data.get('username')
            # user type to create its account
            user_group = form.cleaned_data.get('group')
            if user_group is None:
                group = Group.objects.get(name=user_group)
            else:
                group = Group.objects.get(name='user')
            user.groups.add(group)

            messages.success(request, 'We have sent you an email, Please confirm your email address to complete ' + username)
            return redirect('login')
    else:
        form = CreateUserForm()
    return render(request, 'annonces/register.html', {'form': form})

def activate_account(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except(TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return redirect('login')
    else:
        return redirect('signup')

@unauthenticated_user
def loginPage(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user is not None:
            if user.is_active:
                login(request, user)
                return redirect('dashboard')
            else:
                messages.info(request, 'Your account is not activated !!!')
        else:
            messages.info(request, 'Username or password is incorrect')

    context = {}
    return render(request, 'annonces/login.html', context)

@login_required(login_url='login')
def show_profile(request, pk):
    #profile = get_object_or_404(Profile, user_id=pk)
    profile = Profile.objects.get(user_id=pk)
    context = {'profile': profile}
    return render(request, 'annonces/prestataire/profile/show.html', context)

@login_required(login_url='login')
def edit_profile(request, pk):
    # user_profile = Profile.objects.get(user_id=pk)
    # form = ProfileForm(instance=user_profile)
    if request.method == 'POST':
        user_form = UserEditForm(data=request.POST or None, instance=request.user)
        profile_form = ProfileEditForm(data=request.POST or None, instance=request.user.profile, files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            # return redirect('show_profile')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    context = {'user_form': user_form, 'profile_form': profile_form}
    return render(request, 'annonces/prestataire/profile/edit.html', context)

def logoutUser(request):
    logout(request)
    return redirect('home')

# Prestataire view
@login_required(login_url='login')
@prestataire_only
def dashboard(request):
    announce = Annonces.objects.filter(user_id=request.user.id).count()
    product = Products.objects.filter(user_id=request.user.id).count()
    catalogue = Catalogue.objects.filter(user_id=request.user.id).count()
    newsletters = Newsletters.objects.all()
    messages_count = Messages.objects.filter(statut=0).count()
    context = {'announce': announce, 'product': product, 'catalogue': catalogue, 'messages_count': messages_count}
    return render(request, 'annonces/prestataire/dashboard.html', context)

# CATALOGUE PRESTATAIRE
@login_required(login_url='login')
@prestataire_only
def list_catalogue(request):
    catalogues = Catalogue.objects.filter(user_id=request.user.id)
    context = {'catalogues': catalogues}
    return render(request, 'annonces/prestataire/catalogues/index.html', context)

@login_required(login_url='login')
@prestataire_only
def create_catalogue(request):
    form = CatalogueForm()
    if request.method == 'POST' and request.FILES['catalogue_picture']:
        form = CatalogueForm(request.POST, request.FILES)
        if form.is_valid():
            form.nom = request.POST.get('nom')
            form.user_id = request.POST.get('user_id')
            form.catalogue_picture = request.POST.get('catalogue_picture')
            form.save()
            return redirect('list_catalogue')
    # form = CatalogueForm()
    context = {'form': form}
    return render(request, 'annonces/prestataire/catalogues/create.html', context)

@login_required(login_url='login')
@prestataire_only
def edit_catalogue(request, pk):
    catalogue = Catalogue.objects.get(id=pk)
    form = CatalogueForm(instance=catalogue)

    if request.method == 'POST':
        form = CatalogueForm(request.POST, request.FILES, instance=catalogue)
        if form.is_valid():
            form.save()
            return redirect('list_catalogue')
    context = {'form': form, 'catalogue': catalogue}
    return render(request, 'annonces/prestataire/catalogues/edit.html', context)

@login_required(login_url='login')
@prestataire_only
def delete_catalogue(request, pk):
    catalogue = Catalogue.objects.get(id=pk)
    catalogue.delete()
    return redirect('list_catalogue')

# ANNOUNCE PRESTATAIRE
@login_required(login_url='login')
@prestataire_only
def create_announce(request):
    #category = request.category.id
    #form = AnnonceForm(instance=Categories)
    form = AnnonceForm()
    if request.method == 'POST' and request.FILES['annonce_photo']:
        #form = AnnonceForm(request.POST, request.FILES, instance=Categories)
        form = AnnonceForm(request.POST, request.FILES)
        if form.is_valid():
            form.subcategory = request.POST.get('subcategory')
            form.annonce_name = request.POST.get('annonce_name')
            form.annonce_description = request.POST.get('annonce_description')
            form.annonce_photo = request.FILES['annonce_photo']
            form.user = request.POST.get('user')
            form.villes = request.POST.get('ville')
            form.save()
            return redirect('list_announce')

        form = AnnonceForm()
    categories = Categories.objects.all()
    villes = Villes.objects.all()
    context = {'form': form, 'categories': categories, 'villes': villes}
    return render(request, 'annonces/prestataire/announces/create.html', context)


@login_required(login_url='login')
@prestataire_only
def list_announces(request):
    announces = Annonces.objects.all().filter(user_id=request.user.id)
    context = {'announces': announces}
    return render(request, 'annonces/prestataire/announces/index.html', context)

@login_required(login_url='login')
@prestataire_only
def update_announce(request, pk):
    announce = Annonces.objects.get(id=pk)
    form = AnnonceForm(instance=announce)
    if request.method == 'POST':
        form = AnnonceForm(request.POST, request.FILES, instance=announce)
        if form.is_valid():
            form = AnnonceForm(request.POST, request.FILES)
            form.save()
            return redirect('list_announce')
    context = {'form': form, 'announce': announce}
    return render(request, 'annonces/prestataire/announces/edit.html', context)

@login_required(login_url='login')
@prestataire_only
def delete_announce(request, pk):
    annonce = Annonces.objects.get(id=pk)
    annonce.delete()
    return redirect('list_announce')


# PRODUCT PRESTATAIRE
@login_required(login_url='login')
@prestataire_only
def list_products(request):
    products = Products.objects.filter(user_id=request.user.id)
    context = {'products': products}
    return render(request, 'annonces/prestataire/products/index.html', context)

@login_required(login_url='login')
@prestataire_only
def create_product(request):
    user = User.objects.get(id=request.user.id)
    if request.method == 'POST':
        category = Categories.objects.get(id=request.POST.get('category'))
        catalogue = Catalogue.objects.get(id=request.POST.get('catalogue'))
        form = ProductForm(request.POST, request.FILES)
        files = request.FILES.getlist('image[]')
        if form.is_valid():
            product = form.save(commit=False)
            product.user = user
            product.category = category
            product.catalogue = catalogue
            product.product_name = request.POST.get('product_name')
            product.product_price = request.POST.get('product_price')
            product.product_description = request.POST.get('product_description')
            product.product_image = request.FILES['product_image']
            product.save()
            for f in files:
                product_image = ProductImage(request.POST, request.FILES)
                product_image = Product_images(product=product, image=f)
                product_image.save()

            return redirect('list_products')
    else:
        form = ProductForm()
    catalogues = Catalogue.objects.all()
    categories = Categories.objects.all()
    context = {'form': form, 'catalogues': catalogues, 'categories': categories}
    return render(request, 'annonces/prestataire/products/create.html', context)

@login_required(login_url='login')
@prestataire_only
def edit_product(request, pk):
    product = Products.objects.get(id=pk)
    form = ProductForm(instance=product)

    if request.method == 'POST':
        form = ProductForm(request.POST, instance=product)
        if form.is_valid():
            form = ProductForm(request.POST, request.FILES)
            form.save()
            return redirect('list_products')
    context = {'form': form }
    return render(request, 'annonces/prestataire/products/edit.html', context)

@login_required(login_url='login')
@prestataire_only
def delete_product(request, pk):
    product = Products.objects.get(id=pk)
    product.delete()
    return redirect('list_products')

# MESSAGES PRESTATAIRE
@login_required(login_url='login')
@prestataire_only
def presta_show_messages(request):
    messages = Messages.objects.filter(user_id=request.user.id)
    context = {'messages': messages}
    return render(request, 'annonces/prestataire/messages/index.html', context)

@login_required(login_url='login')
def delete_message(request, pk):
    message = Messages.objects.get(id=pk)
    message.delete()
    return redirect('presta_show_messages')

@login_required(login_url='login')
def view_message(request, pk):
    message = Messages.objects.get(id=pk)
    return render(request, 'annonces/prestataire/messages/show.html', {'message': message})

@login_required(login_url='login')
def reply_message(request, pk):
    message = Messages.objects.get(id=pk)
    # form = MessageForm(instance=message)
    # if request.method == 'POST':
    #     form = MessageForm(request.POST, instance=message)
    #     if form.is_valid():
    #         form.save()
    #         return redirect('presta_show_messages')
    context = {'message': message}
    return render(request, 'annonces/prestataire/messages/reply.html', context)

@login_required(login_url='login')
def reply_to_message(request):
    form = MessageForm()
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('presta_show_messages')

@login_required(login_url='login')
def comments(request):
    comments = Comments.objects.all()
    context = {'comments': comments}
    return render(request, 'annonces/prestataire/comments/index.html', context)

@login_required(login_url='login')
def reply_comment(request, pk):
    comment = Comments.objects.get(id=pk)
    return render(request, 'annonces/prestataire/comments/reply.html', comment)

@login_required(login_url='login')
def reply_to_comment(request):
    form = CommentForm()
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('comments')

#User view
@login_required(login_url='login')
def user_page(request):
    context = {}
    return render(request, 'annonces/client/dashboard.html', context)

@login_required(login_url='login')
def user_modify(request, pk):
    user_profile = Profile.objects.get(user_id=pk)
    form = ProfileForm(instance=user_profile)
    if request.method == 'POST':
        if form.is_valid():
            form = ProfileForm(request.POST, request.FILES)
            form.save()
            return redirect('show_profile')
    context = {'profile': user_profile}
    return render(request, 'annonces/client/profile/edit.html', context)

@login_required(login_url='login')
def user_show_profile(request, pk):
    profile = Profile.objects.get(user_id=pk)
    context = {'profile': profile}
    return render(request, 'annonces/client/profile/show.html', context)

@login_required(login_url='login')
def show_messages(request, pk):
    messages = Messages.objects.all().filter(user_id=request.user.id, statut=0)
    message_inbox_count = Messages.objects.all().filter(user_id=request.user.id, statut=0).count()
    message_sent_count = Messages.objects.all().filter(user_id=request.user.id, statut=1).count()
    context = {'messages': messages, 'message_inbox_count': message_inbox_count, 'message_sent_count': message_sent_count}
    return render(request, 'annonces/client/messages/index.html', context)

@login_required(login_url='login')
def sent_messages(request, pk):
    messages = Messages.objects.all().filter(user_id=pk)
    context = {'messages': messages}
    return render(request, 'annonces/client/messages/sent.html', context)

@login_required(login_url='login')
def see_message(request, pk):
    message = Messages.objects.get(id=pk)
    message.statut = 1
    message.save()
    context = {'message': message}
    return render(request, 'annonces/client/messages/show.html', context)


# FRONT PAGE VIEW
def home(request):
    categories = Categories.objects.all()
    questions = Questions.objects.all()
    testimonies = Testimonies.objects.all()
    # announces = Annonces.objects.all()
    # myfilter = AnnounceFilter(request.GET, queryset=announces)
    # announces = myfilter.qs
    context = {'categories': categories,
               'testimonies': testimonies,
               'questions': questions
               }
    return render(request, 'annonces/index.html', context)

def products(request):
    context = {}
    return render(request, 'annonces/produits.html', context)

def annonces(request):
    categories = Categories.objects.all().order_by('-id')
    villes = Villes.objects.all()
    annonces = Annonces.objects.all()
    paginator = Paginator(annonces, 10)
    page = request.GET.get('page')
    try:
        annonces = paginator.page(page)
    except PageNotAnInteger:
        annonces = paginator.page(1)
    except EmptyPage:
        annonces = paginator.page(paginator.num_pages)

    # if page is None:
    #     start_index = 0
    #     end_index = 12
    # else:
    #     (start_index, end_index) = proper_pagination(annonces, index=9)
    # page_range = list(paginator.page_range)[start_index:end_index]
    context = {'annonces': annonces,
               'categories': categories,
               'villes': villes}
    return render(request, 'annonces/annonces.html', context)

def about(request):
    return render(request, 'annonces/about.html')

def contact(request):
    return render(request, 'annonces/contact.html')

def detail_announce(request, pk):
    annonce = get_object_or_404(Annonces, pk=pk)
    comments = Comments.objects.filter(annonce=annonce, reply=None).order_by('-id')
    is_liked = False
    if annonce.likes.filter(id=request.user.id).exists():
        is_liked = True

    if request.method == 'POST':
        comment_form = CommentForm(request.POST or None)
        if comment_form.is_valid():
            content = request.POST.get('content')
            reply_id = request.POST.get('comment_id')
            comment_qs = None
            if reply_id:
                comment_qs = Comments.objects.get(id=reply_id)
            comment = Comments.objects.create(annonce=annonce, user=request.user, content=content, reply=comment_qs)
            comment.save()
            return HttpResponseRedirect(annonce.get_absolute_url())
        else:
            comment_form = CommentForm()
    context = {'annonce': annonce,
               'comments': comments,
               'is_like': is_liked,
               'total_likes': annonce.total_likes()}
    return render(request, 'annonces/single.html', context)


def contact_us(request):
    form = ContactForm()
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('contact')

def send_message(request):
    form = MessageForm()
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Message send successfully')
            return redirect('annonces')

def post_comment(request, pk):
    annonce = get_object_or_404(Annonces, pk=pk)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('detail_announce', id=annonce.id)

def like_announce(request):
    annonce = get_object_or_404(Annonces, id=request.POST.get('id'))
    is_liked = False
    if annonce.likes.filter(id=request.user.id).exists():
        annonce.likes.remove(request.user)
        is_liked = False
    else:
        annonce.likes.add(request.user)
        is_liked = True
    context = {'announce': annonce,
               'is_liked': is_liked,
               'total_likes': annonce.total_likes(),
               }
    if request.is_ajax():
        html = render_to_string('annonces/like_section.html', context, request=request)
        return JsonResponse({'form': html})
    #return HttpResponseRedirect(annonce.get_absolute_url())

def get_subcategories(request):
    category = request.GET.get('category_id')
    subcategories = Subcategories.objects.filter(category=category).order_by('name')
    context = {'subcategories': subcategories}
    return render(request, 'annonces/prestataire/announces/ajax_subcategory.html', context)
    # return JsonResponse(list(subcategories.values('id', 'name')), safe=False)

def search(request):
    category = request.GET.get('category')
    item = request.GET.get('item')
    town = request.GET.get('town')
    ville = Villes.objects.filter(name=town)
    if request.method == 'GET':
        annonces = Annonces.objects.filter(category=category, villes=ville, announce_name=item)
    context = {'annonces': annonces}
    return render(request, 'annonces/search_result.html', context)

def signup_news(request):
    form = NewsletterForm()
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('home')

