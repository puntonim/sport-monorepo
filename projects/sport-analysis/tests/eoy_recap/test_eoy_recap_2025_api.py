from sport_analysis.eoy_recap.eoy_recap_2025_api import EoyRecap2025Api


class TestEoyRecap2025Api:
    def test_happy_flow(self):
        eoy = EoyRecap2025Api(
            # TODO Now it's 15 Dec, but at the ned of the year I have to remove this
            #  line so as to use the default 31 Dec.
            start_date_before="2025-12-14T23:59:59+01:00",
        )
        eoy.plot()
