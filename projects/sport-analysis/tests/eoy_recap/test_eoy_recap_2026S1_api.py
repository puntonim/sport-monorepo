import pytest

from sport_analysis.conf.settings_module import ROOT_DIR
from sport_analysis.eoy_recap.eoy_recap_2026S1.main import cli_cmd


class TestEoyRecap2026S1Api:
    # Do not use VCR.py because it is already used in the live code.
    @pytest.mark.novcr
    def test_happy_flow(self):
        cli_cmd(
            ROOT_DIR
            / "tests"
            / "test-output-images"
            / (self.__class__.__name__ + ".png")
        )
