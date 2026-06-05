# Authentication API

These endpoints manage signup, JWT login, token refresh, and the authenticated user's profile.

## Signup
**Method:** `POST`
**URL:** `/api/auth/signup/`

### Authentication
Not required

### Request Body
```json
{
  "username": "clinton",
  "email": "clinton@example.com",
  "password": "StrongPass123!",
  "password_confirm": "StrongPass123!"
}
```

### Successful Response
```json
{
  "message": "Signup successful.",
  "user": {
    "id": 1,
    "username": "clinton",
    "email": "clinton@example.com",
    "first_name": "",
    "last_name": "",
    "date_joined": "2026-05-14T12:00:00Z"
  },
  "tokens": {
    "refresh": "refresh-token",
    "access": "access-token"
  }
}
```

### Possible Error Responses
```json
{
  "email": ["A user with this email already exists."]
}
```

```json
{
  "password_confirm": "Passwords do not match."
}
```

## Login
**Method:** `POST`
**URL:** `/api/auth/login/`

### Authentication
Not required

### Request Body
```json
{
  "username": "clinton",
  "password": "StrongPass123!"
}
```

### Successful Response
```json
{
  "message": "Login successful.",
  "user": {
    "id": 1,
    "username": "clinton",
    "email": "clinton@example.com",
    "first_name": "",
    "last_name": "",
    "date_joined": "2026-05-14T12:00:00Z"
  },
  "tokens": {
    "refresh": "refresh-token",
    "access": "access-token"
  }
}
```

### Possible Error Responses
```json
{
  "non_field_errors": ["Invalid username or password."]
}
```

## Refresh Token
**Method:** `POST`
**URL:** `/api/auth/token/refresh/`

### Authentication
Not required

### Request Body
```json
{
  "refresh": "refresh-token"
}
```

### Successful Response
```json
{
  "access": "new-access-token"
}
```

### Possible Error Responses
```json
{
  "detail": "Token is invalid",
  "code": "token_not_valid"
}
```

## Get Profile
**Method:** `GET`
**URL:** `/api/auth/profile/`

### Authentication
Required

### Request Body
```json
{}
```

### Successful Response
```json
{
  "id": 1,
  "username": "clinton",
  "email": "clinton@example.com",
  "first_name": "",
  "last_name": "",
  "date_joined": "2026-05-14T12:00:00Z"
}
```

### Possible Error Responses
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Update Profile
**Method:** `PATCH`
**URL:** `/api/auth/profile/`

### Authentication
Required

### Request Body
```json
{
  "username": "clintoncodes",
  "email": "clintoncodes@example.com",
  "first_name": "Clinton",
  "last_name": "Codes"
}
```

### Successful Response
```json
{
  "message": "Profile updated successfully.",
  "user": {
    "id": 1,
    "username": "clintoncodes",
    "email": "clintoncodes@example.com",
    "first_name": "Clinton",
    "last_name": "Codes",
    "date_joined": "2026-05-14T12:00:00Z"
  }
}
```

### Possible Error Responses
```json
{
  "email": ["A user with this email already exists."]
}
```

```json
{
  "detail": "Authentication credentials were not provided."
}
```

## How this was generated
Inspected `config/urls.py`, `accounts/urls.py`, `accounts/views.py`, `accounts/serializers.py`, and `accounts/models.py`.

# Content Discovery API

These public endpoints help frontend clients build category/tag navigation. Category and tag creation is still handled through Django admin for this baseline backend.

## List Categories
**Method:** `GET`
**URL:** `/api/categories/`

### Authentication
Not required

### Request Body
```json
{}
```

### Successful Response
```json
[
  {
    "id": 1,
    "name": "Django",
    "slug": "django"
  }
]
```

### Possible Error Responses
```json
{}
```

## List Tags
**Method:** `GET`
**URL:** `/api/tags/`

### Authentication
Not required

### Request Body
```json
{}
```

### Successful Response
```json
[
  {
    "id": 1,
    "name": "API",
    "slug": "api"
  }
]
```

### Possible Error Responses
```json
{}
```

## How this was generated
Inspected `blog/urls.py`, `blog/views.py`, `blog/serializers.py`, and `blog/models.py`.

# Blog Posts API

These endpoints manage blog posts. Public endpoints only return published posts. Authenticated owners can view, update, delete, and list their own drafts.

Frontend response polish: post responses include nested author/category/tag summaries plus `like_count`, `comment_count`, `is_liked`, and `is_bookmarked`, so post cards can render common UI state without extra requests.

## List Published Posts
**Method:** `GET`
**URL:** `/api/posts/`

### Authentication
Not required

### Query Parameters
- `page`: page number for pagination
- `category`: category slug, such as `django`
- `tag`: tag slug, such as `api`
- `author`: author username
- `search`: text search across title, content, and excerpt

Query parameters can be combined. Public post listing always returns published posts only, even when filters or search match a draft.

### Example URLs
- `/api/posts/?category=django`
- `/api/posts/?tag=api`
- `/api/posts/?search=authentication`
- `/api/posts/?category=django&tag=api`
- `/api/posts/?category=django&search=jwt`

### Request Body
```json
{}
```

### Successful Response
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Published Post",
      "slug": "published-post",
      "excerpt": "A short summary.",
      "cover_image": "http://localhost:8000/media/post_covers/cover.jpg",
      "author": {
        "id": 1,
        "username": "clinton"
      },
      "category": {
        "id": 1,
        "name": "Django",
        "slug": "django"
      },
      "tags": [
        {
          "id": 1,
          "name": "API",
          "slug": "api"
        }
      ],
      "like_count": 0,
      "comment_count": 2,
      "is_liked": false,
      "is_bookmarked": false,
      "published_at": "2026-05-14T12:00:00Z",
      "view_count": 0,
      "created_at": "2026-05-14T12:00:00Z"
    }
  ]
}
```

### Possible Error Responses
```json
{}
```

## Create Post
**Method:** `POST`
**URL:** `/api/posts/`

### Authentication
Required

### Request Body
Send JSON, form data, or multipart form data when uploading `cover_image`.

```json
{
  "title": "My First Blog Post",
  "content": "Full post body.",
  "excerpt": "Short summary.",
  "cover_image": "uploaded-file",
  "category": 1,
  "tags": [1, 2],
  "status": "draft",
  "published_at": null
}
```

### Successful Response
```json
{
  "id": 1,
  "title": "My First Blog Post",
  "slug": "my-first-blog-post",
  "content": "Full post body.",
  "excerpt": "Short summary.",
  "cover_image": "http://localhost:8000/media/post_covers/cover.jpg",
  "author": {
    "id": 1,
    "username": "clinton"
  },
  "category": {
    "id": 1,
    "name": "Django",
    "slug": "django"
  },
  "tags": [],
  "like_count": 0,
  "comment_count": 0,
  "is_liked": false,
  "is_bookmarked": false,
  "status": "draft",
  "published_at": null,
  "view_count": 0,
  "created_at": "2026-05-14T12:00:00Z",
  "updated_at": "2026-05-14T12:00:00Z"
}
```

### Possible Error Responses
```json
{
  "detail": "Authentication credentials were not provided."
}
```

```json
{
  "title": ["This field is required."]
}
```

## Retrieve Post
**Method:** `GET`
**URL:** `/api/posts/<slug>/`

### Authentication
Not required for published posts. Required to view your own draft posts.

### Request Body
```json
{}
```

### Successful Response
```json
{
  "id": 1,
  "title": "Published Post",
  "slug": "published-post",
  "content": "Full post body.",
  "excerpt": "Short summary.",
  "cover_image": null,
  "author": {
    "id": 1,
    "username": "clinton"
  },
  "category": null,
  "tags": [],
  "like_count": 0,
  "comment_count": 2,
  "is_liked": false,
  "is_bookmarked": false,
  "status": "published",
  "published_at": "2026-05-14T12:00:00Z",
  "view_count": 0,
  "created_at": "2026-05-14T12:00:00Z",
  "updated_at": "2026-05-14T12:00:00Z"
}
```

### Possible Error Responses
```json
{
  "detail": "No Post matches the given query."
}
```

## Update Own Post
**Method:** `PATCH`
**URL:** `/api/posts/<slug>/`

### Authentication
Required. Only the post owner can update.

### Request Body
```json
{
  "title": "Updated Blog Post",
  "content": "Updated post body.",
  "excerpt": "Updated summary.",
  "category": 1,
  "tags": [1, 2],
  "status": "published",
  "published_at": "2026-05-14T12:00:00Z"
}
```

### Successful Response
```json
{
  "id": 1,
  "title": "Updated Blog Post",
  "slug": "published-post",
  "content": "Updated post body.",
  "excerpt": "Updated summary.",
  "cover_image": null,
  "author": {
    "id": 1,
    "username": "clinton"
  },
  "category": {
    "id": 1,
    "name": "Django",
    "slug": "django"
  },
  "tags": [],
  "like_count": 0,
  "comment_count": 0,
  "is_liked": false,
  "is_bookmarked": false,
  "status": "published",
  "published_at": "2026-05-14T12:00:00Z",
  "view_count": 0,
  "created_at": "2026-05-14T12:00:00Z",
  "updated_at": "2026-05-14T12:05:00Z"
}
```

### Possible Error Responses
```json
{
  "detail": "You do not have permission to modify this post."
}
```

```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Delete Own Post
**Method:** `DELETE`
**URL:** `/api/posts/<slug>/`

### Authentication
Required. Only the post owner can delete.

### Request Body
```json
{}
```

### Successful Response
```json
{}
```

### Possible Error Responses
```json
{
  "detail": "You do not have permission to modify this post."
}
```

```json
{
  "detail": "Authentication credentials were not provided."
}
```

## List My Posts
**Method:** `GET`
**URL:** `/api/posts/my-posts/`

### Authentication
Required

### Request Body
```json
{}
```

### Successful Response
```json
{
  "count": 2,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 2,
      "title": "Draft Post",
      "slug": "draft-post",
      "content": "Draft body.",
      "excerpt": "",
      "cover_image": null,
      "author": {
        "id": 1,
        "username": "clinton"
      },
      "category": null,
      "tags": [],
      "like_count": 0,
      "comment_count": 0,
      "is_liked": false,
      "is_bookmarked": false,
      "status": "draft",
      "published_at": null,
      "view_count": 0,
      "created_at": "2026-05-14T12:00:00Z",
      "updated_at": "2026-05-14T12:00:00Z"
    }
  ]
}
```

### Possible Error Responses
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## How this was generated
Inspected `config/urls.py`, `blog/urls.py`, `blog/views.py`, `blog/serializers.py`, and `blog/models.py`.

# Blog Likes API

Likes belong to a published blog post and the authenticated user. A user can only have one like per post.

## Toggle Post Like
**Method:** `POST`
**URL:** `/api/posts/<slug>/like/`

### Authentication
Required

### Request Body
```json
{}
```

### Successful Response
When the post was not liked yet:
```json
{
  "message": "Post liked successfully.",
  "liked": true,
  "like_count": 1
}
```

When the post was already liked, the same request unlikes it:
```json
{
  "message": "Post unliked successfully.",
  "liked": false,
  "like_count": 0
}
```

### Possible Error Responses
```json
{
  "detail": "Authentication credentials were not provided."
}
```

```json
{
  "detail": "No Post matches the given query."
}
```

## Unlike Post
**Method:** `DELETE`
**URL:** `/api/posts/<slug>/like/`

### Authentication
Required

### Request Body
```json
{}
```

### Successful Response
```json
{
  "message": "Post unliked successfully.",
  "liked": false,
  "like_count": 0
}
```

### Possible Error Responses
```json
{
  "detail": "Authentication credentials were not provided."
}
```

```json
{
  "detail": "No Post matches the given query."
}
```

## How this was generated
Inspected `blog/urls.py`, `blog/views.py`, `blog/serializers.py`, and `blog/models.py`.

# Blog Bookmarks API

Bookmarks belong to a published blog post and the authenticated user. A user can only bookmark the same post once.

## Bookmark Post
**Method:** `POST`
**URL:** `/api/posts/<slug>/bookmark/`

### Authentication
Required

### Request Body
```json
{}
```

### Successful Response
```json
{
  "message": "Post bookmarked successfully.",
  "bookmarked": true,
  "post": {
    "id": 1,
    "title": "Published Post",
    "slug": "published-post",
    "excerpt": "A short summary.",
    "cover_image": null,
    "author": {
      "id": 1,
      "username": "clinton"
    },
    "category": null,
    "tags": [],
    "like_count": 0,
    "comment_count": 0,
    "is_liked": false,
    "is_bookmarked": true,
    "published_at": "2026-05-14T12:00:00Z",
    "view_count": 0,
    "created_at": "2026-05-14T12:00:00Z"
  }
}
```

If the post was already bookmarked, no duplicate is created:
```json
{
  "message": "Post already bookmarked.",
  "bookmarked": true,
  "post": {
    "id": 1,
    "title": "Published Post",
    "slug": "published-post",
    "excerpt": "A short summary.",
    "cover_image": null,
    "author": {
      "id": 1,
      "username": "clinton"
    },
    "category": null,
    "tags": [],
    "like_count": 0,
    "comment_count": 0,
    "is_liked": false,
    "is_bookmarked": true,
    "published_at": "2026-05-14T12:00:00Z",
    "view_count": 0,
    "created_at": "2026-05-14T12:00:00Z"
  }
}
```

### Possible Error Responses
```json
{
  "detail": "Authentication credentials were not provided."
}
```

```json
{
  "detail": "No Post matches the given query."
}
```

## Remove Bookmark
**Method:** `DELETE`
**URL:** `/api/posts/<slug>/bookmark/`

### Authentication
Required

### Request Body
```json
{}
```

### Successful Response
```json
{
  "message": "Post removed from bookmarks successfully.",
  "bookmarked": false
}
```

### Possible Error Responses
```json
{
  "detail": "Authentication credentials were not provided."
}
```

```json
{
  "detail": "No Post matches the given query."
}
```

## List My Bookmarks
**Method:** `GET`
**URL:** `/api/bookmarks/`

### Authentication
Required

### Request Body
```json
{}
```

### Successful Response
```json
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Published Post",
      "slug": "published-post",
      "excerpt": "A short summary.",
      "cover_image": null,
      "author": {
        "id": 1,
        "username": "clinton"
      },
      "category": null,
      "tags": [],
      "like_count": 0,
      "comment_count": 0,
      "is_liked": false,
      "is_bookmarked": true,
      "published_at": "2026-05-14T12:00:00Z",
      "view_count": 0,
      "created_at": "2026-05-14T12:00:00Z"
    }
  ]
}
```

### Possible Error Responses
```json
{
  "detail": "Authentication credentials were not provided."
}
```

## How this was generated
Inspected `blog/urls.py`, `blog/views.py`, `blog/serializers.py`, and `blog/models.py`.

# Blog Comments API

Comments belong to both a blog post and the user who wrote them. Comments can be listed or created only through published posts.

## List Comments For Post
**Method:** `GET`
**URL:** `/api/posts/<slug>/comments/`

### Authentication
Not required

### Request Body
```json
{}
```

### Successful Response
```json
[
  {
    "id": 1,
    "user": {
      "id": 2,
      "username": "reader"
    },
    "body": "Great article.",
    "created_at": "2026-05-14T12:00:00Z",
    "updated_at": "2026-05-14T12:00:00Z"
  }
]
```

### Possible Error Responses
```json
{
  "detail": "No Post matches the given query."
}
```

## Add Comment To Post
**Method:** `POST`
**URL:** `/api/posts/<slug>/comments/`

### Authentication
Required

### Request Body
```json
{
  "body": "Great article."
}
```

### Successful Response
```json
{
  "id": 1,
  "user": {
    "id": 2,
    "username": "reader"
  },
  "body": "Great article.",
  "created_at": "2026-05-14T12:00:00Z",
  "updated_at": "2026-05-14T12:00:00Z"
}
```

### Possible Error Responses
```json
{
  "detail": "Authentication credentials were not provided."
}
```

```json
{
  "body": ["This field is required."]
}
```

```json
{
  "detail": "No Post matches the given query."
}
```

## Update Own Comment
**Method:** `PATCH`
**URL:** `/api/comments/<int:comment_id>/`

### Authentication
Required

### Request Body
```json
{
  "body": "Updated comment text."
}
```

### Successful Response
```json
{
  "id": 1,
  "user": {
    "id": 2,
    "username": "reader"
  },
  "body": "Updated comment text.",
  "created_at": "2026-05-14T12:00:00Z",
  "updated_at": "2026-05-14T12:05:00Z"
}
```

### Possible Error Responses
```json
{
  "detail": "You do not have permission to modify this comment."
}
```

```json
{
  "detail": "Authentication credentials were not provided."
}
```

## Delete Own Comment
**Method:** `DELETE`
**URL:** `/api/comments/<int:comment_id>/`

### Authentication
Required

### Request Body
```json
{}
```

### Successful Response
```json
{}
```

### Possible Error Responses
```json
{
  "detail": "You do not have permission to modify this comment."
}
```

```json
{
  "detail": "Authentication credentials were not provided."
}
```

## How this was generated
Inspected `blog/urls.py`, `blog/views.py`, `blog/serializers.py`, and `blog/models.py`.
