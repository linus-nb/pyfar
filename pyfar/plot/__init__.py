# -*- coding: utf-8 -*-

"""Plot sub-package for pyfar."""

from .line import (
    freq,
    time,
    phase,
    group_delay,
    spectrogram,
    time_freq,
    freq_phase,
    freq_group_delay,
    custom_subplots
)
from .spatial import (
    scatter,
    quiver
)

from . import utils

__all__ = [
    freq,
    time,
    phase,
    group_delay,
    spectrogram,
    time_freq,
    freq_phase,
    freq_group_delay,
    custom_subplots,
    scatter,
    quiver,
    utils
]
