from sport_analysis.plot.base_plot import _make_percentile_text

HR_MIN = 46
HR_MAX = 174
"""
American HR Zones
  <50%    50-60%   60-70%    70-80%    80-90%     ≥90%
  46-86   87-103   104-121   122-138   139-156   157-174
   Z0       Z1       Z2        Z3        Z4        Z5
"""


class TestMakePercentileText:
    def test_p80_119(self):
        percentile_perc = 80
        percentile_bpm = 119
        bpm_diff_left = percentile_bpm - 103  # The right boundary of the prev zone.
        zone_num = 2
        zone_bpm_range = (104, 121)
        text = _make_percentile_text(
            percentile_perc=percentile_perc,
            percentile_bpm=percentile_bpm,
            hr_min=HR_MIN,
            hr_max=HR_MAX,
        )
        t = f"P{percentile_perc} at {percentile_bpm}bpm"
        t += f" | {round(percentile_bpm * 100 / HR_MAX)}% max HR"
        p_in_zone = round(
            (bpm_diff_left - 1) * 100 / (zone_bpm_range[1] - zone_bpm_range[0])
        )
        t += f" | P{p_in_zone} Z{zone_num}"
        t += f" | Z3-3bpm"
        assert text.plain_txt == t

    def test_p80_123(self):
        percentile_perc = 80
        percentile_bpm = 123
        bpm_diff_left = percentile_bpm - 121  # The right boundary of the prev zone.
        zone_num = 3
        zone_bpm_range = (122, 138)
        text = _make_percentile_text(
            percentile_perc=percentile_perc,
            percentile_bpm=percentile_bpm,
            hr_min=HR_MIN,
            hr_max=HR_MAX,
        )
        t = f"P{percentile_perc} at {percentile_bpm}bpm"
        t += f" | {round(percentile_bpm * 100 / HR_MAX)}% max HR"
        p_in_zone = round(
            (bpm_diff_left - 1) * 100 / (zone_bpm_range[1] - zone_bpm_range[0])
        )
        t += f" | P{p_in_zone} Z{zone_num}"
        t += f" | Z2+2bpm"
        assert text.plain_txt == t

    def test_p80_122(self):
        percentile_perc = 80
        percentile_bpm = 122
        bpm_diff_left = percentile_bpm - 121  # The right boundary of the prev zone.
        zone_num = 3
        zone_bpm_range = (122, 138)
        text = _make_percentile_text(
            percentile_perc=percentile_perc,
            percentile_bpm=percentile_bpm,
            hr_min=HR_MIN,
            hr_max=HR_MAX,
        )
        t = f"P{percentile_perc} at {percentile_bpm}bpm"
        t += f" | {round(percentile_bpm * 100 / HR_MAX)}% max HR"
        p_in_zone = round(
            (bpm_diff_left - 1) * 100 / (zone_bpm_range[1] - zone_bpm_range[0])
        )
        t += f" | P{p_in_zone} Z{zone_num}"
        t += f" | Z2+1bpm"
        assert text.plain_txt == t

    def test_p80_121(self):
        percentile_perc = 80
        percentile_bpm = 121
        bpm_diff_left = percentile_bpm - 103  # The right boundary of the prev zone.
        zone_num = 2
        zone_bpm_range = (104, 121)
        text = _make_percentile_text(
            percentile_perc=percentile_perc,
            percentile_bpm=percentile_bpm,
            hr_min=HR_MIN,
            hr_max=HR_MAX,
        )
        t = f"P{percentile_perc} at {percentile_bpm}bpm"
        t += f" | {round(percentile_bpm * 100 / HR_MAX)}% max HR"
        p_in_zone = round(
            (bpm_diff_left - 1) * 100 / (zone_bpm_range[1] - zone_bpm_range[0])
        )
        t += f" | P{p_in_zone} Z{zone_num}"
        t += f" | Z3-1bpm"
        assert text.plain_txt == t

    def test_p98_119(self):
        percentile_perc = 98
        percentile_bpm = 142
        bpm_diff_left = percentile_bpm - 138  # The right boundary of the prev zone.
        zone_num = 4
        zone_bpm_range = (139, 156)
        text = _make_percentile_text(
            percentile_perc=percentile_perc,
            percentile_bpm=percentile_bpm,
            hr_min=HR_MIN,
            hr_max=HR_MAX,
        )
        t = f"P{percentile_perc} at {percentile_bpm}bpm"
        t += f" | {round(percentile_bpm * 100 / HR_MAX)}% max HR"
        p_in_zone = round(
            (bpm_diff_left - 1) * 100 / (zone_bpm_range[1] - zone_bpm_range[0])
        )
        t += f" | P{p_in_zone} Z{zone_num}"
        t += f" | Z3+4bpm"
        assert text.plain_txt == t
