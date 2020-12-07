"""
Provide a Container class and arithmethic operations for audio signals.

Arithmetic operations can be done on the time and frequency domain data. They
are implemented in `add`, `subtract`, `multiply`, `divide`, and `power`. The
operators `+`, `-`, `*`, `/`, and `**` are overloaded with the corresponding
arithmetic operations in the frequency domain. For time domain operations, the
functions have to be called explicitly. These the function documentation for
more details.
"""

import warnings
import numpy as np
from pyfar import fft as fft
from typing import Callable


class Audio(object):
    """Abstract class for audio objects."""

    def __init__(self):
        """TODO: to be defined1. """


class Signal(Audio):
    """Class for audio signals.

    Objects of this class contain data which is directly convertable between
    time and frequency domain. Equally spaced samples or frequency bins,
    respectively.

    Attributes
    ----------
    data : ndarray, double
        Raw data of the signal in the frequency or time domain
    sampling_rate : double
        Sampling rate in Hertz
    n_samples : int, optional
        Number of samples of the time signal. Required if domain is 'freq'. The
        default is None.
    domain : 'time', 'freq', optional
        Domain of data. The default is 'time'
    signal_type : 'energy', 'power', optional
        Energy signals are finite and have finite energy. An example for an
        energy signal is an impulse response. Power signals are infinite and
        have infinite energy. Examples are noise and sine signals. The default
        is 'energy'
    fft_norm : 'unitary', 'amplitude', 'rms', 'power', 'psd', optional
        The kind of Discrete Fourier Transform (DFT) normalization. See
        pyfar.fft.normalization for more information. The normalization is
        only applied to power signals. The default is 'unitary' for energy
        signals and 'rms' for power signals.
    dtype : string, optional
        Raw data type of the signal. The default is float64

    """
    def __init__(
            self,
            data,
            sampling_rate,
            n_samples=None,
            domain='time',
            signal_type='energy',
            fft_norm=None,
            dtype=np.double,
            comment=None):
        """Init Signal with data, and sampling rate.

        Attributes
        ----------
        data : ndarray, double
            Raw data of the signal in the frequency or time domain
        sampling_rate : double
            Sampling rate in Hertz
        n_samples : int, optional
            Number of samples of the time signal. Required if domain is 'freq'.
            The default is None.
        domain : 'time', 'freq', optional
            Domain of data. The default is 'time'
        signal_type : 'energy', 'power', optional
            Energy signals are finite and have finite energy. An example for an
            energy signal is an impulse response. Power signals are infinite
            and have infinite energy. Examples are noise and sine signals. The
            default is 'energy'
        fft_norm : 'unitary', 'amplitude', 'rms', 'power', 'psd', optional
            The kind of Discrete Fourier Transform (DFT) normalization. See
            pyfar.fft.normalization for more information. The normalization is
            only applied to power signals. The default is 'unitary' for energy
            signals and 'rms' for power signals.
        dtype : string, optional
            Raw data type of the signal. The default is float64

        """

        Audio.__init__(self)
        self._sampling_rate = sampling_rate
        self._dtype = dtype

        self._VALID_SIGNAL_TYPE = ["power", "energy"]
        if (signal_type in self._VALID_SIGNAL_TYPE) is True:
            self._signal_type = signal_type
        else:
            raise ValueError("Not a valid signal type ('power'/'energy')")

        self._VALID_SIGNAL_DOMAIN = ["time", "freq"]
        if domain in self._VALID_SIGNAL_DOMAIN:
            self._domain = domain
        else:
            raise ValueError("Invalid domain. Has to be 'time' or 'freq'.")

        if domain == 'time':
            self._data = np.atleast_2d(np.asarray(data, dtype=dtype))
            self._n_samples = self._data.shape[-1]
        elif domain == 'freq':
            if n_samples is None:
                warnings.warn(
                    "Number of time samples not given, assuming an even "
                    "number of samples from the number of frequency bins.")
                n_bins = data.shape[-1]
                n_samples = (n_bins - 1)*2
            self._n_samples = n_samples
            self._data = np.atleast_2d(np.asarray(data, dtype=np.complex))

        self._VALID_FFT_NORMS = ["unitary", "amplitude", "rms", "power", "psd"]
        if fft_norm is None:
            fft_norm = 'unitary' if signal_type == 'energy' else 'rms'
        if fft_norm in self._VALID_FFT_NORMS:
            self._fft_norm = fft_norm
            self.fft_norm = fft_norm
        else:
            raise ValueError(("Invalid FFT normalization. Has to be "
                              f"{', '.join(self._VALID_FFT_NORMS)}, but found "
                              f"'{fft_norm}'"))

        self._comment = comment

    @property
    def domain(self):
        """The domain the data is stored in"""
        return self._domain

    @domain.setter
    def domain(self, new_domain):
        if new_domain not in self._VALID_SIGNAL_DOMAIN:
            raise ValueError("Incorrect domain, needs to be time/freq.")

        if not (self._domain == new_domain):
            # Only process if we change domain
            if new_domain == 'time':
                # If the new domain should be time, we had a saved spectrum
                # and need to do an inverse Fourier Transform
                self.time = fft.irfft(
                    self._data, self.n_samples, self._sampling_rate,
                    self._signal_type, self._fft_norm)
            elif new_domain == 'freq':
                # If the new domain should be freq, we had sampled time data
                # and need to do a Fourier Transform
                self.freq = fft.rfft(
                    self._data, self.n_samples, self._sampling_rate,
                    self._signal_type, self._fft_norm)

    @property
    def n_samples(self):
        """Number of samples."""
        return self._n_samples

    @property
    def n_bins(self):
        """Number of frequency bins."""
        return fft._n_bins(self.n_samples)

    @property
    def frequencies(self):
        """Frequencies of the discrete signal spectrum."""
        return np.atleast_1d(fft.rfftfreq(self.n_samples, self.sampling_rate))

    @property
    def times(self):
        """Time instances the signal is sampled at."""
        return np.atleast_1d(np.arange(0, self.n_samples) / self.sampling_rate)

    @property
    def time(self):
        """The signal data in the time domain."""
        self.domain = 'time'
        return self._data

    @time.setter
    def time(self, value):
        data = np.atleast_2d(value)
        self._domain = 'time'
        self._data = data
        self._n_samples = data.shape[-1]

    @property
    def freq(self):
        """The signal data in the frequency domain."""
        self.domain = 'freq'
        return self._data

    @freq.setter
    def freq(self, value):
        spec = np.atleast_2d(value)
        new_num_bins = spec.shape[-1]
        if new_num_bins == self.n_bins:
            n_samples = self.n_samples
        else:
            warnings.warn("Number of frequency bins different will change, "
                          "assuming an even number of samples from the number "
                          "of frequency bins.")
            n_samples = (new_num_bins - 1)*2

        self._data = spec
        self._n_samples = n_samples
        self._domain = 'freq'

    @property
    def sampling_rate(self):
        """The sampling rate of the signal."""
        return self._sampling_rate

    @sampling_rate.setter
    def sampling_rate(self, value):
        self._sampling_rate = value

    @property
    def signal_type(self):
        """The signal type."""
        return self._signal_type

    @signal_type.setter
    def signal_type(self, value):
        # check if we do anything
        if value == self._signal_type:
            return

        # check input
        if value not in self._VALID_SIGNAL_TYPE:
            raise ValueError("Not a valid signal type ('power'/'energy')")
        if value == 'energy' and self._fft_norm != 'unitary':
            raise ValueError(("Signal type can only be set to 'energy' if "
                              "fft_norm is 'unitary'"))

        # normalize or de-normalize spectrum
        if self._domain == 'freq' and value == 'energy':
            inverse = True
        if self._domain == 'freq' and value == 'power':
            inverse = False

        self._data = fft.normalization(
            self._data, self._n_samples, self._sampling_rate,
            'power', self._fft_norm, inverse)

        # set new signal type
        self._signal_type = value

    @property
    def fft_norm(self):
        """
        The normalization for the Fourier Transform.

        See pyfar.fft.normalization for more information.
        """
        return self._fft_norm

    @fft_norm.setter
    def fft_norm(self, value):
        """
        The normalization for the Fourier Transform.

        See pyfar.fft.normalization for more information.
        """
        # check input
        if value not in self._VALID_FFT_NORMS:
            raise ValueError(("Invalid FFT normalization. Has to be "
                              f"{', '.join(self._VALID_FFT_NORMS)}, but found "
                              f"'{value}'"))
        if self._signal_type == 'energy' and value != 'unitary':
            raise ValueError(
                "If signal_type is 'energy', fft_norm must be 'unitary'.")

        # apply new normalization if Signal is in frequency domain
        if self._fft_norm != value and self._domain == 'freq':
            # de-normalize
            self._data = fft.normalization(
                self._data, self._n_samples, self._sampling_rate,
                self._signal_type, self._fft_norm, inverse=True)
            # normalize
            self._data = fft.normalization(
                self._data, self._n_samples, self._sampling_rate,
                self._signal_type, value, inverse=False)

        self._fft_norm = value

    @property
    def dtype(self):
        """The data type of the signal. This can be any data type and precision
        supported by numpy."""
        return self._dtype

    @property
    def signal_length(self):
        """The length of the signal in seconds."""
        return (self.n_samples - 1) / self.sampling_rate

    @property
    def cshape(self):
        """
        Return channel shape.

        The channel shape gives the shape of the signal data excluding the last
        dimension, which is `self.n_samples` for time domain signals and
        `self.n_bins` for frequency domain signals.
        """
        return self._data.shape[:-1]

    @property
    def comment(self):
        """Get comment."""
        return self._comment

    @comment.setter
    def comment(self, value):
        """Set comment."""
        self._comment = str(value)

    def __add__(self, data):
        return add((self, data), 'freq')

    def __sub__(self, data):
        return subtract((self, data), 'freq')

    def __mul__(self, data):
        return multiply((self, data), 'freq')

    def __truediv__(self, data):
        return divide((self, data), 'freq')

    def __pow__(self, data):
        return power((self, data), 'freq')

    def __repr__(self):
        """String representation of signal class.
        """
        repr_string = (
            f"{self.domain} domain {self.signal_type} Signal:\n"
            f"{self.cshape} channels with {self.n_samples} samples @ "
            f"{self._sampling_rate} Hz sampling rate and {self.fft_norm} "
            "FFT normalization\n")

        return repr_string

    def __getitem__(self, key):
        """Get signal channels at key.
        """
        if isinstance(key, (int, slice, tuple)):
            try:
                data = self._data[key]
            except KeyError:
                raise KeyError("Index is out of bounds")
        else:
            raise TypeError(
                    "Index must be int, not {}".format(type(key).__name__))
        items = Signal(
            data,
            sampling_rate=self.sampling_rate,
            domain=self.domain,
            signal_type=self.signal_type,
            dtype=self.dtype)

        return items

    def __setitem__(self, key, value):
        """Set signal channels at key.
        """
        self._assert_matching_meta_data(value)
        if isinstance(key, (int, slice)):
            try:
                self._data[key] = value._data
            except KeyError:
                raise KeyError("Index is out of bound")
        else:
            raise TypeError(
                    "Index must be int, not {}".format(type(key).__name__))

    def __len__(self):
        """Length of the object which is the number of samples stored.
        """
        return self.n_samples

    def _assert_matching_meta_data(self, other):
        """Check if the sampling rate, the number of samples, and the signal
        type of two Signal objects match.
        """
        if not isinstance(other, Signal):
            raise ValueError("Comparison only valid against Signal objects.")
        if self.sampling_rate != other.sampling_rate:
            raise ValueError("The sampling rates do not match.")
        if self.n_samples != other.n_samples:
            raise ValueError("The number of samples does not match.")
        if self.signal_type != other.signal_type:
            raise ValueError("The signal types do not match.")

    def __iter__(self):
        """Iterator for signals. The actual iteration is handled through
        numpy's array iteration.
        """
        return SignalIterator(self._data.__iter__(), self)


class SignalIterator(object):
    """Iterator for signals
    """
    def __init__(self, array_iterator, signal):
        self._array_iterator = array_iterator
        self._signal = signal
        self._iterated_sig = Signal(
            signal._data[..., 0, :],
            sampling_rate=signal.sampling_rate,
            n_samples=signal.n_samples,
            domain=signal.domain,
            signal_type=signal.signal_type,
            dtype=signal.dtype)

    def __next__(self):
        if self._signal.domain == self._iterated_sig.domain:
            data = self._array_iterator.__next__()
            self._iterated_sig._data = np.atleast_2d(data)
        else:
            raise RuntimeError("domain changes during iterations break stuff!")

        return self._iterated_sig


def add(data: tuple, domain='freq'):
    """Add signals and/or array likes.

    Parameters
    ----------
    data : tuple of the form (data_1, data_2, ..., data_N)
        Data to be added. Can contain Signal objects, numbers, and, array
        likes.
    domain : 'time', 'freq'
        Flag to indicate if the operation should be performed in the time or
        frequency domain. If working in the frequency domain, the FFT
        normalization is removed before the operation (See
        pyfar.fft.normalization).

    Returns
    -------
    results : Signal, numpy array
        Result of the operation as numpy array, if `data` contains only array
        likes and numbers. Result as Signal object if `data`contains a Signal.
        The `Signal.domain` is set by the input parameter `domain`. The
        `Signal.signal_type` is 'energy' if `data` contains only energy
        Signals and 'power' otherwise. The `Signal.fft_norm` is taken from the
        first signal in `data`.

    """
    return _arithmetic(data, domain, _add)


def subtract(data: tuple, domain='freq'):
    """Subtract signals and/or array likes.

    Parameters
    ----------
    data : tuple of the form (data_1, data_2, ..., data_N)
        Data to be subtracted. Can contain Signal objects, numbers, and, array
        likes.
    domain : 'time', 'freq'
        Flag to indicate if the operation should be performed in the time or
        frequency domain. If working in the frequency domain, the FFT
        normalization is removed before the operation (See
        pyfar.fft.normalization).

    Returns
    -------
    results : Signal, numpy array
        Result of the operation as numpy array, if `data` contains only array
        likes and numbers. Result as Signal object if `data`contains a Signal.
        The `Signal.domain` is set by the input parameter `domain`. The
        `Signal.signal_type` is 'energy' if `data` contains only energy
        Signals and 'power' otherwise. The `Signal.fft_norm` is taken from the
        first signal in `data`.

    """
    return _arithmetic(data, domain, _subtract)


def multiply(data: tuple, domain='freq'):
    """Multiply signals and/or array likes.

    Parameters
    ----------
    data : tuple of the form (data_1, data_2, ..., data_N)
        Data to be multiplied. Can contain Signal objects, numbers, and, array
        likes.
    domain : 'time', 'freq'
        Flag to indicate if the operation should be performed in the time or
        frequency domain. If working in the frequency domain, the FFT
        normalization is removed before the operation (See
        pyfar.fft.normalization).

    Returns
    -------
    results : Signal, numpy array
        Result of the operation as numpy array, if `data` contains only array
        likes and numbers. Result as Signal object if `data`contains a Signal.
        The `Signal.domain` is set by the input parameter `domain`. The
        `Signal.signal_type` is 'energy' if `data` contains only energy
        Signals and 'power' otherwise. The `Signal.fft_norm` is taken from the
        first signal in `data`.

    """
    return _arithmetic(data, domain, _multiply)


def divide(data: tuple, domain='freq'):
    """Divide signals and/or array likes.

    Parameters
    ----------
    data : tuple of the form (data_1, data_2, ..., data_N)
        Data to be divided. Can contain Signal objects, numbers, and, array
        likes.
    domain : 'time', 'freq'
        Flag to indicate if the operation should be performed in the time or
        frequency domain. If working in the frequency domain, the FFT
        normalization is removed before the operation (See
        pyfar.fft.normalization).

    Returns
    -------
    results : Signal, numpy array
        Result of the operation as numpy array, if `data` contains only array
        likes and numbers. Result as Signal object if `data`contains a Signal.
        The `Signal.domain` is set by the input parameter `domain`. The
        `Signal.signal_type` is 'energy' if `data` contains only energy
        Signals and 'power' otherwise. The `Signal.fft_norm` is taken from the
        first signal in `data`.

    """
    return _arithmetic(data, domain, _divide)


def power(data: tuple, domain='freq'):
    """Power of signals and/or array likes.

    Parameters
    ----------
    data : tuple of the form (data_1, data_2, ..., data_N)
        Data to be powerd. Can contain Signal objects, numbers, and, array
        likes.
    domain : 'time', 'freq'
        Flag to indicate if the operation should be performed in the time or
        frequency domain. If working in the frequency domain, the FFT
        normalization is removed before the operation (See
        pyfar.fft.normalization).

    Returns
    -------
    results : Signal, numpy array
        Result of the operation as numpy array, if `data` contains only array
        likes and numbers. Result as Signal object if `data`contains a Signal.
        The `Signal.domain` is set by the input parameter `domain`. The
        `Signal.signal_type` is 'energy' if `data` contains only energy
        Signals and 'power' otherwise. The `Signal.fft_norm` is taken from the
        first signal in `data`.

    """
    return _arithmetic(data, domain, _power)


def _arithmetic(data: tuple, domain: str, operation: Callable):
    """Apply arithmetic operations."""

    # check input and obtain meta data of new signal
    sampling_rate, n_samples, signal_type, fft_norm = \
        _assert_match_for_arithmetic(data, domain)

    # apply arithmetic operation
    result = _get_arithmetic_data(data[0], n_samples, domain)

    for d in range(1, len(data)):
        result = operation(
            result, _get_arithmetic_data(data[d], n_samples, domain))

    # check if to retun as Signal
    if sampling_rate is not None:
        # apply desried fft normalization
        if domain == 'freq':
            result = fft.normalization(result, n_samples, sampling_rate,
                                       signal_type, fft_norm)

        result = Signal(
            result, sampling_rate, n_samples, domain, signal_type, fft_norm)

    return result


def _assert_match_for_arithmetic(data: tuple, domain: str):
    """Check if type and meta data of input is fine for arithmetic operations.

    Check if sampling rate and number of samples agree if multiple signals are
    provided. Check if arrays are numeric. Check if a power signal is contained
    in the input.

    Input:
    data : tuple
        Can contain signal and array like data
    domain : str
        Domain in which the arithmetic operation should be performed. 'time' or
        'freq'.

    Returns
    -------
    sampling_rate : number, None
        Sampling rate of the signals. None, if no signal is contained in `data`
    n_samples : number, None
        Number of samples of the signals. None, if no signal is contained in
        `data`
    signal_type : str, None
        'energy' if all signaly are of type energy. 'power' if any power signal
        is contained in `data`. None if no signal is contained in `data`
    fft_norm : str, None
        FFT norm of the first signal in `data`. None if no signal is contained
        in `data`.

    """

    # we need at least two signals
    if not isinstance(data, tuple):
        raise ValueError("Input argument 'data' must be a tuple.")

    # check validity of domain
    if domain not in ['time', 'freq']:
        raise ValueError(f"domain must be time or freq but is {domain}.")

    # check input types and meta data
    sampling_rate = None
    n_samples = None
    signal_type = None
    fft_norm = None
    for d in data:
        # check or store meta data of signals
        if isinstance(d, Signal):
            if sampling_rate is None:
                sampling_rate = d.sampling_rate
                n_samples = d.n_samples
                signal_type = d.signal_type
                fft_norm = d.fft_norm
            else:
                if sampling_rate != d.sampling_rate:
                    raise ValueError("The sampling rates do not match.")
                if n_samples != d.n_samples:
                    raise ValueError("The number of samples does not match.")
            # if there is a power signal, the returned signal will be a power
            # signal
            if d.signal_type == "power":
                signal_type = "power"
        # check type of non signal input
        else:
            dtypes = ['int8', 'int16', 'int32', 'int64',
                      'float32', 'float64',
                      'complex64', 'complex128']
            if np.asarray(d).dtype not in dtypes:
                raise ValueError(
                    f"Input must be of type Signal, {', '.join(dtypes)}")
            if np.asarray(d).dtype in ['complex64', 'complex128'] \
                    and domain == 'time':
                raise ValueError(
                    "Complex input can not be applied in the time domain.")

    return sampling_rate, n_samples, signal_type, fft_norm


def _get_arithmetic_data(data, n_samples, domain):
    """
    Return data in desired domain without any fft normalization.

    Parameters
    ----------
    data : Signal, array like, number
        Input data
    n_samples :
        Number of samples of data if data is a Signal (required for fft
        normalization).
    domain : 'time', 'freq'
        Domain in which the data is returned

    Returns
    -------
    data_out : numpy array
        Data in desired domain without any fft normlaization if data is a
        Signal. `np.asarray(data)` otherwise.
    """
    if isinstance(data, Signal):

        # get signal in correct domain
        if domain == "time":
            data_out = data.time.copy()
        elif domain == "freq":
            data_out = data.freq.copy()

            if data.signal_type == 'power':
                # remove current fft normalization
                data_out = fft.normalization(
                    data_out, n_samples, data.sampling_rate,
                    'power', data.fft_norm, inverse=True)

        else:
            raise ValueError(
                f"domain must be 'time' or 'freq' but found {domain}")

    else:
        data_out = np.asarray(data)

    return data_out


def _add(a, b):
    return a + b


def _subtract(a, b):
    return a - b


def _multiply(a, b):
    return a * b


def _divide(a, b):
    return a / b


def _power(a, b):
    return a**b
