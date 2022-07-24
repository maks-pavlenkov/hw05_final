import shutil
import tempfile
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.cache import cache
from django import forms
from django.conf import settings
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Post, Group, User, Follow

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostPagesTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user_views')
        cls.group = Group.objects.create(
            title='Test title',
            slug='test_slug',
            description='Test description with many characters'
        )
        cls.post = Post.objects.create(
            text='TEST POST!!!',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        cache.clear()
        self.authorized_client = Client()
        self.authorized_client.force_login(PostPagesTest.user)

    def test_pages_uses_correct_templates(self):
        """URL-адрес использует соответствующий шаблон."""
        group = PostPagesTest.group
        post = PostPagesTest.post
        slug = group.slug
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': (
                reverse('posts:group_list', kwargs={'group': slug})
            ),
            'posts/profile.html': (
                reverse('posts:profile', kwargs={'username': post.author})
            ),
            'posts/post_detail.html': (
                reverse('posts:post_detail', kwargs={'post_id': post.pk})
            ),
            'posts/create_post.html': reverse('posts:create'),
        }
        for template, url in templates_pages_names.items():
            with self.subTest(url=url):
                response = self.authorized_client.get(url)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_obj = response.context['page_obj'][0]
        text = first_obj.text
        author = first_obj.author
        self.assertEqual(text, 'TEST POST!!!')
        self.assertEqual(author.username, 'test_user_views')

    def test_group_show_correct_context(self):
        slug = PostPagesTest.group.slug
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'group': slug}))
        group_obj = response.context['group']
        first_obj_page = response.context['page_obj'][0]
        title = group_obj.title
        text = first_obj_page.text
        author = first_obj_page.author
        self.assertEqual(text, 'TEST POST!!!')
        self.assertEqual(title, 'Test title')
        self.assertEqual(author.username, 'test_user_views')

    def test_profile_show_correct_context(self):
        author = PostPagesTest.user.username
        response = self.authorized_client.get(
            reverse(
                'posts:profile',
                kwargs={'username': author}
            )
        )
        author_obj = response.context['author']
        counted_posts_obj = response.context['counted_posts']
        self.assertEqual(author_obj, PostPagesTest.user)
        self.assertEqual(counted_posts_obj, 1)

    def test_post_detail_show_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTest.post.pk}
            )
        )
        post_obj = response.context['post']
        user_post_obj = response.context['user_posts']
        text = post_obj.text
        author = post_obj.author
        self.assertEqual(text, PostPagesTest.post.text)
        self.assertEqual(author, PostPagesTest.user)
        self.assertEqual(user_post_obj, 1)

    def test_post_create_show_correct_context(self):
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.ModelChoiceField
        }
        response = self.authorized_client.get(reverse('posts:create'))
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        response = self.authorized_client.get(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': PostPagesTest.post.pk}
            )
        )
        posts_obj = response.context['posts']
        text_obj = posts_obj.text
        author_obj = posts_obj.author
        edit_obj = response.context['is_edit']
        self.assertEqual(text_obj, PostPagesTest.post.text)
        self.assertTrue(edit_obj)
        self.assertEqual(author_obj, PostPagesTest.user)


class PagimatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        PAGINATOR_FIXTURES = 15
        cls.user = User.objects.create_user(username='test_user_views')
        cls.group = Group.objects.create(
            title='Test title',
            slug='test_slug',
            description='Test description with many characters'
        )
        for _ in range(PAGINATOR_FIXTURES):
            cls.post = Post.objects.create(
                text='TEST POST!!!',
                author=cls.user,
                group=cls.group
            )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(PagimatorViewsTest.user)

    def test_paginator(self):
        post = PagimatorViewsTest.post
        slug = PagimatorViewsTest.group.slug
        urls = [
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'group': slug}),
            reverse('posts:profile', kwargs={'username': post.author})
        ]
        user = PagimatorViewsTest.authorized_client
        for url in urls:
            with self.subTest(url=url):
                response = user.get(url)
                self.assertEqual(
                    response.context['page_obj'].end_index(), 10)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class ImgTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_user_views')
        cls.group = Group.objects.create(
            title='Test title',
            slug='test_slug',
            description='Test description with many characters'
        )
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            text='TEST POST!!!',
            author=cls.user,
            group=cls.group,
            image=uploaded
        )
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def setUp(self):
        cache.clear()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_index_show_img(self):
        resonse = self.authorized_client.get(reverse('posts:index'))
        self.assertTrue(resonse.context['page_obj'][0].image)

    def test_group_list_show_index(self):
        url = reverse(
            'posts:group_list',
            kwargs={'group': ImgTest.group.slug})
        response = self.authorized_client.get(url)
        self.assertTrue(response.context['page_obj'][0].image)

    def test_profile_show_context(self):
        url = reverse(
            'posts:profile',
            kwargs={'username': self.user.username}
        )
        response = self.authorized_client.get(url)
        self.assertTrue(response.context['page_obj'][0].image)

    def test_profile_show_context(self):
        url = reverse(
            'posts:post_detail',
            kwargs={'post_id': self.post.pk}
        )
        response = self.authorized_client.get(url)
        self.assertTrue(response.context['post'].image)


class AddCommentTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_comments')
        cls.group = Group.objects.create(
            title='Test title',
            slug='test_slug',
            description='Test description with many characters'
        )
        cls.post = Post.objects.create(
            text='TEST POST!!!',
            author=cls.user,
            group=cls.group
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(AddCommentTest.user)

    def test_commenting_users(self):
        pk = AddCommentTest.post.pk
        form_data = {
            'text': 'TEST COMMENT 1'
        }
        response_guest = self.guest_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': pk}),
            data=form_data,
            follow=True
        )
        response_authorized = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(
            response_guest,
            f'/auth/login/?next=/posts/{pk}/comment/'
        )
        self.assertRedirects(response_authorized, f'/posts/{pk}/')

    def test_comment_added(self):
        pk = AddCommentTest.post.pk
        form_data = {
            'text': 'TEST COMMENT 1'
        }
        response_authorized = self.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': pk}),
            data=form_data,
            follow=True
        )
        self.assertEqual(
            response_authorized.context['comments'][0].text,
            form_data['text']
        )

    def test_cache(self):
        Post.objects.all().delete()
        Post.objects.create(
            author=self.user,
            text='Тестовый пост',
            group=self.group,
        )
        response_old = self.guest_client.get(reverse('posts:index'))
        Post.objects.all().delete()
        response_new = self.guest_client.get(reverse('posts:index'))
        html_1 = response_old.content.decode('utf-8')
        html_2 = response_new.content.decode('utf-8')
        self.assertHTMLEqual(html_1, html_2)
        cache.clear()
        response_cache_clear = self.guest_client.get(reverse('posts:index'))
        self.assertNotEqual(response_new, response_cache_clear)


class FollowTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='test_follow')
        cls.user_2 = User.objects.create_user(username='following_1')
        cls.user_3 = User.objects.create_user(username='following_2')
        cls.group = Group.objects.create(
            title='Test title',
            slug='test_slug',
            description='Test description with many characters'
        )
        cls.post_1 = Post.objects.create(
            text='TEST POST!!!',
            author=cls.user_2,
            group=cls.group
        )
        cls.post_2 = Post.objects.create(
            text='TEST POST!!!',
            author=cls.user_3,
            group=cls.group
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.authorized_client_1 = Client()
        self.authorized_client_2 = Client()
        self.authorized_client_1.force_login(FollowTest.user)
        self.authorized_client_2.force_login(FollowTest.user_2)

    def test_authorized_client_can_follow(self):
        self.authorized_client_1.get(
            reverse('posts:profile_follow', args=(self.post_1.author,))
        )
        check_follower = Follow.objects.filter(author=self.user_2)
        self.assertEqual(check_follower[0].author, self.user_2)
        self.authorized_client_1.get(
            reverse('posts:profile_unfollow', args=(self.post_1.author,))
        )
        check_unfollower = Follow.objects.filter(author=self.user_2)
        self.assertFalse(check_unfollower)

    def test_correct_follow(self):
        self.authorized_client_1.get(
            reverse('posts:profile_follow', args=(self.post_1.author,))
        )
        response_index = self.authorized_client_1.get(
            reverse('posts:follow_index')
        )
        author = response_index.context['page_obj'][0].author
        self.assertEqual(author, self.post_1.author)

    def test_not_correct_follow(self):
        response_index_not = self.authorized_client_2.get(
            reverse('posts:follow_index')
        )
        author = response_index_not.context['page_obj'].objectt_list
        self.assertFalse(author)
