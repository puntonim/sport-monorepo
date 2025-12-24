from sport_analysis.eoy_recap.eoy_recap_2025.main import EoyRecap2025


class TestEoyRecap2025Api:
    def test_happy_flow(self):
        eoy = EoyRecap2025()
        eoy.plot()
