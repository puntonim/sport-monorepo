from datetime import datetime

from garmin_connect_client import GarminConnectClient


class TestListActivities:
    def test_happy_flow(self):
        client = GarminConnectClient()
        activities = client.list_activities("2025-03-22")
        assert len(activities["ActivitiesForDay"]["payload"]) == 2
        assert activities["ActivitiesForDay"]["payload"][0]["activityId"] == 18603794245
        assert (
            activities["ActivitiesForDay"]["payload"][0]["activityName"] == "Strength"
        )
        assert activities["ActivitiesForDay"]["payload"][1]["activityId"] == 18606916834
        assert (
            activities["ActivitiesForDay"]["payload"][1]["activityName"]
            == "Limone Piemonte Trail Running"
        )

    def test_datetime(self):
        client = GarminConnectClient()
        activities = client.list_activities(datetime(2025, 3, 22))
        assert len(activities["ActivitiesForDay"]["payload"]) == 2
        assert activities["ActivitiesForDay"]["payload"][0]["activityId"] == 18603794245
        assert (
            activities["ActivitiesForDay"]["payload"][0]["activityName"] == "Strength"
        )
        assert activities["ActivitiesForDay"]["payload"][1]["activityId"] == 18606916834
        assert (
            activities["ActivitiesForDay"]["payload"][1]["activityName"]
            == "Limone Piemonte Trail Running"
        )


class TestGetActivitySummary:
    def test_happy_flow(self):
        client = GarminConnectClient()
        activity_id = 18606916834
        summary = client.get_activity_summary(activity_id)
        assert summary["activityId"] == activity_id
        assert summary["activityName"] == "Limone Piemonte Trail Running"


class TestGetActivityDetails:
    def test_happy_flow(self):
        client = GarminConnectClient()
        activity_id = 18606916834
        details = client.get_activity_details(
            activity_id,
            max_metrics_data_count=50,
            do_include_polyline=False,
            # max_polyline_count: int = 4000,
            do_keep_raw_response=False,
        )
        from pprint import pprint

        import ipdb

        ipdb.set_trace()
        assert details
