import numpy as np
import cmath as cm
from pyfar import Signal


class FractionalSmoothing:
    """ Class of fractional smoothing object.
        Object contains data of a signal and a given smoothing width.
    """
    def __init__(
            self,
            data,
            smoothing_width):
        """__init
        Initiate FractionalSmoothing object.

        :param  data:               Raw data of the signal in the
                                    frequency domain
        :type   data:               ndarray, double
        :param  smoothing_width:    Width of smoothing window relative
                                    to an octave
        :type   smoothing_width:    float, int
        :raises TypeError:         Invalid data type of sampling_rate.
        :raises TypeError:         Invalid data type of smoothing_width.
        """
        if isinstance(data, np.ndarray) is True:
            if data.dtype == np.complex128:
                # Get number of freq bins from signal data
                self._n_bins = data.shape[-1]
                # Get number of channels
                self._n_channels = data.shape[0]
                # Copy signal data
                self._data = np.atleast_2d(
                    np.asarray(data.copy(), dtype=np.complex))
            else:
                raise TypeError(
                    "ndarry must by of type: numpy.complex182.")
        else:
            raise TypeError(
                    "Invalid data type of input data (numpy.ndarray).")

        if isinstance(smoothing_width, (float, int)) is True:
            self._smoothing_width = smoothing_width
        else:
            raise TypeError("Invalid data type of window width (int/float).")

    def calc_integration_limits(self):
        """integration_limits
        Computes integration limits for each frequency bin
        k. For each k two arrays are computed, one containing the upper, one
        containing the lower integration limits.
        The k arrays of upper and lower limits are stored in two arrays for
        upper and lower limits. Finally, the log2 on all elements is computed
        and the two arrays are combined to one. The array 'Phi' contains all
        integration limits and is stored in the FractionalSmoothing object.
        """
        # Freq bin iterator:
        k_i = np.arange(self._n_bins)
        # Lower and upper cutoff frequencies bin for each bin k:
        k_cutoff_low = k_i*2**(-self._smoothing_width/2)
        k_cutoff_up = k_i*2**(self._smoothing_width/2)

        # Matrix with shape: 'number of freq bins' x 'max. cutoff bin' x 2:
        # Each row stores upper and lower limits for k. freq bin from 0 to
        # max. cutoff freq:
        # k_cutoff_max = k_max*2**(self._smoothing_width/2) = k_cutoff_up[-1]
        size = int(np.ceil(k_cutoff_up[-1]) + 1)
        k_mat = np.array([
            lim_padder(low, up, size) for low, up in
            zip(k_cutoff_low, k_cutoff_up)])

        # Divide by k:
        k_divider = np.array([k_i]*(k_mat.shape[2]*2)).T.reshape(k_mat.shape)
        k_mat /= k_divider

        # Apply log:
        self._limits = np.log2(k_mat)

        # Replace all -inf and nan by zero:
        self._limits = np.nan_to_num(self._limits, posinf=.0, neginf=.0)

    def calc_weights(self):
        """calc_weights
        Computes integration from lower to upper limits for a
        triangular window.
        """
        # Computation: Upper - Lower / Smoothing_Width
        self._weights = (self._limits[:, 0] - self._limits[:, 1])
        self._weights /= self._smoothing_width
        # Set Weight for freq bin = 0 to 1 (no smoothing at 0 Hz)
        self._weights[0, 0] = 1

    def apply(self):
        """apply
        Apply weights to magnitude spectrum of signal and return new
        complex spectrum.
        The weights matrix is repeated according to the number of channels.
        Further, the data array is padded to fit the size of the weights
        matrix. This is done by padding the data array for each frequency bin
        by the mean value of the part of the data array that is overlapped by
        the window. This is done to avoid boundary effects at the end of the
        spectrum.

        :return: Complex spectrum
        :rtype: ndarray
        """
        # Pad_width from difference of weights length and data length
        pad_width = self._weights.shape[1] - self._n_bins
        # Get size of signal that is used to calc mean value to pad:
        # Difference between data length and start of weighting window
        mean_size = self._n_bins - (self._weights != 0).argmax(axis=1)
        # Add new dimension for channels
        self._weights = np.expand_dims(self._weights, axis=0)
        # Expand weights matrix for channels
        self._weights = np.repeat(self._weights, self._n_channels, axis=0)

        # Pad data into array of weighting matrix shape
        # For each frequency bin k, data is padded according with
        # specified mean. The mean is computed from all values within
        # the range of the smoothing window of the particular frequency bin k
        padded_data = data_padder(self._data, pad_width, mean_size)

        # Multiplication of weighting and data matrix along axis 2
        magnitude = np.sum(self._weights*padded_data, axis=2)
        # Remove padded samples:
        magnitude = magnitude[:, :self._n_bins]
        # Copy phase from original data
        phase = np.angle(self._data)

        # Return array in cartesian form:
        return polar2cartesian(magnitude, phase)


def lim_padder(low, up, size):
    """lim_padder Returns a 2D array of shape (2, 'size') containing a range of
    k+.5 and k-.5 values with k increasing from 'low' to 'up' values.
    Arrays are padded by k-1 zeros befor and size - (K+1) after.
    First array: [0, ..., 0, k+.5, ..., K+.5, up, 0, ... ,0 ]
    Second array: [0, ..., 0, low, k-.5, ..., K-.5, 0, ..., 0]

    :param low: Lower value to start array
    :type low: float
    :param up: Upper value to end array
    :type up: float
    :param size: Total length of arrays
    :type size: int
    :return: Double padded array. 
    :rtype: ndarray
    """
    # Get rounded limits:
    # Round up for lower limit, round down for upper limits
    low_ceil = np.ceil(low)
    up_floor = np.floor(up)
    # Set base array beginning to lowest k'-.5 that is above limit "low"
    begin = low_ceil - 0.5 if (low_ceil - low) > .5 else low_ceil + 0.5
    # Set base array end to highest k'+5 that is below limit "up"
    end = up_floor + 1 if (up - up_floor) > .5 else up_floor
    # Create base array
    base = np.arange(begin, end)
    # Append actuall limits to base:
    # Push back for upper limit
    upper_limit = np.append(base, up)
    # Push front for lower limit
    lower_limit = np.append(low, base)
    # Pad arrays front:
    pad_front = int(upper_limit[0])
    upper_limit = np.pad(upper_limit, (pad_front, 0))
    lower_limit = np.pad(lower_limit, (pad_front, 0))
    # Pad array back to 'size' (length of largest smoothing window at highest
    # frequency bin k)
    upper_limit = np.pad(upper_limit, (0, size-len(upper_limit)))
    lower_limit = np.pad(lower_limit, (0, size-len(lower_limit)))
    # Return upper and lower limits of k-th freq bin in one array:
    return np.concatenate((
        upper_limit.reshape(1, -1),
        lower_limit.reshape(1, -1)))


def data_padder(data, pad_width, mean_size):
    """data_padder Pads data array of shape (N, M) to data matrix of shape
    (N, M, M+pad_width). The output data contains M copies of the input data
    rows padded by 'pad_width' with the mean value of the last data samples.
    The number of samples used to compute the mean for each row is specified in
    the array 'mean_size'.

    :param data: Array of shape (N, M) of the data.
                 (N= Number of channels, M=Length of Signal)
    :type data: ndarray
    :param pad_wdith: Padding length
    :type pad_wdith: int
    :param mean_size: Array with numbers of samples used to compute the mean.
    :type mean_size: ndarray
    :raises ValueError: Data array must be 2D.
    :return: Padded data matrix containing the data values and specified
             padding value for each frequency bin.
    :rtype: ndarray
    """
    if data.ndim == 2:
        padded = np.array([np.pad(
            data, ((0, 0), (0, pad_width)), 'mean', stat_length=(m))
            for m in mean_size])
        # move channel axis to front and return
        return np.moveaxis(padded, 1, 0)
    else:
        raise ValueError('Data array must be 2D.')


def polar2cartesian(amplitude, phase):
    """polar2cartesian Converts two arrays of amplitude and phase into one array
    of complex numbers in cartesian form.

    :param amplitude: Array of amplitude values.
    :type amplitude: ndarray
    :param phase: Array of phase values.
    :type phase: ndarray
    :raises ValueError: Arrays must have same shape
    :return: Array of same shape as input arrays with complex numbers.
    :rtype: ndarray
    """
    if(amplitude.shape == phase.shape):
        input_shape = amplitude.shape
        reshaped_amplitude = amplitude.reshape(1, -1)[0]
        reshaped_phase = phase.reshape(1, -1)[0]
        cartesian = np.array([
                              cm.rect(a, p) for a, p in
                              zip(reshaped_amplitude, reshaped_phase)])
        return cartesian.reshape(input_shape)
    else:
        raise ValueError("Arrays must have same shapes.")


def frac_smooth_signal(signal, smoothing_width):
    """fractional_smooth Method to smooth a given signal.
    Takes the data of a given signal of shape (n, m), where n is number of
    channels and m length of the signal.
    Creates an object of class FractionalSmoothing to compute integration
    limits and smoothing weights. Finally applies the weights on the input data
    and returns smoothed signal.

    :param signal:  Input signal to be smoothed
    :type signal:   Signal
    :param          smoothing_width:    Width of smoothing window relative
                                        to an octave
    :type           smoothing_width:    float, int
    :raises         TypeError:          Input data must be of type Signal.
    :return:        Smoothed Signal
    :rtype:         Signal
    """
    if isinstance(signal, Signal) is True:
        # Create smoothing bject
        obj = FractionalSmoothing(
            data=signal.freq,
            smoothing_width=smoothing_width)
        # Compute limits:
        obj.calc_integration_limits()
        # Compute weights:
        obj.calc_weights()
        # Compute smoothed magnitude spectrum
        data = obj.apply()

        # Return smoothed signal
        return Signal(
            data,
            signal.sampling_rate,
            signal.n_samples,
            domain='freq')
    else:
        raise TypeError("Input data must be of type Signal.")


def frac_smooth_hrtf(hrtf, smoothing_width):
    """fractional_smooth_hrtf Methode to smooth a given head related transfer
    function (HRTF). Takes the hrtf as an numpy array of shape (n, m) or m,
    where n is the number of channels and m is the lenght of the spectrum.
    Creates an object of class FractionalSmoothing to compute integration
    limits and smoothing weights. Finally applies the weights on the input data
    and returns smoothed HRTF.

    :param hrtf: Array of HRTF data in frequency domain.
    :type hrtf: numpy.ndarray with np.complex128
    :param          smoothing_width:    Width of smoothing window relative
                                        to an octave
    :type           smoothing_width:    float, int
    :raises TypeError: Input data must be of type ndarray.
    :return: Smoothed HRTF
    :rtype: ndarray
    """
    if isinstance(hrtf, np.ndarray) is True:
        # Check shape of hrtf:
        if hrtf.ndim == 1:
            # Add channel dimension if 1D:
            hrtf.reshape(1, -1)
        # Create smoothing object:
        obj = FractionalSmoothing(hrtf, smoothing_width=smoothing_width)
        # Compute limits:
        obj.calc_integration_limits()
        # Compute weights:
        obj.calc_weights()
        # Compute smoothed hrtf
        data = obj.apply()
        return data
    else:
        raise TypeError("Input data must be of type ndarray.")
