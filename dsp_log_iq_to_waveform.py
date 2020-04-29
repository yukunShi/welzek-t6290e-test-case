from library.utility import *
import sys
import os.path
import tkinter as tk


class Inputbox():
    def __init__(self, text=""):
        self.root = tk.Tk()
        self.get = ""
        self.root.geometry("300x100")
        self.root.title("Inputbox")
        self.label_file_name = tk.Label(self.root, text=text)
        self.label_file_name.pack()
        self.entry = tk.Entry(self.root)
        self.entry.pack()
        self.entry.focus()
        self.entry.bind("<Return>", lambda x: self.getinput(self.entry.get()))
        self.root.mainloop()

    def getinput(self, value):
        self.get = value
        self.root.destroy()


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
    filename = './NR_FDD_UL_mtk_PLCid_1_S30K_B100_DFT_OFF_PCOMp_OFF_2592993e+3_Q64_B_OFF_273rb_0_14_0_T1_SING_1_0_.txt'
    if len(sys.argv) > 1:
        filename = sys.argv[1]

    full_data = list()
    with open(filename, 'r') as fp:

        while True:
            line = fp.readline()
            if len(line) <= 0:
                break

            line = line.strip()
            line = line.strip(',')
            line = line.strip().split(',')
            data = list(map(lambda x: int(x), line))
            full_data.extend(data)
            pass

    full_data = np.array(full_data)
    full_data = IQHelper.fetched_iq_to_complex(full_data)

    inp = Inputbox(text="Input sample rate, unit MHz")

    sample_rate = float(inp.get) * 1e6
    IQHelper.save_to_89600_csv(full_data, '%s/%s-for89600.csv' % (os.path.dirname(filename), os.path.basename(filename)), sample_rate)
    IQHelper.save_to_vw(full_data, '%s/%s-for-rs.wv' % (os.path.dirname(filename), os.path.basename(filename),),sample_rate)

