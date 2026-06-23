from src import server


def test_demo_mode_returns_listings(monkeypatch):
    monkeypatch.setattr(server, "APIFY_TOKEN", "")
    monkeypatch.setattr(server, "ACTOR_ID", "")
    res = server._search(make="BMW", limit=3)
    assert res["demo"] is True
    assert len(res["listings"]) == 3
    assert res["listings"][0]["url"].startswith("http")
    assert "price_eur" in res["listings"][0]


def test_free_limit_caps_results(monkeypatch):
    monkeypatch.setattr(server, "APIFY_TOKEN", "")
    monkeypatch.setattr(server, "FREE_LIMIT", 5)
    res = server._search(limit=100)
    assert len(res["listings"]) <= 5


def test_live_path_maps_input_and_normalizes(monkeypatch):
    """With token+actor set, it should call the actor and normalize output."""
    captured = {}

    class FakeDatasetClient:
        def list_items(self, limit=None):
            class R:
                items = [
                    {"make": "BMW", "model": "320d", "year": 2019, "price_eur": 21900,
                     "mileage_km": 98000, "url": "https://x/1", "junk": "drop me"},
                ]
            return R()

    class FakeActorClient:
        def call(self, run_input=None):
            captured["run_input"] = run_input
            return {"defaultDatasetId": "ds1"}

    class FakeClient:
        def __init__(self, token):
            captured["token"] = token

        def actor(self, actor_id):
            captured["actor_id"] = actor_id
            return FakeActorClient()

        def dataset(self, ds_id):
            return FakeDatasetClient()

    import apify_client
    monkeypatch.setattr(apify_client, "ApifyClient", FakeClient)
    monkeypatch.setattr(server, "APIFY_TOKEN", "tok")
    monkeypatch.setattr(server, "ACTOR_ID", "me/mobile-de-scraper")

    res = server._search(make="BMW", fuel="diesel", transmission="automatic", limit=1)
    assert captured["token"] == "tok"
    assert captured["actor_id"] == "me/mobile-de-scraper"
    assert captured["run_input"]["fuel"] == "DIESEL"
    assert captured["run_input"]["transmission"] == "AUTOMATIC_GEAR"
    assert captured["run_input"]["make"] == "BMW"
    assert res["listings"][0] == {
        "make": "BMW", "model": "320d", "year": 2019,
        "mileage_km": 98000, "price_eur": 21900, "url": "https://x/1",
    }


def test_fuel_and_transmission_maps():
    assert server._FUEL_MAP["diesel"] == "DIESEL"
    assert server._FUEL_MAP["electric"] == "ELECTRICITY"
    assert server._TRANS_MAP["automatic"] == "AUTOMATIC_GEAR"
