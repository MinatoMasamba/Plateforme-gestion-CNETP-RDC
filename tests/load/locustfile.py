"""Test de charge Locust pour la plateforme CNETP.

Simule des experts authentifiés (comptes seedés) qui consultent les normes,
créent des versions, génèrent des PDF, envoient des messages et consultent les KPIs.

Lancement :
    locust -f tests/load/locustfile.py --headless -u 30 -r 5 -t 90s \
        --host http://localhost:8000 --html reports/load_report.html
"""
import itertools
import re
import threading

from locust import HttpUser, between, task


BASE = 'http://localhost:8000'
PASSWORD = 'Cnetp2026!'
ACCOUNTS = [f'expert{i}@cnetp.cd' for i in range(1, 12)]

_counter = itertools.count()
_lock = threading.Lock()


def _next_account():
    with _lock:
        return ACCOUNTS[next(_counter) % len(ACCOUNTS)]


class ExpertUser(HttpUser):
    host = BASE
    wait_time = between(0.5, 2.0)

    def on_start(self):
        self.email = _next_account()
        self.norme_id = None
        self.contact_ids = []
        self.csrf = None
        self.login()

    def login(self):
        resp = self.client.get('/se-connecter/', name='/se-connecter/')
        match = re.search(r'name="csrfmiddlewaretoken" value="([^"]+)"', resp.text)
        self.csrf = match.group(1) if match else (self.client.cookies.get('csrftoken') or '')
        self.client.post(
            '/se-connecter/',
            data={'email': self.email, 'password': PASSWORD, 'csrfmiddlewaretoken': self.csrf},
            headers={'Referer': f'{BASE}/se-connecter/'},
            name='/se-connecter/ (POST)',
        )
        self._load_normes()
        self._load_contacts()

    def _headers(self):
        return {'X-CSRFToken': self.client.cookies.get('csrftoken', self.csrf or ''),
                'Referer': BASE}

    def _load_normes(self):
        resp = self.client.get('/api/v1/norms/?page_size=20', name='/api/v1/norms/')
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('results', data) if isinstance(data, dict) else data
            if results:
                self.norme_id = results[0]['id']

    def _load_contacts(self):
        resp = self.client.get('/api/v1/messages/contacts/', name='/api/v1/messages/contacts/')
        if resp.status_code == 200:
            data = resp.json()
            results = data.get('results', data) if isinstance(data, dict) else data
            self.contact_ids = [c['user_id'] for c in results][:10]

    @task(5)
    def list_norms(self):
        self.client.get('/api/v1/norms/?page_size=20', name='/api/v1/norms/')

    @task(3)
    def norme_detail(self):
        if self.norme_id:
            self.client.get(f'/api/v1/norms/{self.norme_id}/', name='/api/v1/norms/{id}/')

    @task(2)
    def create_version(self):
        if self.norme_id:
            self.client.post(
                f'/api/v1/norms/{self.norme_id}/create_version/',
                json={'title': 'Charge E2E', 'content': 'Section 1\nContenu charge.',
                      'comment': 'locust'},
                headers=self._headers(),
                name='/api/v1/norms/{id}/create_version/',
            )

    @task(2)
    def download_pdf(self):
        if self.norme_id:
            self.client.get(f'/api/v1/norms/{self.norme_id}/pdf/',
                            name='/api/v1/norms/{id}/pdf/')

    @task(3)
    def send_message(self):
        if self.contact_ids:
            rid = self.contact_ids[_counter.__next__() % len(self.contact_ids)]
            self.client.post(
                '/api/v1/messages/',
                json={'receiver_id': rid, 'content': 'Message de charge Locust.'},
                headers=self._headers(),
                name='/api/v1/messages/',
            )

    @task(2)
    def dashboard_kpis(self):
        self.client.get('/api/v1/dashboard/kpis/kpis/', name='/api/v1/dashboard/kpis/kpis/')

    @task(1)
    def unread_count(self):
        self.client.get('/api/v1/messages/unread_count/', name='/api/v1/messages/unread_count/')
