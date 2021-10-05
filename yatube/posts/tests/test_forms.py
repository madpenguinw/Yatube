import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile

from posts.models import Post, Group
from posts.forms import PostForm

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.guest_client = Client()
        cls.user = User.objects.create_user(username='Mikhail')
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)
        cls.group = Group.objects.create(
            title='Какой-нибудь заголовок',
        ),
        Post.objects.create(
            text='Какой-нибудь текст',
            author=cls.user,
        )
        cls.form = PostForm()

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_create_post(self):
        """Проверка создания новой записи в БД
        при отправке валидной формы"""
        posts_count = Post.objects.count()
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
        form_data = {
            'title': 'Тестовый заголовок',
            'text': 'Какой-нибудь текст',
            'image': uploaded,
        }
        response = PostCreateFormTests.authorized_client.post(
            reverse('posts:create'),
            data=form_data,
            follow=True
        )
        last_object = Post.objects.last()
        self.assertEqual(Post.objects.count(), posts_count + 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(last_object.text, form_data['text'])
        self.assertEqual(last_object.author, self.user)
        self.assertTrue(
            Post.objects.filter(
                text='Какой-нибудь текст',
                image='posts/small.gif'
            ).exists()
        )

    def test_edit_post(self):
        """Проверка редактирвоания записи в БД
        при отправке валидной формы"""
        post = Post.objects.create(
            text='Какой-нибудь текст',
            author=PostCreateFormTests.user,
        )
        posts_count = Post.objects.count()
        form_data = {
            'text': 'Какой-нибудь текст',
        }
        response = PostCreateFormTests.authorized_client.post(
            reverse(
                'posts:post_edit',
                kwargs={'post_id': post.id}
            ),
            data=form_data,
            follow=True
        )
        self.assertEqual(Post.objects.last().text, form_data['text'])
        self.assertEqual(Post.objects.count(), posts_count)
        self.assertEqual(response.status_code, 200)

    def test_authorized_user_can_comment(self):
        """Комментировать посты может только авторизованный пользователь"""
        post = Post.objects.create(
            text='Какой-нибудь текст',
            author=PostCreateFormTests.user,
        )
        form_data = {
            'text': 'Какой-нибудь текст',
        }
        no_comment = post.comments.count()
        PostCreateFormTests.authorized_client.post(
            reverse(
                'posts:add_comment',
                kwargs={'post_id': post.id}
            ),
            data=form_data,
        )
        comment = post.comments.get(author=self.user)
        created_comment = post.comments.count()
        self.assertEqual(comment.text, form_data['text'])
        self.assertEqual(no_comment, 0)
        self.assertEqual(created_comment, 1)
