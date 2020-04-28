import os
from tkinter import messagebox
import numpy as np
from scipy import signal
import struct

def generate_result_filename(dut, name, ):
    idn = dut.idn().split(',')
    module = idn[1]
    sn = idn[2].replace('/', '-')

    full_name = os.path.abspath('./result/%s(%s)/%s(%s)_%s.csv' % (module, sn, module, sn, name))

    if not os.path.exists(os.path.dirname(full_name)):
        os.makedirs(os.path.dirname(full_name))

    return full_name


class MessageBox:
    @staticmethod
    def info(message='', title='Info'):
        messagebox.showinfo(title, message)

    @staticmethod
    def yes_or_no(message='', title='Ask'):
        return messagebox.askyesno(title, message)


class csv:
    def __init__(self):
        pass

    @staticmethod
    def get_csv_data(name, stype='str'):
        data = list()
        with open(name, 'r') as fp:
            for line in fp.readlines():
                line = line.strip()
                line = line.strip(',')
                if len(line) < 1:
                    continue

                if stype == 'float':
                    data.append([float(v) for v in line.split(',')])
                elif stype == 'hex':
                    data.append([int(v, 16) for v in line.split(',')])
                elif stype == 'int':
                    data.append([int(v) for v in line.split(',')])
                elif stype == 'str':
                    data.append([str(v) for v in line.split(',')])
                else:
                    raise Exception('unknown data type')

        return data

    @staticmethod
    def save_csv_data(name, data, mode='w', stype=None):
        real_path = os.path.dirname(name)
        if os.path.exists(real_path) is False:
            os.makedirs(real_path)

        with open(name, mode) as fp:
            csv.save_list(fp, data, stype)
        return

    @staticmethod
    def save_list(fp, data, stype=None):
        if isinstance(data, list):
            item = None
            for item in data:
                csv.save_list(fp, item, stype)
            if isinstance(item, list) is False:
                fp.write('\n')
        elif isinstance(data, dict):
            for key in data:
                fp.write('%s,' % key)
                csv.save_list(fp, data[key], stype)
        elif isinstance(data, np.ndarray):
            csv.save_list(fp, data.tolist(), stype)
        else:
            if isinstance(data, str):
                fp.write('%s,' % data)
            elif isinstance(data, int):
                if stype == 'hex':
                    fp.write('%x,' % data)
                else:
                    fp.write('%d,' % data)
            elif isinstance(data, float):
                fp.write('%f,' % data)
            else:
                fp.write('%s,' % str(data))

    @staticmethod
    def to_one_list(data, result):
        if isinstance(data, list):
            for item in data:
                csv.to_one_list(item, result)
        else:
            result.append(data)

    @staticmethod
    def number_of_columns(name):
        with open(name, 'r') as f:
            ncols = len(f.readline().split(','))
            return ncols


class IQHelper:
    @staticmethod
    def fetched_iq_to_complex(data):
        data = np.array(data)
        data = np.reshape(data, (-1, 2))
        line, col = data.shape
        c = np.empty(line, dtype=np.complex64)
        for i in range(line):
            '''
            if data[i][0] == 0 and data[i][1] == 0:
                # add random noise?
                if i % 2 == 0:
                    c[i] = complex(1, 0)
                else:
                    c[i] = complex(-1, 0)
            else:
                c[i] = complex(data[i][0], data[i][1])
            '''
            c[i] = complex(data[i][0], data[i][1])
        return c

    @staticmethod
    def fetched_iq_to_complex_voltage(data, ref_level):
        data = IQHelper.fetched_iq_to_complex(data)

        backoff = 6
        coefficients = (2 / 2 ** 16) * np.power(10, (ref_level - backoff) / 20)
        a = 0xff
        b = a & 0x0f

        return data * coefficients

    @staticmethod
    def spectrum_without_window(data_in_voltage):
        spec = np.fft.fftshift(np.abs(np.fft.fft(data_in_voltage)))
        power = ((spec/len(spec)) ** 2) / (2*50)
        return 10*np.log10(power*1000)

    @staticmethod
    def spectrum_with_window(data_in_voltage, window='flattop'):
        # reference
        # http://download.ni.com/evaluation/pxi/Understanding%20FFTs%20and%20Windowing.pdf
        # https://kluedo.ub.uni-kl.de/frontdoor/deliver/index/docId/4293/file/exact_fft_measurements.pdf
        if window == 'flattop':  # ampl acc
            w = signal.windows.flattop(len(data_in_voltage))
        elif window == 'hanning':
            w = signal.windows.hann(len(data_in_voltage))
        else:
            raise Exception('not supported window function: %s' % window)

        # https://www.mathworks.com/matlabcentral/answers/372516-calculate-windowing-correction-factor
        Aw = len(w) / sum(w)
        spec = np.fft.fftshift(np.abs(np.fft.fft(data_in_voltage * w * Aw)))
        power = ((spec/len(spec)) ** 2) / (2*50)
        return 10*np.log10(power*1000)

    @staticmethod
    def iqpower(data_in_voltage):
        peak_voltage = np.abs(data_in_voltage)
        rms_voltage = peak_voltage / np.sqrt(2)
        rms_p = (rms_voltage ** 2) / 50
        return 10 * np.log10(1000*rms_p)

    @staticmethod
    def spectrum_peak_power(iq_raw, reference_level, path_loss=0):
        iq_voltage = IQHelper.fetched_iq_to_complex_voltage(iq_raw, reference_level)
        spec = IQHelper.spectrum_with_window(iq_voltage)
        peaks, _ = signal.find_peaks(spec, height=reference_level-100, distance=100)
        if len(peaks) > 0:
            return max(spec[peaks]) + path_loss
        else:
            raise Exception('can not found the peak of the spectrum')

    @staticmethod
    def spectrum_peak_power_from_iq_voltage(iq_voltage, path_loss=0):
        spec = IQHelper.spectrum_with_window(iq_voltage)
        peaks, _ = signal.find_peaks(spec, distance=100)
        if len(peaks) > 0:
            return max(spec[peaks]) + path_loss
        else:
            raise Exception('can not found the peak of the spectrum')

    @staticmethod
    def save_to_vw(data, filename, sample_rate):
        data = np.array(data)
        data = data / np.max(np.abs(data))
        rms = np.sqrt(np.mean(np.abs(data))) / np.max(np.abs(data))
        with open(filename, 'wb') as fp:
            fp.write(bytes('{TYPE: SMU-WV, 0}', encoding='ansi'))
            s = '{LEVEL OFFS: %f,0}' % (20*np.log10(1.0/rms))
            fp.write(bytes(s, encoding='ansi'))
            fp.write(bytes('{CLOCK: %f}' % sample_rate, encoding='ansi'))
            fp.write(bytes('{SAMPLES: %d}' % len(data), encoding='ansi'))
            fp.write(bytes('{WAVEFORM-%d: #' % (len(data) * 4 + 3), encoding='ansi'))
            for d in data:
                fp.write(struct.pack('hh', int(d.real*32767), int(d.imag*32767)))
            fp.write(bytes('}', encoding='ansi'))

    @staticmethod
    def save_to_89600_csv(data_in_voltage, filename, sample_rate):
        fp = open(filename, 'w')
        half_span = sample_rate/1.28/2
        fp.write('FreqValidMax, %e\n' % half_span)
        fp.write('FreqValidMin, %e\n' % -half_span)
        fp.write('InputCenter, 0\n')
        fp.write('InputRange, 1\n')
        fp.write('InputRefImped, 50\n')
        fp.write('InputZoom, 1\n')
        fp.write('XDelta, %e\n' % (1/sample_rate))
        fp.write('XDomain, 2\n')
        fp.write('XStart, 2\n')
        fp.write('XUnit, "Sec"\n')
        fp.write('YUnit, "V"\n')

        for s in data_in_voltage:
            fp.write('%e,%e\n' % (np.real(s), np.imag(s)))
        fp.close()

    @staticmethod
    def angle(data, deg=True):
        return np.angle(data, deg=deg)

    @staticmethod
    def detector(data, target=1001, method='Positive Peak'):
        if method == 'All Points':
            return data

        data = np.array(data)

        n = int(data.size / target)
        if data.size % target != 0:
            data = data[0:n * target]

        data2 = np.reshape(data, (target, n))
        if method == 'Positive Peak':
            data2 = np.max(data2, axis=1)
        elif method == 'Average':
            data2 = np.average(data2, axis=1)
        elif method == 'Negative Peak':
            data2 = np.min(data2, axis=1)

        return data2
