from sport_analysis.eoy_recap.eoy_recap_2026S1.main import EoyRecap2026S1


class TestEoyRecap2026S1Api:
    def test_happy_flow(self):
        eoy = EoyRecap2026S1()
        eoy.plot()
