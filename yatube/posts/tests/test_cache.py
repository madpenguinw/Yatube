from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from django.core.cache import cache

from posts.models import Post, Group

User = get_user_model()


class CacheTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='Mikhail')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Какой-нибудь заголовок',
            description='Какое-нибудь описание',
            slug='slug',
        )
        Post.objects.create(
            author=cls.user,
            text='Какой-нибудь текст',
            group=cls.group,
        )

    def test_cache(self):
        response = CacheTests.authorized_client.get(reverse('posts:index'))
        data = response.content
        post_obj = Post.objects.create(
            author=self.user,
            text='Какой-либо текст',
            group=self.group,
        )
        new_response = CacheTests.authorized_client.get(reverse('posts:index'))
        new_data = new_response.content
        self.assertEqual(data, new_data)
        post_obj.delete()
        Post.objects.create(
            author=self.user,
            text='Какой-то текст',
            group=self.group,
        )
        response_after_deletion = CacheTests.authorized_client.get(reverse(
            'posts:index'))
        data_after_deletion = response_after_deletion.content
        self.assertEqual(new_data, data_after_deletion)
        cache.clear()
        response_after_cleansing = CacheTests.authorized_client.get(reverse(
            'posts:index'))
        data_after_cleansing = response_after_cleansing.content
        self.assertNotEqual(data_after_deletion, data_after_cleansing)
