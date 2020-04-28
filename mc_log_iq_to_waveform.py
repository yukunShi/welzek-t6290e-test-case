from library.utility import *
import sys
import os.path


def is_seg_start(l):
    r = l.split('):')
    if len(r) == 2:
        if r[1].find('sampleRate ') != -1:
            r = r[1].strip().split(' ')
            return None, int(r[1]) * 1000

        if r[1].find(', IQ from No') != -1:
            "Seg 0, IQ from No.0 ms, len 1 ms:"
            r = r[1].split(',')
            return r[0], None

    return None, None


def get_one_line_iq_data(l):
    r = l.split('):')
    iq = list()
    if len(r) == 2:
        d = r[1].split(':')
        if len(d) == 2:
            num = int(d[0])
            s = d[1].strip().split(' ')
            for v in s:
                n = int(v, 16)
                i1, q1, i2, q2, = struct.unpack('hhhh', n.to_bytes(8, byteorder='big', signed=False))
                iq.append(complex(i2, q2))
                iq.append(complex(i1, q1))
            return num, iq

    return -1, list()


if __name__ == '__main__':
    filename = './PPC_10.3.19.200_20200428_192442_out.txt'
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    with open(filename, 'r') as fp:
        found_start = False
        full_iq = list()
        sample_rate = 1e6
        count = 1
        while True:
            line = fp.readline()
            if len(line) <= 0:
                break

            if found_start is True:
                seq, iq = get_one_line_iq_data(line)
                if seq == -1:
                    IQHelper.save_to_89600_csv(full_iq, '%s/%s-%s-%d.csv' % (os.path.dirname(filename), os.path.basename(filename), segName, count), sample_rate)
                    IQHelper.save_to_vw(full_iq, '%s/%s-%s-%d.wv' % (os.path.dirname(filename), os.path.basename(filename), segName, count), sample_rate)
                    found_start = False
                    count += 1
                    full_iq = list()
                else:
                    full_iq.extend(iq)

            else:
                segName, sr = is_seg_start(line)
                if sr is not None:
                    sample_rate = sr

                if segName is not None:
                    print(segName)
                    found_start = True
            pass
