from includes.MemMap import MemMap
import numpy as np
import tensorflow as tf
import configparser


class ImageBuffer():
    def __init__(self,mmap_xml):
        self.mmap = MemMap(mmap_xml)
        self.counter_last = -1
        self.counter_second = -1

        self.last_image = None
        self.focus_frame_position = [0.4, 0.4, 0.6, 0.6]

        # percentil calc paramter
        self.pct_counter = 0
        self.pct_min = None
        self.pct_max = None
    def getNOldestImags(self, N):
        counters = np.array([slot.counter for slot in self.mmap.rbf])
        countersArgSort = np.argsort(counters)
        indices, = np.where(
            (countersArgSort<(N+1))&(countersArgSort>0)
        )
        imList = []
        metaList = []
        for idx in indices:
            imList.append(
                # tf.convert_to_tensor(self.mmap.rbf[idx].image.astype(np.uint8)[None,:])
                self.mmap.rbf[idx].image.astype(np.float32)[None, :]
            )
            metaList.append({
                'timestamp_us': int(
                    str(self.mmap.rbf[idx].time_unix) + str(self.mmap.rbf[idx].time_us)),
            })
        imList = tf.repeat(tf.concat(imList, axis=0), 3, axis=-1)
        return imList, metaList


    def get2nToOldestImage(self, return16bit=False):
        counters = [slot.counter for slot in self.mmap.rbf]
        idx = int(np.where((len(counters)-2) == np.argsort(counters))[0])

        if self.counter_second == counters[idx]:
            return None, {}

        image = self.mmap.rbf[idx].image.squeeze()
        meta_data = {
            'timestamp_us': int(str(self.mmap.rbf[idx].time_unix) + str(self.mmap.rbf[idx].time_us)) ,
        }
        image = image.astype(np.uint8)
        self.counter_second = counters[idx]
        return image, meta_data

    def getNewestImage(self, return16bit=False):

        # get newest counter
        counters = [slot.counter for slot in self.mmap.rbf]

        counter_max = np.max(counters)
        counter_max_idx = np.argmax(counters)

        # return if there is no new one
        if counter_max == self.counter_last:
            # print("not new!")
            return None, {}

        image = self.mmap.rbf[counter_max_idx].image.squeeze()
        meta_data = {
            'timestamp_us': int(str(self.mmap.rbf[counter_max_idx].time_unix) + str(self.mmap.rbf[counter_max_idx].time_us)) ,
        }
        image = image.astype(np.uint8)


        self.counter_last = counter_max
        # print("img type:", image.dtype)
        return image, meta_data

    def get_frame(self, scaling=1, offX_orig=0, offY_orig=0, width_orig=None, height_orig=None, return16bit=False):
        # check for 16bit data
        image, frameInfo = self.getNewestImage()
        if image is None:
            return None
        if image.dtype == 'uint16' and not return16bit:

            if self.pct_min == None or self.pct_counter % 100 == 0:
                # calculate new min max values
                self.pct_min = np.percentile(image,1)
                self.pct_max = np.percentile(image,99)
                # print(self.pct_min,self.pct_max)

            image = ((image - self.pct_min) / (self.pct_max - self.pct_min) * 255)
            image [image < 0] = 0
            image [image > 255] = 255
            image = image.astype('uint8')
            self.pct_counter += 1

        return image

def write_config(config_path,smap):
    config = configparser.ConfigParser()
    config['Default'] = {'Version':1}
    config['Setup'] = {
        'pressure' : smap.pressure.decode('UTF-8'),
        'channel width' : '200 um',
        'channel length ': '5.8 cm',
        'imaging position after inlet' : smap.imaging_position.decode('UTF-8'),
        'bioink' : smap.bioink.decode('UTF-8'),
        'room temperature' : smap.room_temperature.decode('UTF-8'),
        'cell temperature' : '23 deg C',
    }
    config['MICROSCOPE'] = {
        'microscope' : 'Leica DM 6000',
        'objective' : '40x',
        'na' : 0.6,
        'coupler' : '0.5x',
        'condensor aperture' : smap.aperture.decode('UTF-8'),
    }
    config['CAMERA'] = {
        'exposure time' : '30 us',
        'gain' : smap.gain,
        'frame rate' : f'{smap.framerate} fps',
        'camera' : 'Basler acA20 - 520',
        'camera pixel size' : '6.9 um',
    }
    config['CELL'] = {
        'cell type' : smap.cell_type.decode('UTF-8'),
        'cell passage number' : smap.cell_passage_nr.decode('UTF-8'),
        'time after harvest ': smap.time_after_harvest.decode('UTF-8'),
        'treatment' : smap.treatment.decode('UTF-8'),
    }
    with open(config_path, 'w') as configfile:
        config.write(configfile)
    return config

def create_config(smap,config):
    config_data = {}

    config_data["magnification"] = float(config['microscope']['objective'].split()[0])
    config_data["coupler"] = float(config['microscope']['coupler'].split()[0])
    config_data["camera_pixel_size"] = float(config['camera']['camera pixel size'].split()[0])
    config_data["pixel_size"] = config_data["camera_pixel_size"] / (
            config_data["magnification"] * config_data["coupler"])  # in u meter
    config_data["px_to_um"] = config_data["pixel_size"]
    config_data["pixel_size_m"] = config_data["pixel_size"] * 1e-6  # in m
    config_data["channel_width_px"] = float(config['setup']['channel width'].split()[0]) / config_data[
        "pixel_size"]  # in pixels
    config_data["imaging_pos_mm"] = float(smap.imaging_position) * 10  # in mm

    config_data["pressure_pa"] = float(smap.pressure) * 1e5  # applied pressure (in Pa)

    config_data["channel_width_m"] = float(config['setup']['channel width'].split()[0]) * 1e-6
    config_data["channel_length_m"] = float(config['setup']['channel length'].split()[0]) * 1e-2

    config_data["cell_treatment"] = smap.treatment

    config_data["frame_rate"] = float(smap.framerate)
    return config_data