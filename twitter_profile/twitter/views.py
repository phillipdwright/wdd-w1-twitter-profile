from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponseForbidden
from django.core.exceptions import PermissionDenied
from django.contrib.auth import logout as django_logout, get_user_model
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.contrib import messages
from django.conf import settings
from django.db.models import Q

from .models import Tweet
from .forms import TweetForm, ProfileForm


@login_required()
def logout(request):
    django_logout(request)
    return redirect('/')

@login_required()
def profile(request):
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=request.user)
        form.fields['username'].disabled = True
        if form.is_valid():
            # Do something to update request.user with the form data
            form.save()
            messages.success(request, 'Profile Updated!')
    
    data = {
        'username': request.user.username,
        'first_name': request.user.first_name,
        'last_name': request.user.last_name,
        'birth_date': request.user.birth_date
    }
    form = ProfileForm(initial=data)
    form.fields['username'].disabled = True
    
    return render(request, 'profile.html', {'form': form})


def home(request, username=None):
    if not request.user.is_authenticated():
        if not username or request.method != 'GET':
            return redirect(settings.LOGIN_URL + '?next=%s' % request.path)

    user = request.user

    if request.method == 'POST':
        if username and username != user.username:
            return HttpResponseForbidden()
        form = TweetForm(request.POST)
        if form.is_valid():
            tweet = form.save(commit=False)
            tweet.user = request.user
            tweet.save()
            messages.success(request, 'Tweet Created!')

    form = TweetForm()

    if username:
        user = get_object_or_404(get_user_model(), username=username)
        form = None
        tweets = Tweet.objects.filter(user=user)
    else:
        users_following = request.user.following
        tweets = Tweet.objects.filter(
            Q(user=user) | Q(user__in=users_following))

    following_profile = (request.user.is_authenticated() and
                         request.user.is_following(user))
    return render(request, 'feed.html', {
        'form': form,
        'twitter_profile': user,
        'tweets': tweets,
        'following_profile': following_profile
    })


@login_required()
@require_POST
def follow(request):
    followed = get_object_or_404(
        get_user_model(), username=request.POST['username'])
    request.user.follow(followed)
    return redirect(request.GET.get('next', '/'))


@login_required()
@require_POST
def unfollow(request):
    unfollowed = get_object_or_404(
        get_user_model(), username=request.POST['username'])
    request.user.unfollow(unfollowed)
    return redirect(request.GET.get('next', '/'))


@login_required()
def delete_tweet(request, tweet_id):
    tweet = get_object_or_404(Tweet, pk=tweet_id)
    if tweet.user != request.user:
        raise PermissionDenied
    tweet.delete()
    messages.success(request, 'Tweet successfully deleted')
    return redirect(request.GET.get('next', '/'))
