from abc import ABC, abstractmethod

# I used a website to generate a palette:
#  https://www.learnui.design/tools/data-color-picker.html#divergent
COLORS_TEAL_TO_RED = (
    "#122740",
    "#1b485e",
    "#326b77",
    "#568b87",
    "#80ae9a",
    "#b5d1ae",
    "#cdcbd1",
    "#c6b8ce",
    "#c8a3c5",
    "#ce8bb4",
    "#d5729a",
    "#d85778",
    "#de425b",
)

# The size of the right margin of a bar, so the space between the bar and its label.
BAR_MARGIN_R = 0.3


class BaseStats(ABC):
    @abstractmethod
    def add_activity_summary(self, activity): ...

    @abstractmethod
    def finalize_stats(self): ...

    @abstractmethod
    def print_stats(self): ...

    @abstractmethod
    def plot(self, *args, **kwargs): ...
