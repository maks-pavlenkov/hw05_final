from django.shortcuts import redirect, render, get_object_or_404
from django.views.decorators.cache import cache_page
from django.contrib.auth.decorators import login_required
from .models import Post, Group, User, Comment, Follow
from .forms import PostForm, CommentForm
from .paginator import paginate


@cache_page(20, key_prefix='index_page')
def index(request):
    posts_list = Post.objects.select_related('group')
    page_obj = paginate(request, posts_list)
    context = {
        'page_obj': page_obj
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, group):
    group = get_object_or_404(Group, slug=group)
    posts_list = group.posts.all()
    page_obj = paginate(request, posts_list)
    context = {
        'group': group,
        'page_obj': page_obj
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    if request.user.is_authenticated:
        following = Follow.objects.filter(
            user=request.user,
            author=author).exists()
    else:
        following = False
    user_posts = author.posts.select_related('group')
    counted_posts = user_posts.count()
    page_obj = paginate(request, user_posts)
    context = {
        'author': author,
        'page_obj': page_obj,
        'counted_posts': counted_posts,
        'following': following
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = Post.objects.select_related('group', 'author').get(pk=post_id)
    user = post.author.username
    user_posts = Post.objects.filter(author__username=user).count()
    comments = Comment.objects.all()
    form = CommentForm(request.POST or None)
    context = {
        'form': form,
        'comments': comments,
        'post': post,
        'user_posts': user_posts
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    form = PostForm(request.POST or None, files=request.FILES or None)
    if request.method == 'POST':
        form = PostForm(request.POST, files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', username=request.user.username)
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    posts = Post.objects.get(pk=post_id)
    form = PostForm(
        data=request.POST or None,
        files=request.FILES or None,
        instance=posts)
    if request.user != posts.author:
        return redirect(f'/posts/{post_id}')
    if request.method == 'POST':
        form = PostForm(
            data=request.POST,
            files=request.FILES or None,
            instance=posts)
        if form.is_valid():
            form.save()
            return redirect(f'/posts/{post_id}')
    context = {
        'form': form,
        'posts': posts,
        'is_edit': True
    }
    return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(
        Post.objects.select_related('author', 'group'),
        pk=post_id
    )
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    # информация о текущем пользователе доступна в переменной request.user
    author_list = request.user.follower.all().values_list('author', flat=True)
    posts = Post.objects.select_related().filter(author__in=author_list)
    page_obj = paginate(request, posts)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = get_object_or_404(User, username=username)
    if request.user != author and not Follow.objects.filter(
            user=request.user, author=author).exists():
        Follow.objects.create(user=request.user, author=author)
    return redirect('posts:profile', username=author)


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    Follow.objects.filter(user=request.user, author=author).delete()
    return redirect('posts:profile', username=author)
