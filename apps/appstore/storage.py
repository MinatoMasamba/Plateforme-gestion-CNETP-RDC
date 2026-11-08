"""Stockage privé des binaires distribués par l'App Store."""


def appstore_private_storage():
    from django.conf import settings
    from django.core.files.storage import FileSystemStorage

    root = settings.BASE_DIR / '.appstore_packages'
    root.mkdir(parents=True, exist_ok=True)
    return FileSystemStorage(
        location=root,
        file_permissions_mode=0o600,
        directory_permissions_mode=0o700,
    )


def package_upload_to(instance, filename):
    safe = (filename or 'package.bin').replace('\\', '/').split('/')[-1]
    safe = ''.join(ch for ch in safe if ch.isalnum() or ch in '._-')[:180] or 'package.bin'
    app_slug = getattr(getattr(instance, 'version', None), 'application', None)
    app_part = getattr(app_slug, 'slug', 'app') or 'app'
    version_part = getattr(instance.version, 'version_number', '0') or '0'
    platform = getattr(instance, 'platform', 'any') or 'any'
    return f'{app_part}/{version_part}/{platform}/{safe}'
