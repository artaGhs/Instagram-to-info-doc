from pathlib import Path

from instagram_to_info_doc.instagram import authenticate_loader


class _FakeSession:
    def __init__(self):
        import requests

        self.cookies = requests.cookies.RequestsCookieJar()


class _FakeContext:
    def __init__(self):
        self._session = _FakeSession()


class _FakeLoader:
    def __init__(self):
        self.context = _FakeContext()
        self.loaded = None
        self.logged_in = None
        self.saved = None

    def load_session_from_file(self, username, filename):
        self.loaded = (username, filename)

    def login(self, username, password):
        self.logged_in = (username, password)

    def save_session_to_file(self, filename):
        self.saved = filename


def test_auth_uses_session_file_if_present(tmp_path: Path):
    loader = _FakeLoader()
    sf = tmp_path / "ig.session"
    sf.write_text("dummy", encoding="utf-8")

    authenticate_loader(loader, "u", None, sf, None)

    assert loader.loaded == ("u", str(sf))
    assert loader.logged_in is None


def test_auth_login_and_saves_session(tmp_path: Path):
    loader = _FakeLoader()
    sf = tmp_path / "saved.session"

    authenticate_loader(loader, "u", "p", sf, None)

    assert loader.logged_in == ("u", "p")
    assert loader.saved == str(sf)


def test_auth_loads_instagram_cookie_file(tmp_path: Path):
    loader = _FakeLoader()
    cookie_file = tmp_path / "cookies.txt"
    cookie_file.write_text(
        "# Netscape HTTP Cookie File\n"
        ".instagram.com\tTRUE\t/\tTRUE\t2147483647\tsessionid\tabc123\n",
        encoding="utf-8",
    )

    authenticate_loader(loader, None, None, None, cookie_file)

    assert loader.context._session.cookies.get("sessionid") == "abc123"
