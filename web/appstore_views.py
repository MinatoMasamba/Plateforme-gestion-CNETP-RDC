"""Vues web de l'App Store CNE-ITP."""
from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET, require_http_methods, require_POST

from apps.appstore.forms import (
    AppAnnouncementForm,
    AppCategoryForm,
    AppReleaseFileForm,
    AppScreenshotForm,
    AppVersionForm,
    SoftwareAppForm,
)
from apps.appstore.models import (
    AppAnnouncement,
    AppCategory,
    AppReleaseFile,
    AppScreenshot,
    AppVersion,
    SoftwareApp,
)
from apps.appstore.services import (
    approve_release_file,
    archive_announcement,
    attach_package,
    can_download_file,
    can_manage_appstore,
    download_stats,
    downloadable_files_for,
    publish_announcement,
    publish_version,
    published_apps_queryset,
    reject_release_file,
    serve_download,
    visible_versions_for,
    withdraw_version,
)


def appstore_admin_required(view_func):
    @wraps(view_func)
    @login_required(login_url='web:expert_login')
    def wrapped(request, *args, **kwargs):
        if not can_manage_appstore(request.user):
            raise PermissionDenied
        return view_func(request, *args, **kwargs)

    return wrapped


def _platform_labels():
    return dict(AppReleaseFile.Platform.choices)


# ─── Public catalogue ───────────────────────────────────────────────────────


@require_GET
def catalog(request):
    search = (request.GET.get('q') or '').strip()
    category = (request.GET.get('category') or '').strip()
    platform = (request.GET.get('platform') or '').strip()
    apps = list(published_apps_queryset(search=search, category=category, platform=platform))
    featured = [app for app in apps if app.is_featured][:6]
    categories = AppCategory.objects.filter(is_active=True, applications__is_published=True).distinct()
    used_platforms = (
        AppReleaseFile.objects.filter(
            version__application__is_published=True,
            version__status=AppVersion.Status.PUBLISHED,
            quarantine_status=AppReleaseFile.QuarantineStatus.APPROVED,
        )
        .values_list('platform', flat=True)
        .distinct()
    )
    cards = []
    for app in apps:
        platforms = app.visible_platforms()
        recommended = app.recommended_version
        download_file = None
        if recommended and request.user.is_authenticated:
            for release in recommended.files.all():
                if can_download_file(request.user, release):
                    download_file = release
                    break
        cards.append({
            'app': app,
            'platforms': platforms,
            'recommended': recommended,
            'download_file': download_file,
        })
    return render(request, 'appstore/catalog.html', {
        'cards': cards,
        'featured': featured,
        'categories': categories,
        'platforms': [(p, _platform_labels().get(p, p)) for p in used_platforms],
        'search': search,
        'selected_category': category,
        'selected_platform': platform,
        'can_admin': can_manage_appstore(request.user),
    })


@require_GET
def app_detail(request, slug):
    app = get_object_or_404(
        SoftwareApp.objects.select_related('category', 'recommended_version')
        .prefetch_related('screenshots'),
        slug=slug,
        is_published=True,
        withdrawn_at__isnull=True,
    )
    versions = visible_versions_for(request.user, app)
    version_param = (request.GET.get('version') or '').strip()
    selected = None
    if version_param:
        selected = next((v for v in versions if v.version_number == version_param), None)
    if selected is None:
        preferred = app.recommended_version
        if preferred and preferred in versions:
            selected = preferred
        elif versions:
            selected = versions[0]
    files = downloadable_files_for(request.user, selected) if selected else []
    announcements = AppAnnouncement.objects.filter(
        status=AppAnnouncement.Status.PUBLISHED,
        application=app,
    )[:5]
    return render(request, 'appstore/detail.html', {
        'app': app,
        'versions': versions,
        'selected_version': selected,
        'files': files,
        'features': app.feature_list(),
        'screenshots': app.screenshots.all(),
        'announcements': announcements,
        'can_admin': can_manage_appstore(request.user),
        'login_required_for_download': not request.user.is_authenticated,
    })


@require_GET
def announcements(request):
    items = AppAnnouncement.objects.filter(
        status=AppAnnouncement.Status.PUBLISHED,
    ).select_related('application', 'version')
    return render(request, 'appstore/announcements.html', {
        'announcements': items,
        'can_admin': can_manage_appstore(request.user),
    })


@login_required(login_url='web:expert_login')
@require_GET
def download_release(request, file_id):
    release_file = get_object_or_404(
        AppReleaseFile.objects.select_related('version__application'),
        pk=file_id,
    )
    try:
        return serve_download(request, release_file)
    except PermissionDenied:
        raise
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc))
        return redirect('web:appstore_detail', slug=release_file.version.application.slug)


# ─── Administration ─────────────────────────────────────────────────────────


@appstore_admin_required
@require_GET
def admin_home(request):
    apps = SoftwareApp.objects.select_related('category', 'recommended_version').order_by('name')
    pending_files = AppReleaseFile.objects.filter(
        quarantine_status=AppReleaseFile.QuarantineStatus.PENDING,
    ).select_related('version__application')[:20]
    stats = download_stats(days=30)
    return render(request, 'appstore/admin/home.html', {
        'apps': apps,
        'pending_files': pending_files,
        'stats': stats,
        'announcement_count': AppAnnouncement.objects.count(),
        'category_count': AppCategory.objects.count(),
    })


@appstore_admin_required
@require_http_methods(['GET', 'POST'])
def admin_app_edit(request, pk=None):
    instance = get_object_or_404(SoftwareApp, pk=pk) if pk else None
    form = SoftwareAppForm(request.POST or None, request.FILES or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        app = form.save(commit=False)
        if not instance:
            app.created_by = request.user
        app.updated_by = request.user
        app.save()
        messages.success(request, 'Application enregistrée.')
        return redirect('web:appstore_admin_app', pk=app.pk)
    versions = []
    screenshots = []
    if instance:
        versions = instance.versions.prefetch_related('files').all()
        screenshots = instance.screenshots.all()
    return render(request, 'appstore/admin/app_form.html', {
        'form': form,
        'app': instance,
        'versions': versions,
        'screenshots': screenshots,
        'screenshot_form': AppScreenshotForm() if instance else None,
        'version_form': AppVersionForm() if instance else None,
    })


@appstore_admin_required
@require_POST
def admin_app_withdraw(request, pk):
    app = get_object_or_404(SoftwareApp, pk=pk)
    app.withdrawn_at = timezone.now()
    app.is_published = False
    app.updated_by = request.user
    app.save(update_fields=['withdrawn_at', 'is_published', 'updated_by', 'updated_at'])
    messages.success(request, 'Application retirée du catalogue.')
    return redirect('web:appstore_admin_home')


@appstore_admin_required
@require_POST
def admin_screenshot_add(request, pk):
    app = get_object_or_404(SoftwareApp, pk=pk)
    form = AppScreenshotForm(request.POST, request.FILES)
    if form.is_valid():
        shot = form.save(commit=False)
        shot.application = app
        shot.created_by = request.user
        shot.updated_by = request.user
        shot.save()
        messages.success(request, 'Capture ajoutée.')
    else:
        messages.error(request, 'Capture invalide.')
    return redirect('web:appstore_admin_app', pk=app.pk)


@appstore_admin_required
@require_POST
def admin_screenshot_delete(request, pk, shot_id):
    shot = get_object_or_404(AppScreenshot, pk=shot_id, application_id=pk)
    shot.delete()
    messages.success(request, 'Capture supprimée.')
    return redirect('web:appstore_admin_app', pk=pk)


@appstore_admin_required
@require_http_methods(['GET', 'POST'])
def admin_version_edit(request, app_id, pk=None):
    app = get_object_or_404(SoftwareApp, pk=app_id)
    instance = get_object_or_404(AppVersion, pk=pk, application=app) if pk else None
    form = AppVersionForm(request.POST or None, instance=instance)
    if request.method == 'POST' and form.is_valid():
        version = form.save(commit=False)
        version.application = app
        if not instance:
            version.created_by = request.user
        version.updated_by = request.user
        version.save()
        messages.success(request, 'Version enregistrée.')
        return redirect('web:appstore_admin_version', app_id=app.pk, pk=version.pk)
    file_form = AppReleaseFileForm() if instance else None
    files = instance.files.all() if instance else []
    return render(request, 'appstore/admin/version_form.html', {
        'form': form,
        'app': app,
        'version': instance,
        'file_form': file_form,
        'files': files,
    })


@appstore_admin_required
@require_POST
def admin_version_publish(request, app_id, pk):
    version = get_object_or_404(AppVersion, pk=pk, application_id=app_id)
    set_recommended = request.POST.get('set_recommended') == '1'
    try:
        publish_version(version, set_recommended=set_recommended)
        messages.success(request, f'Version {version.version_number} publiée.')
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc))
    return redirect('web:appstore_admin_version', app_id=app_id, pk=pk)


@appstore_admin_required
@require_POST
def admin_version_withdraw(request, app_id, pk):
    version = get_object_or_404(AppVersion, pk=pk, application_id=app_id)
    withdraw_version(version)
    messages.success(request, f'Version {version.version_number} retirée.')
    return redirect('web:appstore_admin_version', app_id=app_id, pk=pk)


@appstore_admin_required
@require_POST
def admin_set_recommended(request, app_id, pk):
    app = get_object_or_404(SoftwareApp, pk=app_id)
    version = get_object_or_404(AppVersion, pk=pk, application=app)
    if version.status != AppVersion.Status.PUBLISHED:
        messages.error(request, 'Seule une version publiée peut être recommandée.')
    else:
        app.recommended_version = version
        app.updated_by = request.user
        app.save(update_fields=['recommended_version', 'updated_by', 'updated_at'])
        messages.success(request, 'Version stable recommandée mise à jour.')
    return redirect('web:appstore_admin_version', app_id=app_id, pk=pk)


@appstore_admin_required
@require_POST
def admin_file_upload(request, app_id, version_id):
    version = get_object_or_404(AppVersion, pk=version_id, application_id=app_id)
    form = AppReleaseFileForm(request.POST, request.FILES)
    if not form.is_valid():
        messages.error(request, 'Fichier invalide.')
        return redirect('web:appstore_admin_version', app_id=app_id, pk=version_id)
    package = form.cleaned_data.get('package')
    if not package:
        messages.error(request, 'Sélectionnez un fichier à téléverser.')
        return redirect('web:appstore_admin_version', app_id=app_id, pk=version_id)
    release = form.save(commit=False)
    release.version = version
    release.created_by = request.user
    release.updated_by = request.user
    try:
        # Save shell row first for unique constraint, then attach blob.
        release.save()
        attach_package(release, package, approve=bool(form.cleaned_data.get('approve_now')))
        messages.success(request, 'Fichier enregistré.')
    except ValidationError as exc:
        if release.pk:
            release.delete()
        messages.error(request, '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc))
    except Exception as exc:
        if release.pk and not release.file:
            release.delete()
        messages.error(request, str(exc))
    return redirect('web:appstore_admin_version', app_id=app_id, pk=version_id)


@appstore_admin_required
@require_POST
def admin_file_approve(request, app_id, version_id, file_id):
    release = get_object_or_404(AppReleaseFile, pk=file_id, version_id=version_id, version__application_id=app_id)
    try:
        approve_release_file(release)
        messages.success(request, 'Fichier approuvé.')
    except ValidationError as exc:
        messages.error(request, '; '.join(exc.messages) if hasattr(exc, 'messages') else str(exc))
    return redirect('web:appstore_admin_version', app_id=app_id, pk=version_id)


@appstore_admin_required
@require_POST
def admin_file_reject(request, app_id, version_id, file_id):
    release = get_object_or_404(AppReleaseFile, pk=file_id, version_id=version_id, version__application_id=app_id)
    reject_release_file(release)
    messages.success(request, 'Fichier rejeté.')
    return redirect('web:appstore_admin_version', app_id=app_id, pk=version_id)


@appstore_admin_required
@require_http_methods(['GET', 'POST'])
def admin_categories(request):
    form = AppCategoryForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        cat = form.save(commit=False)
        cat.created_by = request.user
        cat.updated_by = request.user
        cat.save()
        messages.success(request, 'Catégorie créée.')
        return redirect('web:appstore_admin_categories')
    return render(request, 'appstore/admin/categories.html', {
        'form': form,
        'categories': AppCategory.objects.all(),
    })


@appstore_admin_required
@require_http_methods(['GET', 'POST'])
def admin_category_edit(request, pk):
    category = get_object_or_404(AppCategory, pk=pk)
    form = AppCategoryForm(request.POST or None, instance=category)
    if request.method == 'POST' and form.is_valid():
        cat = form.save(commit=False)
        cat.updated_by = request.user
        cat.save()
        messages.success(request, 'Catégorie mise à jour.')
        return redirect('web:appstore_admin_categories')
    return render(request, 'appstore/admin/category_form.html', {'form': form, 'category': category})


@appstore_admin_required
@require_http_methods(['GET', 'POST'])
def admin_announcements(request):
    form = AppAnnouncementForm(request.POST or None, request.FILES or None)
    if request.method == 'POST' and form.is_valid():
        item = form.save(commit=False)
        item.created_by = request.user
        item.updated_by = request.user
        if item.status == AppAnnouncement.Status.PUBLISHED and not item.published_at:
            item.published_at = timezone.now()
        item.save()
        messages.success(request, 'Annonce enregistrée.')
        return redirect('web:appstore_admin_announcements')
    return render(request, 'appstore/admin/announcements.html', {
        'form': form,
        'announcements': AppAnnouncement.objects.select_related('application', 'version').all(),
    })


@appstore_admin_required
@require_http_methods(['GET', 'POST'])
def admin_announcement_edit(request, pk):
    item = get_object_or_404(AppAnnouncement, pk=pk)
    form = AppAnnouncementForm(request.POST or None, request.FILES or None, instance=item)
    if request.method == 'POST' and form.is_valid():
        ann = form.save(commit=False)
        ann.updated_by = request.user
        if ann.status == AppAnnouncement.Status.PUBLISHED and not ann.published_at:
            ann.published_at = timezone.now()
        ann.save()
        messages.success(request, 'Annonce mise à jour.')
        return redirect('web:appstore_admin_announcements')
    return render(request, 'appstore/admin/announcement_form.html', {'form': form, 'announcement': item})


@appstore_admin_required
@require_POST
def admin_announcement_publish(request, pk):
    item = get_object_or_404(AppAnnouncement, pk=pk)
    publish_announcement(item)
    messages.success(request, 'Annonce publiée.')
    return redirect('web:appstore_admin_announcements')


@appstore_admin_required
@require_POST
def admin_announcement_archive(request, pk):
    item = get_object_or_404(AppAnnouncement, pk=pk)
    archive_announcement(item)
    messages.success(request, 'Annonce archivée.')
    return redirect('web:appstore_admin_announcements')


@appstore_admin_required
@require_GET
def admin_stats(request):
    return render(request, 'appstore/admin/stats.html', {
        'stats_30': download_stats(days=30),
        'stats_all': download_stats(),
    })
