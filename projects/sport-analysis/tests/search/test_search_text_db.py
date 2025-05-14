from sport_analysis.search.search_text_db import search_text_db


class TestSearchText:
    def test_1(self, create_db_fixture):
        activities = list(search_text_db("MORtirolo"))
        assert len(activities) == 5
        for activity in activities:
            try:
                assert "mortirolo" in activity.name.lower()
            except AssertionError:
                assert "mortirolo" in activity.description.lower()
