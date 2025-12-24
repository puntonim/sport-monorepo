**END OF YER RECAP 2026 SEMESTER 1**
====================================

This script creates a PNG image with the END OF YEAR recap.

Note: it is run via a test so we can leverage VCR.py and record HTTP interactions.

Usage
=====
```sh
$ IS_VCR_EPISODE_OR_ERROR=n pytest -s tests/eoy_recap/test_eoy_recap_2026S1_api.py
```

How to create the next EOY recap
================================
- Duplicate the dir `sport_analysis/eoy_recap/eoy_recap_2026S1` naming the dir properly
   and renaming the class `main.py::EoyRecap2026S1` properly.
- Duplicate the file `tests/eoy_recap/test_eoy_recap_2026S1_api.py` naming it properly.
- Edit the `start_date_after|before` in `main.py`.
- Edit the PRS in `sport_analysis/eoy_recap/eoy_recap_2026S1/stats_weight_training.py`
   and check the TODO to reposition the text.
- Edit the PRS and HR_MAX in `sport_analysis/eoy_recap/eoy_recap_2026S1/stats_run.py`.
   and check the TODOs to reposition the text and fix overlapping labels.
- Edit the PRS and HR_MAX in `sport_analysis/eoy_recap/eoy_recap_2026S1/stats_ride.py`.
   and check the TODOs to reposition the text and fix overlapping labels.
- Download the weight CSV file from Renpho scale (see info in `stats_weight.py`)
   then check all TODOs in `sport_analysis/eoy_recap/eoy_recap_2026S1/stats_weight.py`.
- Run the test to create the image:
  `$ IS_VCR_EPISODE_OR_ERROR=n pytest -s tests/eoy_recap/test_eoy_recap_2026S1_api.py`
