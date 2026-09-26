import pytest
from fastapi.testclient import TestClient

# Une base injoignable : le port 1 refuse toute connexion, tout de suite.
DOWN_PASSWORD = "mot-de-passe-qui-ne-doit-jamais-sortir"
DOWN_URL = f"postgresql://hellofedge:{DOWN_PASSWORD}@127.0.0.1:1/hellofedge"


@pytest.fixture
def make_client(monkeypatch, tmp_path):
    """Construit l'api avec l'environnement voulu, cycle de vie compris (démarrage, arrêt)."""
    clients = []

    def _make(database_url: str, frontend_dist=None) -> TestClient:
        monkeypatch.setenv("DATABASE_URL", database_url)
        monkeypatch.setenv("FRONTEND_DIST", str(frontend_dist or tmp_path / "absent"))
        from hellofedge.api.app import create_app

        client = TestClient(create_app())
        client.__enter__()
        clients.append(client)
        return client

    yield _make
    for client in clients:
        client.__exit__(None, None, None)


@pytest.fixture
def cockpit_dist(tmp_path):
    dist = tmp_path / "dist"
    (dist / "assets").mkdir(parents=True)
    (dist / "index.html").write_text(
        "<!doctype html><title>Hellofedge</title>", encoding="utf-8"
    )
    (dist / "assets" / "app.js").write_text("console.log('cockpit')", encoding="utf-8")
    return dist


class TestHealth:
    def test_reports_ok_when_the_database_answers(self, make_client, db_url):
        response = make_client(db_url).get("/api/health")

        assert response.status_code == 200
        assert response.json() == {"status": "ok", "database": "ok"}

    def test_reports_503_when_the_database_is_unreachable(self, make_client):
        response = make_client(DOWN_URL).get("/api/health")

        assert response.status_code == 503
        assert response.json() == {"status": "error", "database": "down"}

    def test_never_leaks_the_database_password_when_the_database_is_down(
        self, make_client, capsys
    ):
        response = make_client(DOWN_URL).get("/api/health")

        assert DOWN_PASSWORD not in response.text
        assert DOWN_PASSWORD not in capsys.readouterr().out

    def test_logs_the_database_failure_as_an_error(self, make_client, capsys):
        make_client(DOWN_URL).get("/api/health")

        assert '"msg": "base injoignable"' in capsys.readouterr().out

    def test_only_answers_get(self, make_client):
        response = make_client(DOWN_URL).post("/api/health")

        assert response.status_code == 405


class TestCockpitFiles:
    def test_serves_the_cockpit_page_at_the_root(self, make_client, cockpit_dist):
        response = make_client(DOWN_URL, cockpit_dist).get("/")

        assert response.status_code == 200
        assert "<title>Hellofedge</title>" in response.text

    def test_serves_the_built_assets(self, make_client, cockpit_dist):
        response = make_client(DOWN_URL, cockpit_dist).get("/assets/app.js")

        assert response.status_code == 200
        assert "cockpit" in response.text

    def test_the_cockpit_never_hides_the_api_routes(self, make_client, cockpit_dist):
        response = make_client(DOWN_URL, cockpit_dist).get("/api/health")

        assert response.headers["content-type"].startswith("application/json")
        assert response.json()["database"] == "down"

    def test_an_unknown_api_path_is_a_404_not_the_cockpit_page(
        self, make_client, cockpit_dist
    ):
        response = make_client(DOWN_URL, cockpit_dist).get("/api/inconnu")

        assert response.status_code == 404
        assert "<title>" not in response.text

    def test_starts_without_cockpit_files_and_answers_404_at_the_root(
        self, make_client
    ):
        client = make_client(DOWN_URL)

        assert client.get("/").status_code == 404
        assert client.get("/api/health").status_code == 503
