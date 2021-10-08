from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django import forms

from posts.models import Post, Group, Follow

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='Mikhail')
        cls.author = User.objects.create_user(username='Author_Mikhail')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Какой-нибудь заголовок',
            description='Какое-нибудь описание',
            slug='slug',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='Какой-нибудь текст',
            group=cls.group,
        )

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_pages_names = [
            {
                'route': 'posts/index.html',
                'reverse': reverse('posts:index'),
            },
            {
                'route': 'posts/group_list.html',
                'reverse': reverse(
                    'posts:group_posts',
                    kwargs={'slug': PostPagesTests.group.slug}
                ),
            },
            {
                'route': 'posts/profile.html',
                'reverse': reverse(
                    'posts:profile',
                    kwargs={'username': PostPagesTests.user}
                ),
            },
            {
                'route': 'posts/post_detail.html',
                'reverse': reverse(
                    'posts:post_detail',
                    kwargs={'post_id': PostPagesTests.post.id}
                ),
            },
            {
                'route': 'posts/create_post.html',
                'reverse': reverse('posts:create'),
            },
            {
                'route': 'posts/create_post.html',
                'reverse': reverse(
                    'posts:post_edit',
                    kwargs={'post_id': PostPagesTests.post.id}
                ),
            },
        ]
        for templates_pages_name in templates_pages_names:
            reverse_name = templates_pages_name.get('reverse')
            route = templates_pages_name.get('route')
            with self.subTest(reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, route)

    def check_post_method(self, first_object):
        """Метод, проверяющий пост на страницах"""
        post_text_0 = first_object.text
        post_author_0 = first_object.author
        post_group_0 = first_object.group
        post_image_0 = first_object.image
        self.assertEqual(post_text_0, self.post.text)
        self.assertEqual(post_author_0, self.post.author)
        self.assertEqual(post_group_0, self.post.group)
        self.assertEqual(post_image_0.name, self.post.image.name)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = PostPagesTests.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        self.check_post_method(first_object)

    def test_group_list_page_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = PostPagesTests.authorized_client.get(
            reverse(
                'posts:group_posts', kwargs={'slug': PostPagesTests.group.slug}
            )
        )
        first_object = response.context['page_obj'][0]
        self.check_post_method(first_object)
        group_object = response.context['group']
        self.assertEqual(group_object.title, self.group.title)
        self.assertEqual(group_object.description, self.group.description)
        self.assertEqual(group_object.slug, self.group.slug)

        self.check_post_method(first_object)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = PostPagesTests.authorized_client.get(
            reverse(
                'posts:profile', kwargs={'username': PostPagesTests.user})
        )
        first_object = response.context['page_obj'][0]
        self.check_post_method(first_object)
        author_object = response.context['author']
        self.assertEqual(author_object, self.user)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = PostPagesTests.authorized_client.get(
            reverse(
                'posts:post_detail',
                kwargs={'post_id': PostPagesTests.post.id})
        )
        first_object = response.context['post_detail']
        self.check_post_method(first_object)

    def test_create_post_page_show_correct_context(self):
        """Шаблон create сформирован с правильным контекстом."""
        response = PostPagesTests.authorized_client.get(reverse(
            'posts:create')
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_fields = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_fields, expected)

    def test_post_edit_page_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = PostPagesTests.authorized_client.get(
            reverse('posts:post_edit', kwargs={
                    'post_id': PostPagesTests.post.id})
        )
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
            'image': forms.fields.ImageField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_authorized_user_can_follow_author(self):
        """Авторизованный пользователь может подписываться
        на других пользователей."""
        follows_count = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.author.username}
        ))
        last_object = Follow.objects.last()
        self.assertEqual(last_object.user, self.user)
        self.assertEqual(last_object.author, self.author)
        self.assertEqual(Follow.objects.count(), follows_count + 1)

    def test_authorized_user_can_unfollow_author(self):
        """Авторизованный пользователь может  удалять других
        пользователей из подписок."""
        Follow.objects.create(user=self.user, author=self.author)
        count_follows = Follow.objects.count()
        self.authorized_client.get(reverse(
            'posts:profile_unfollow',
            kwargs={'username': self.author.username}
        ))
        self.assertEqual(Follow.objects.count(), count_follows - 1)

    def test_followers_can_see_new_post_of_following_author(self):
        """Новая запись пользователя появляется в ленте тех,
        кто на него подписан."""
        follow_client = User.objects.create_user(username='Author_of_the_post')
        authorized_client_1 = Client()
        authorized_client_1.force_login(follow_client)
        authorized_client_1.get(reverse(
            'posts:profile_follow',
            kwargs={'username': self.user.username}))
        follow_1_index = authorized_client_1.get(reverse('posts:follow_index'))
        follow_1_post = follow_1_index.context['page_obj'][0]
        self.check_post_method(follow_1_post)

    def test_followers_can_not_see_new_post_of_following_author(self):
        """Новая запись пользователя не появляется в ленте тех,
        кто на него не подписан."""
        not_a_follower = User.objects.create_user(username='Capitan_Nemo')
        not_a_follower_authorized_client = Client()
        not_a_follower_authorized_client.force_login(not_a_follower)
        response = not_a_follower_authorized_client.get(reverse(
            'posts:follow_index'))
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='Mikhail')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Какой-нибудь заголовок',
            description='Какое-нибудь описание',
            slug='slug',
        )
        list_of_posts = []
        for post in range(13):
            list_of_posts.append(Post(
                text=f'Пост {post}',
                author=cls.user,
                group=cls.group,
            ))
        Post.objects.bulk_create(list_of_posts)

    def test_first_page_contains_ten_records(self):
        """Первая страница содержит 10 записей."""
        list_of_pages = [
            reverse('posts:index'),
            reverse(
                'posts:group_posts',
                kwargs={'slug': PaginatorViewsTest.group.slug}
            ),
            reverse(
                'posts:profile', kwargs={'username': PaginatorViewsTest.user}
            ),
        ]
        for page in list_of_pages:
            response_first_page = PaginatorViewsTest.authorized_client.get(
                page)
            response_second_page = PaginatorViewsTest.authorized_client.get(
                page + '?page=2')
            self.assertEqual(len(response_first_page.context['page_obj']), 10)
            self.assertEqual(len(response_second_page.context['page_obj']), 3)
