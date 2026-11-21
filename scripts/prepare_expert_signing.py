"""Créer une clé bêta privée persistante ; ne jamais la téléverser avec l'APK."""
import os
from pathlib import Path
import secrets
import subprocess

root = Path(__file__).resolve().parents[1]
directory = root / '.private_build'
directory.mkdir(mode=0o700, exist_ok=True)
properties = root / 'flutter_app/android/key.properties'
if properties.exists():
    raise SystemExit('Configuration de signature existante conservée.')
keystore = directory / 'cne-itp-expert-beta.p12'
if keystore.exists():
    raise SystemExit('Clé existante : restaurer sa configuration, sans écrasement.')
password = secrets.token_urlsafe(32)
env = dict(os.environ, CNE_EXPERT_SIGN_PASSWORD=password)
subprocess.run([
    '/home/minato/android-studio/jbr/bin/keytool', '-genkeypair', '-noprompt',
    '-keystore', str(keystore), '-storetype', 'PKCS12',
    '-storepass:env', 'CNE_EXPERT_SIGN_PASSWORD', '-keypass:env', 'CNE_EXPERT_SIGN_PASSWORD',
    '-alias', 'expert-beta', '-keyalg', 'RSA', '-keysize', '3072', '-validity', '3650',
    '-dname', 'CN=CNE-ITP Expert Beta',
], env=env, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
keystore.chmod(0o600)
fd = os.open(properties, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
with os.fdopen(fd, 'w') as stream:
    stream.write(f'storeFile={keystore}\nstorePassword={password}\nkeyPassword={password}\nkeyAlias=expert-beta\n')
print('Clé bêta créée dans .private_build ; configuration Android privée créée.')
