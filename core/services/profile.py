import json
import cloudinary.uploader
from io import BytesIO
from PIL import Image
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST, require_GET
from django.views.decorators.cache import never_cache
from django.contrib import messages

from ..models import CustomUser, FreelancerProfile, Post, PostLike, Comment


ALLOWED_MIMETYPES = {'image/jpeg', 'image/png', 'video/mp4'}
MAX_FILE_MB = 50


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _get_resource_type(content_type: str) -> str:
    if content_type == 'video/mp4':
        return 'video'
    return 'image'


def _build_post_json(post, user, media_files_override=None):
    """Serialize a Post to a dict safe for JSON."""
    liked = PostLike.objects.filter(user=user, post=post).exists() if user.is_authenticated else False
    comments = list(
        post.comments.select_related('user').values(
            'id', 'text', 'user__username', 'user__user_type', 'created_at'
        )
    )
    # Convert datetimes to ISO strings
    for c in comments:
        c['created_at'] = c['created_at'].isoformat()

    media_files = []
    if media_files_override:
        media_files = media_files_override
    else:
        # Get from PostMedia relation
        for pm in post.media_files.all():
            # Use stored resource_type on the PM record if available
            rt = getattr(pm, 'resource_type', None) or ''
            
            if hasattr(pm.media, 'url'):
                m_url = pm.media.url
            else:
                pub = str(pm.media)
                if rt == 'video':
                    import cloudinary
                    m_url = cloudinary.CloudinaryVideo(pub).build_url(secure=True)
                else:
                    import cloudinary
                    m_url = cloudinary.CloudinaryImage(pub).build_url(secure=True)
            
            # Infer resource_type from URL if not stored
            if not rt:
                rt = 'video' if ('/video/' in m_url or any(m_url.lower().endswith(e) for e in ('.mp4', '.mov', '.webm'))) else 'image'
            media_files.append({'url': m_url, 'resource_type': rt})
            
        # Fallback for old posts without PostMedia
        if getattr(post, 'media', None) and not media_files:
            media_field = post.media
            if hasattr(media_field, 'url'):
                media_url = media_field.url
            else:
                import cloudinary
                media_url = cloudinary.CloudinaryImage(str(media_field)).build_url(secure=True)
            rt = getattr(post.media, 'resource_type', None)
            if not rt:
                rt = 'video' if any(media_url.lower().endswith(ext) for ext in ('.mp4', '.mov', '.webm')) else 'image'
            media_files.append({'url': media_url, 'resource_type': rt})

    # For legacy backwards compatibility in front-end
    media_url = media_files[0]['url'] if media_files else ''
    resource_type = media_files[0]['resource_type'] if media_files else 'image'

    return {
        'id': post.id,
        'media_url': media_url,
        'resource_type': resource_type,
        'media_files': media_files,
        'caption': post.caption or '',
        'category': post.category,
        'category_display': post.get_category_display(),
        'likes_count': post.likes_count,
        'comments_count': post.comments_count,
        'liked': liked,
        'comments': comments,
        'created_at': post.created_at.isoformat(),
        'owner': post.user.username,
    }


# ─── Profile Page ─────────────────────────────────────────────────────────────

@never_cache
def profile_view(request, username):
    """Render the freelancer profile page."""
    profile_user = get_object_or_404(CustomUser, username=username)

    # Only freelancers have public profiles via this view
    if profile_user.user_type != 'freelancer':
        from django.http import Http404
        raise Http404("Profile not found")

    profile = FreelancerProfile.get_or_create_for(profile_user)
    is_owner = request.user.is_authenticated and request.user == profile_user

    posts_qs = (
        Post.objects
        .filter(user=profile_user)
        .prefetch_related('likes', 'comments__user', 'media_files')
        .select_related('user')
    )

    # Compute average rating from reviews
    from django.db.models import Avg
    avg = profile_user.received_reviews.aggregate(avg=Avg('rating'))['avg']
    if avg is not None:
        profile.rating = round(avg, 1)

    category_choices = Post.CATEGORY_CHOICES
    selected_category = request.GET.get('category', '')

    context = {
        'profile_user': profile_user,
        'profile': profile,
        'is_owner': is_owner,
        'posts': posts_qs,
        'category_choices': category_choices,
        'selected_category': selected_category,
    }
    return render(request, 'core/profile.html', context)


# ─── Update Profile Photo (AJAX) ──────────────────────────────────────────────

@login_required
@require_POST
def update_profile_photo(request):
    """Upload a cropped profile photo (sent as file blob) to Cloudinary."""
    file = request.FILES.get('photo')
    if not file:
        return JsonResponse({'success': False, 'error': 'No file provided.'}, status=400)

    if file.content_type not in {'image/jpeg', 'image/png'}:
        return JsonResponse({'success': False, 'error': 'Only JPEG/PNG accepted.'}, status=400)

    try:
        # Enforce backend resize + compression to keep avatar payload small and consistent.
        image = Image.open(file)
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')
        elif image.mode == 'L':
            image = image.convert('RGB')

        image = image.resize((256, 256), Image.Resampling.LANCZOS)
        output = BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)

        result = cloudinary.uploader.upload(
            output,
            resource_type='image',
            folder='freelancehub/profiles',
            public_id=f"user_{request.user.id}_avatar",
            overwrite=True,
            format='jpg',
        )
        public_id = result['public_id']
        url = result['secure_url']
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Upload failed: {str(e)}'}, status=500)

    profile = FreelancerProfile.get_or_create_for(request.user)
    # Store public_id into the CloudinaryField
    profile.profile_photo = public_id
    profile.save(update_fields=['profile_photo'])

    return JsonResponse({'success': True, 'url': url})


# ─── Add Post ─────────────────────────────────────────────────────────────────

@login_required
@require_POST
def add_post(request):
    """Create a new portfolio post. Only freelancers can post."""
    if request.user.user_type != 'freelancer':
        return JsonResponse({'success': False, 'error': 'Only freelancers can post.'}, status=403)

    files = request.FILES.getlist('media')
    caption = request.POST.get('caption', '').strip()
    category = request.POST.get('category', 'other')

    if not files:
        return JsonResponse({'success': False, 'error': 'At least one media file is required.'}, status=400)

    if len(files) > 10:
        return JsonResponse({'success': False, 'error': 'Maximum 10 files allowed per post.'}, status=400)

    for file in files:
        if file.content_type not in ALLOWED_MIMETYPES:
            return JsonResponse({'success': False, 'error': 'Only JPEG, PNG, and MP4 are allowed.'}, status=400)
        if file.size > MAX_FILE_MB * 1024 * 1024:
            return JsonResponse({'success': False, 'error': f'File too large. Max {MAX_FILE_MB}MB.'}, status=400)

    post = Post.objects.create(
        user=request.user,
        media=None, # Legacy field
        caption=caption,
        category=category,
    )

    from ..models import PostMedia
    import cloudinary.uploader

    media_files_data = []

    try:
        for file in files:
            resource_type = _get_resource_type(file.content_type)
            result = cloudinary.uploader.upload(
                file,
                resource_type=resource_type,
                type='upload',  # Ensures public access
                folder=f'freelancehub/posts/{request.user.username}',
            )
            public_id = result['public_id']
            secure_url = result['secure_url']

            PostMedia.objects.create(post=post, media=public_id, resource_type=resource_type)
            media_files_data.append({
                'url': secure_url,
                'resource_type': resource_type
            })

    except Exception as e:
        post.delete() # Rollback on error
        return JsonResponse({'success': False, 'error': f'Upload failed: {str(e)}'}, status=500)

    return JsonResponse({
        'success': True,
        'post': _build_post_json(
            post,
            request.user,
            media_files_override=media_files_data
        )
    })


# ─── Delete Post ──────────────────────────────────────────────────────────────

@login_required
@require_POST
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.user != request.user:
        return JsonResponse({'success': False, 'error': 'Permission denied.'}, status=403)
    post.delete()
    return JsonResponse({'success': True})


# ─── Toggle Like (AJAX) ───────────────────────────────────────────────────────

@login_required
@require_POST
def toggle_like(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    like, created = PostLike.objects.get_or_create(user=request.user, post=post)
    if not created:
        like.delete()
        liked = False
    else:
        liked = True
    return JsonResponse({'success': True, 'liked': liked, 'likes_count': post.likes.count()})


# ─── Add Comment (AJAX) ───────────────────────────────────────────────────────

@login_required
@require_POST
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    try:
        data = json.loads(request.body)
        text = data.get('text', '').strip()
    except (json.JSONDecodeError, AttributeError):
        text = request.POST.get('text', '').strip()

    if not text:
        return JsonResponse({'success': False, 'error': 'Comment text required.'}, status=400)

    comment = Comment.objects.create(user=request.user, post=post, text=text)
    return JsonResponse({
        'success': True,
        'comment': {
            'id': comment.id,
            'text': comment.text,
            'user__username': comment.user.username,
            'user__user_type': comment.user.user_type,
            'created_at': comment.created_at.isoformat(),
        }
    })


# ─── Filter Posts (AJAX) ──────────────────────────────────────────────────────

@never_cache
@require_GET
def filter_posts(request, username):
    """Return posts for a freelancer, optionally filtered by category."""
    profile_user = get_object_or_404(CustomUser, username=username)
    category = request.GET.get('category', '').strip()

    posts_qs = (
        Post.objects
        .filter(user=profile_user)
        .prefetch_related('likes', 'comments__user')
        .select_related('user')
    )
    if category:
        posts_qs = posts_qs.filter(category=category)

    user = request.user
    data = [_build_post_json(p, user) for p in posts_qs]
    return JsonResponse({'success': True, 'posts': data})
