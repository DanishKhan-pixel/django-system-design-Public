from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase
import shutil
import tempfile

from .models import Bookmark, Category, Comment, Like, Post, Tag


User = get_user_model()
TEST_MEDIA_ROOT = tempfile.mkdtemp()


class BlogModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='StrongPass123!',
        )

    def test_category_generates_slug(self):
        category = Category.objects.create(name='Django Tutorials')

        self.assertEqual(category.slug, 'django-tutorials')

    def test_tag_generates_slug(self):
        tag = Tag.objects.create(name='REST API')

        self.assertEqual(tag.slug, 'rest-api')

    def test_post_generates_slug(self):
        post = Post.objects.create(
            author=self.user,
            title='My First Blog Post',
            content='This is the post body.',
        )

        self.assertEqual(post.slug, 'my-first-blog-post')

    def test_duplicate_slugs_get_unique_suffixes(self):
        first = Post.objects.create(
            author=self.user,
            title='Same Title',
            content='First body.',
        )
        second = Post.objects.create(
            author=self.user,
            title='Same Title',
            content='Second body.',
        )

        self.assertEqual(first.slug, 'same-title')
        self.assertEqual(second.slug, 'same-title-2')

    def test_duplicate_category_names_are_not_allowed(self):
        Category.objects.create(name='Backend')

        with self.assertRaises(IntegrityError):
            Category.objects.create(name='Backend')

    def test_published_at_can_be_set_for_published_post(self):
        published_time = timezone.now()
        post = Post.objects.create(
            author=self.user,
            title='Published Post',
            content='Published body.',
            status=Post.Status.PUBLISHED,
            published_at=published_time,
        )

        self.assertEqual(post.status, Post.Status.PUBLISHED)
        self.assertEqual(post.published_at, published_time)

    def test_comment_belongs_to_post_and_user(self):
        post = Post.objects.create(
            author=self.user,
            title='Commented Post',
            content='Post body.',
            status=Post.Status.PUBLISHED,
        )
        comment = Comment.objects.create(
            post=post,
            user=self.user,
            body='Nice post.',
        )

        self.assertEqual(comment.post, post)
        self.assertEqual(comment.user, self.user)
        self.assertEqual(post.comments.count(), 1)
        self.assertEqual(self.user.comments.count(), 1)

    def test_like_belongs_to_post_and_user(self):
        post = Post.objects.create(
            author=self.user,
            title='Liked Post',
            content='Post body.',
            status=Post.Status.PUBLISHED,
        )
        like = Like.objects.create(post=post, user=self.user)

        self.assertEqual(like.post, post)
        self.assertEqual(like.user, self.user)
        self.assertEqual(post.likes.count(), 1)
        self.assertEqual(self.user.likes.count(), 1)

    def test_duplicate_likes_are_prevented(self):
        post = Post.objects.create(
            author=self.user,
            title='Unique Like Post',
            content='Post body.',
            status=Post.Status.PUBLISHED,
        )
        Like.objects.create(post=post, user=self.user)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Like.objects.create(post=post, user=self.user)

    def test_bookmark_belongs_to_post_and_user(self):
        post = Post.objects.create(
            author=self.user,
            title='Bookmarked Post',
            content='Post body.',
            status=Post.Status.PUBLISHED,
        )
        bookmark = Bookmark.objects.create(post=post, user=self.user)

        self.assertEqual(bookmark.post, post)
        self.assertEqual(bookmark.user, self.user)
        self.assertEqual(post.bookmarks.count(), 1)
        self.assertEqual(self.user.bookmarks.count(), 1)

    def test_duplicate_bookmarks_are_prevented(self):
        post = Post.objects.create(
            author=self.user,
            title='Unique Bookmark Post',
            content='Post body.',
            status=Post.Status.PUBLISHED,
        )
        Bookmark.objects.create(post=post, user=self.user)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Bookmark.objects.create(post=post, user=self.user)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class BlogPostAPITests(APITestCase):
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.author = User.objects.create_user(
            username='author',
            email='author@example.com',
            password='StrongPass123!',
        )
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='StrongPass123!',
        )
        self.category = Category.objects.create(name='Django')
        self.tag = Tag.objects.create(name='API')
        self.published_post = Post.objects.create(
            author=self.author,
            title='Published Post',
            content='This post is visible to everyone.',
            excerpt='Visible excerpt',
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        self.published_post.tags.add(self.tag)
        self.draft_post = Post.objects.create(
            author=self.author,
            title='Draft Post',
            content='This post is private to the owner.',
            status=Post.Status.DRAFT,
        )

    def test_anonymous_user_can_list_only_published_posts(self):
        response = self.client.get(reverse('post-list-create'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [post['slug'] for post in response.data['results']]
        self.assertIn(self.published_post.slug, slugs)
        self.assertNotIn(self.draft_post.slug, slugs)

    def test_list_supports_simple_filtering_and_search(self):
        response = self.client.get(
            reverse('post-list-create'),
            {
                'category': self.category.slug,
                'tag': self.tag.slug,
                'author': self.author.username,
                'search': 'visible',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['slug'], self.published_post.slug)

    def test_anonymous_user_can_list_categories(self):
        response = self.client.get(reverse('category-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], self.category.name)
        self.assertEqual(response.data[0]['slug'], self.category.slug)

    def test_anonymous_user_can_list_tags(self):
        response = self.client.get(reverse('tag-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], self.tag.name)
        self.assertEqual(response.data[0]['slug'], self.tag.slug)

    def test_published_post_list_filters_by_category_slug(self):
        other_category = Category.objects.create(name='Python')
        Post.objects.create(
            author=self.author,
            title='Python Post',
            content='A different visible post.',
            category=other_category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )

        response = self.client.get(
            reverse('post-list-create'),
            {'category': self.category.slug},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [post['slug'] for post in response.data['results']]
        self.assertEqual(slugs, [self.published_post.slug])

    def test_published_post_list_filters_by_tag_slug(self):
        other_tag = Tag.objects.create(name='Python')
        other_post = Post.objects.create(
            author=self.author,
            title='Tagged Python Post',
            content='A different visible post.',
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        other_post.tags.add(other_tag)

        response = self.client.get(
            reverse('post-list-create'),
            {'tag': self.tag.slug},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [post['slug'] for post in response.data['results']]
        self.assertEqual(slugs, [self.published_post.slug])

    def test_search_matches_title_content_and_excerpt(self):
        title_post = Post.objects.create(
            author=self.author,
            title='Needle Title',
            content='Regular content.',
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        content_post = Post.objects.create(
            author=self.author,
            title='Content Search Post',
            content='The needle appears in the body.',
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        excerpt_post = Post.objects.create(
            author=self.author,
            title='Excerpt Search Post',
            content='Regular content.',
            excerpt='Needle summary.',
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )

        response = self.client.get(
            reverse('post-list-create'),
            {'search': 'needle'},
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = {post['slug'] for post in response.data['results']}
        self.assertEqual(
            slugs,
            {title_post.slug, content_post.slug, excerpt_post.slug},
        )

    def test_filters_and_search_do_not_expose_drafts(self):
        draft_category = Category.objects.create(name='Private Django')
        draft_tag = Tag.objects.create(name='Private API')
        self.draft_post.title = 'Secret Discovery Draft'
        self.draft_post.content = 'Hidden discovery content.'
        self.draft_post.excerpt = 'Secret excerpt.'
        self.draft_post.category = draft_category
        self.draft_post.save()
        self.draft_post.tags.add(draft_tag)

        category_response = self.client.get(
            reverse('post-list-create'),
            {'category': draft_category.slug},
        )
        tag_response = self.client.get(
            reverse('post-list-create'),
            {'tag': draft_tag.slug},
        )
        search_response = self.client.get(
            reverse('post-list-create'),
            {'search': 'secret'},
        )

        self.assertEqual(category_response.status_code, status.HTTP_200_OK)
        self.assertEqual(tag_response.status_code, status.HTTP_200_OK)
        self.assertEqual(search_response.status_code, status.HTTP_200_OK)
        self.assertEqual(category_response.data['results'], [])
        self.assertEqual(tag_response.data['results'], [])
        self.assertEqual(search_response.data['results'], [])

    def test_combined_category_tag_search_filtering(self):
        self.published_post.title = 'Visible JWT Tutorial'
        self.published_post.save()
        other_category = Category.objects.create(name='Python')
        other_tag = Tag.objects.create(name='Backend')

        wrong_category_post = Post.objects.create(
            author=self.author,
            title='Visible JWT Tutorial Wrong Category',
            content='This matches search but not category.',
            category=other_category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        wrong_category_post.tags.add(self.tag)

        wrong_tag_post = Post.objects.create(
            author=self.author,
            title='Visible JWT Tutorial Wrong Tag',
            content='This matches search but not tag.',
            category=self.category,
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        wrong_tag_post.tags.add(other_tag)

        response = self.client.get(
            reverse('post-list-create'),
            {
                'category': self.category.slug,
                'tag': self.tag.slug,
                'search': 'jwt',
            },
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [post['slug'] for post in response.data['results']]
        self.assertEqual(slugs, [self.published_post.slug])

    def test_authenticated_user_can_create_post(self):
        self.client.force_authenticate(user=self.author)

        response = self.client.post(
            reverse('post-list-create'),
            {
                'title': 'Created From API',
                'content': 'A useful post body.',
                'excerpt': 'A useful summary.',
                'category': self.category.id,
                'tags': [self.tag.id],
                'status': Post.Status.PUBLISHED,
            },
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['title'], 'Created From API')
        self.assertEqual(response.data['author']['username'], self.author.username)
        self.assertEqual(response.data['category']['slug'], self.category.slug)
        self.assertEqual(response.data['tags'][0]['slug'], self.tag.slug)

    def test_create_post_accepts_cover_image_upload(self):
        self.client.force_authenticate(user=self.author)
        image = SimpleUploadedFile(
            'cover.gif',
            (
                b'GIF87a\x01\x00\x01\x00\x80\x01\x00\x00\x00\x00'
                b'\xff\xff\xff,\x00\x00\x00\x00\x01\x00\x01\x00'
                b'\x00\x02\x02D\x01\x00;'
            ),
            content_type='image/gif',
        )

        response = self.client.post(
            reverse('post-list-create'),
            {
                'title': 'Post With Image',
                'content': 'Image post body.',
                'cover_image': image,
            },
            format='multipart',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('post_covers/', response.data['cover_image'])

    def test_anonymous_user_can_retrieve_published_post(self):
        response = self.client.get(
            reverse('post-detail', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['slug'], self.published_post.slug)

    def test_anonymous_user_cannot_retrieve_draft_post(self):
        response = self.client.get(
            reverse('post-detail', kwargs={'slug': self.draft_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_owner_can_retrieve_own_draft_post(self):
        self.client.force_authenticate(user=self.author)

        response = self.client.get(
            reverse('post-detail', kwargs={'slug': self.draft_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], Post.Status.DRAFT)

    def test_authenticated_user_can_list_own_posts_including_drafts(self):
        self.client.force_authenticate(user=self.author)

        response = self.client.get(reverse('my-posts'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [post['slug'] for post in response.data['results']]
        self.assertIn(self.published_post.slug, slugs)
        self.assertIn(self.draft_post.slug, slugs)

    def test_owner_can_update_own_post(self):
        self.client.force_authenticate(user=self.author)

        response = self.client.patch(
            reverse('post-detail', kwargs={'slug': self.draft_post.slug}),
            {'title': 'Updated Draft Title'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.draft_post.refresh_from_db()
        self.assertEqual(self.draft_post.title, 'Updated Draft Title')

    def test_non_owner_cannot_update_another_users_post(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            reverse('post-detail', kwargs={'slug': self.published_post.slug}),
            {'title': 'Not Allowed'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_owner_can_delete_own_post(self):
        self.client.force_authenticate(user=self.author)

        response = self.client.delete(
            reverse('post-detail', kwargs={'slug': self.draft_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Post.objects.filter(pk=self.draft_post.pk).exists())

    def test_non_owner_cannot_delete_another_users_post(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(
            reverse('post-detail', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_anonymous_user_can_list_comments_for_published_post(self):
        Comment.objects.create(
            post=self.published_post,
            user=self.author,
            body='First comment.',
        )

        response = self.client.get(
            reverse('post-comments', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['body'], 'First comment.')
        self.assertEqual(response.data[0]['user']['username'], self.author.username)

    def test_anonymous_user_cannot_list_comments_for_draft_post(self):
        Comment.objects.create(
            post=self.draft_post,
            user=self.author,
            body='Draft comment.',
        )

        response = self.client.get(
            reverse('post-comments', kwargs={'slug': self.draft_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_authenticated_user_can_comment_on_published_post(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            reverse('post-comments', kwargs={'slug': self.published_post.slug}),
            {'body': 'Great article.'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['body'], 'Great article.')
        self.assertEqual(response.data['user']['username'], self.other_user.username)
        self.assertEqual(self.published_post.comments.count(), 1)

    def test_authenticated_user_cannot_comment_on_draft_post(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            reverse('post-comments', kwargs={'slug': self.draft_post.slug}),
            {'body': 'I should not be here.'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(self.draft_post.comments.count(), 0)

    def test_anonymous_user_cannot_create_comment(self):
        response = self.client.post(
            reverse('post-comments', kwargs={'slug': self.published_post.slug}),
            {'body': 'Anonymous comment.'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_comment_owner_can_update_own_comment(self):
        comment = Comment.objects.create(
            post=self.published_post,
            user=self.author,
            body='Original comment.',
        )
        self.client.force_authenticate(user=self.author)

        response = self.client.patch(
            reverse('comment-detail', kwargs={'comment_id': comment.id}),
            {'body': 'Updated comment.'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        comment.refresh_from_db()
        self.assertEqual(comment.body, 'Updated comment.')

    def test_non_owner_cannot_update_another_users_comment(self):
        comment = Comment.objects.create(
            post=self.published_post,
            user=self.author,
            body='Original comment.',
        )
        self.client.force_authenticate(user=self.other_user)

        response = self.client.patch(
            reverse('comment-detail', kwargs={'comment_id': comment.id}),
            {'body': 'Not allowed.'},
            format='json',
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_comment_owner_can_delete_own_comment(self):
        comment = Comment.objects.create(
            post=self.published_post,
            user=self.author,
            body='Original comment.',
        )
        self.client.force_authenticate(user=self.author)

        response = self.client.delete(
            reverse('comment-detail', kwargs={'comment_id': comment.id})
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Comment.objects.filter(pk=comment.pk).exists())

    def test_non_owner_cannot_delete_another_users_comment(self):
        comment = Comment.objects.create(
            post=self.published_post,
            user=self.author,
            body='Original comment.',
        )
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(
            reverse('comment-detail', kwargs={'comment_id': comment.id})
        )

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertTrue(Comment.objects.filter(pk=comment.pk).exists())

    def test_authenticated_user_can_like_published_post(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            reverse('post-like', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Post liked successfully.')
        self.assertTrue(response.data['liked'])
        self.assertEqual(response.data['like_count'], 1)
        self.assertTrue(
            Like.objects.filter(post=self.published_post, user=self.other_user).exists()
        )

    def test_second_like_request_unlikes_published_post(self):
        Like.objects.create(post=self.published_post, user=self.other_user)
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            reverse('post-like', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Post unliked successfully.')
        self.assertFalse(response.data['liked'])
        self.assertEqual(response.data['like_count'], 0)
        self.assertFalse(
            Like.objects.filter(post=self.published_post, user=self.other_user).exists()
        )

    def test_delete_unlikes_published_post_and_is_idempotent(self):
        Like.objects.create(post=self.published_post, user=self.other_user)
        self.client.force_authenticate(user=self.other_user)

        first_response = self.client.delete(
            reverse('post-like', kwargs={'slug': self.published_post.slug})
        )
        second_response = self.client.delete(
            reverse('post-like', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertFalse(first_response.data['liked'])
        self.assertEqual(first_response.data['like_count'], 0)
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertFalse(second_response.data['liked'])
        self.assertEqual(second_response.data['like_count'], 0)

    def test_anonymous_user_cannot_like_or_unlike_post(self):
        like_response = self.client.post(
            reverse('post-like', kwargs={'slug': self.published_post.slug})
        )
        unlike_response = self.client.delete(
            reverse('post-like', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(like_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(unlike_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_cannot_like_draft_post(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            reverse('post-like', kwargs={'slug': self.draft_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(
            Like.objects.filter(post=self.draft_post, user=self.other_user).exists()
        )

    def test_post_list_includes_like_count_and_is_liked(self):
        Like.objects.create(post=self.published_post, user=self.other_user)
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(reverse('post-list-create'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post_data = response.data['results'][0]
        self.assertEqual(post_data['like_count'], 1)
        self.assertTrue(post_data['is_liked'])

    def test_post_list_includes_comment_count(self):
        Comment.objects.create(
            post=self.published_post,
            user=self.author,
            body='First comment.',
        )
        Comment.objects.create(
            post=self.published_post,
            user=self.other_user,
            body='Second comment.',
        )

        response = self.client.get(reverse('post-list-create'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post_data = response.data['results'][0]
        self.assertEqual(post_data['comment_count'], 2)

    def test_post_detail_includes_like_count_and_is_liked(self):
        Like.objects.create(post=self.published_post, user=self.other_user)
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(
            reverse('post-detail', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['like_count'], 1)
        self.assertTrue(response.data['is_liked'])

    def test_post_detail_includes_comment_count(self):
        Comment.objects.create(
            post=self.published_post,
            user=self.author,
            body='First comment.',
        )
        Comment.objects.create(
            post=self.published_post,
            user=self.other_user,
            body='Second comment.',
        )

        response = self.client.get(
            reverse('post-detail', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['comment_count'], 2)

    def test_anonymous_post_detail_returns_is_liked_false(self):
        Like.objects.create(post=self.published_post, user=self.other_user)

        response = self.client.get(
            reverse('post-detail', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['like_count'], 1)
        self.assertFalse(response.data['is_liked'])

    def test_authenticated_user_can_bookmark_published_post(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            reverse('post-bookmark', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Post bookmarked successfully.')
        self.assertTrue(response.data['bookmarked'])
        self.assertEqual(response.data['post']['slug'], self.published_post.slug)
        self.assertTrue(response.data['post']['is_bookmarked'])
        self.assertTrue(
            Bookmark.objects.filter(
                post=self.published_post,
                user=self.other_user,
            ).exists()
        )

    def test_repeated_bookmark_request_does_not_duplicate(self):
        Bookmark.objects.create(post=self.published_post, user=self.other_user)
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            reverse('post-bookmark', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Post already bookmarked.')
        self.assertTrue(response.data['bookmarked'])
        self.assertEqual(
            Bookmark.objects.filter(
                post=self.published_post,
                user=self.other_user,
            ).count(),
            1,
        )

    def test_authenticated_user_can_remove_bookmark(self):
        Bookmark.objects.create(post=self.published_post, user=self.other_user)
        self.client.force_authenticate(user=self.other_user)

        response = self.client.delete(
            reverse('post-bookmark', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'Post removed from bookmarks successfully.')
        self.assertFalse(response.data['bookmarked'])
        self.assertFalse(
            Bookmark.objects.filter(
                post=self.published_post,
                user=self.other_user,
            ).exists()
        )

    def test_repeated_remove_bookmark_request_is_idempotent(self):
        self.client.force_authenticate(user=self.other_user)

        first_response = self.client.delete(
            reverse('post-bookmark', kwargs={'slug': self.published_post.slug})
        )
        second_response = self.client.delete(
            reverse('post-bookmark', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(first_response.status_code, status.HTTP_200_OK)
        self.assertFalse(first_response.data['bookmarked'])
        self.assertEqual(second_response.status_code, status.HTTP_200_OK)
        self.assertFalse(second_response.data['bookmarked'])

    def test_anonymous_user_cannot_bookmark_remove_or_list_bookmarks(self):
        bookmark_response = self.client.post(
            reverse('post-bookmark', kwargs={'slug': self.published_post.slug})
        )
        remove_response = self.client.delete(
            reverse('post-bookmark', kwargs={'slug': self.published_post.slug})
        )
        list_response = self.client.get(reverse('bookmark-list'))

        self.assertEqual(bookmark_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(remove_response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertEqual(list_response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_authenticated_user_cannot_bookmark_draft_post(self):
        self.client.force_authenticate(user=self.other_user)

        response = self.client.post(
            reverse('post-bookmark', kwargs={'slug': self.draft_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(
            Bookmark.objects.filter(
                post=self.draft_post,
                user=self.other_user,
            ).exists()
        )

    def test_bookmark_list_returns_only_current_users_bookmarks(self):
        other_post = Post.objects.create(
            author=self.author,
            title='Another Published Post',
            content='Visible to everyone.',
            status=Post.Status.PUBLISHED,
            published_at=timezone.now(),
        )
        Bookmark.objects.create(post=self.published_post, user=self.other_user)
        Bookmark.objects.create(post=other_post, user=self.author)
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(reverse('bookmark-list'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        slugs = [post['slug'] for post in response.data['results']]
        self.assertEqual(slugs, [self.published_post.slug])
        self.assertTrue(response.data['results'][0]['is_bookmarked'])

    def test_post_list_includes_is_bookmarked(self):
        Bookmark.objects.create(post=self.published_post, user=self.other_user)
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(reverse('post-list-create'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        post_data = response.data['results'][0]
        self.assertTrue(post_data['is_bookmarked'])

    def test_post_detail_includes_is_bookmarked(self):
        Bookmark.objects.create(post=self.published_post, user=self.other_user)
        self.client.force_authenticate(user=self.other_user)

        response = self.client.get(
            reverse('post-detail', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['is_bookmarked'])

    def test_anonymous_post_detail_returns_is_bookmarked_false(self):
        Bookmark.objects.create(post=self.published_post, user=self.other_user)

        response = self.client.get(
            reverse('post-detail', kwargs={'slug': self.published_post.slug})
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['is_bookmarked'])
