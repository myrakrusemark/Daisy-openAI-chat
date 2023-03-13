from dotenv import load_dotenv
import logging

#
# Copyright 2018-2021 Picovoice Inc.
#
# You may not use this file except in compliance with the license. A copy of the license is located in the "LICENSE"
# file accompanying this source.
#
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on
# an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the
# specific language governing permissions and limitations under the License.
#

import argparse
import os
import struct
import wave
import platform
from datetime import datetime

import pvporcupine
from pvrecorder import PvRecorder

load_dotenv()

class Porcupine():
    """
    Microphone Demo for Porcupine wake word engine. It creates an input audio stream from a microphone, monitors it, and
    upon detecting the specified wake word(s) prints the detection time and wake word on console. It optionally saves
    the recorded audio into a file for further debugging.
    """

    def __init__(
            self,
            keyword_paths,
            sensitivities,
            input_device_index=int(os.environ["INPUT_DEVICE"]),
            ):

        """
        Constructor.

        :param keyword_paths: Absolute paths to keyword model files.
        :param sensitivities: Sensitivities for detecting keywords. Each value should be a number within [0, 1]. A
        higher sensitivity results in fewer misses at the cost of increasing the false alarm rate. If not set 0.5 will
        be used.
        :param input_device_index: Optional argument. If provided, audio is recorded from this input device. Otherwise,
        the default audio input device is used.
        """

        super(Porcupine, self).__init__()

        self._access_key = os.environ["PORCUPINE_KEY"]
        #self._library_path = None #library_path
        #self._model_path = model_path
        self._keyword_paths = [keyword_paths]
        self._sensitivities = [sensitivities]
        self._input_device_index = input_device_index
        #self._output_path = output_path

    def run(self):
        """
         Creates an input audio stream, instantiates an instance of Porcupine object, and monitors the audio stream for
         occurrences of the wake word(s). It prints the time of detection for each occurrence and the wake word.
         """

        keywords = list()
        for x in self._keyword_paths:
            keyword_phrase_part = os.path.basename(x).replace('.ppn', '').split('_')
            if len(keyword_phrase_part) > 6:
                keywords.append(' '.join(keyword_phrase_part[0:-6]))
            else:
                keywords.append(keyword_phrase_part[0])

        porcupine = None
        recorder = None
        wav_file = None
        try:
            porcupine = pvporcupine.create(
                access_key=self._access_key,
                #library_path=self._library_path,
                #model_path=self._model_path,
                keyword_paths=self._keyword_paths,
                sensitivities=self._sensitivities)
            recorder = PvRecorder(device_index=self._input_device_index, frame_length=porcupine.frame_length)
            recorder.start()

            #if self._output_path is not None:
            #    wav_file = wave.open(self._output_path, "w")
            #    wav_file.setparams((1, 2, 16000, 512, "NONE", "NONE"))

            logging.debug('Using device: %s' % recorder.selected_device)

            logging.info('Listening {')
            for keyword, sensitivity in zip(keywords, self._sensitivities):
                logging.info('  %s (%.2f)' % (keyword, sensitivity))
            logging.info('}')

            while True:
                pcm = recorder.read()

                if wav_file is not None:
                    wav_file.writeframes(struct.pack("h" * len(pcm), *pcm))

                result = porcupine.process(pcm)
                if result >= 0:
                    logging.debug('[%s] Detected %s' % (str(datetime.now()), keywords[result]))
                    return True
        except pvporcupine.PorcupineInvalidArgumentError as e:
            args = (
                self._access_key,
                #self._library_path,
                #self._model_path,
                self._keyword_paths,
                self._sensitivities,
            )
            logging.error("One or more arguments provided to Porcupine is invalid: ", args)
            logging.error("If all other arguments seem valid, ensure that '%s' is a valid AccessKey" % self._access_key)
            raise e

        except pvporcupine.PorcupineActivationError as e:
            logging.error("AccessKey activation error")
            raise e
        except pvporcupine.PorcupineActivationLimitError as e:
            logging.error("AccessKey '%s' has reached it's temporary device limit" % self._access_key)
            raise e
        except pvporcupine.PorcupineActivationRefusedError as e:
            logging.error("AccessKey '%s' refused" % self._access_key)
            raise e
        except pvporcupine.PorcupineActivationThrottledError as e:
            logging.error("AccessKey '%s' has been throttled" % self._access_key)
            raise e
        except pvporcupine.PorcupineError as e:
            logging.error("Failed to initialize Porcupine")
            raise e
        except KeyboardInterrupt:
            logging.error('Stopping ...')
        finally:
            if porcupine is not None:
                porcupine.delete()

            if recorder is not None:
                recorder.delete()

            if wav_file is not None:
                wav_file.close()

    @classmethod
    def show_audio_devices(cls):
        devices = PvRecorder.get_audio_devices()

        for i in range(len(devices)):
            logging.info('index: %d, device name: %s' % (i, devices[i]))

#Instantiate DEFAULT ("daisy daisy") wake word
keyword_paths = None
if platform.system() == "Windows":
    keyword_paths = "plugins/daisy-daisy_en_windows_v2_1_0.ppn"
elif platform.system() == "Linux":
    keyword_paths = "plugins/daisy-daisy_en_raspberry-pi_v2_1_0.ppn"
else:
    logging.error("Unknown operating system, can't load wake word model.")
instance = Porcupine(
                keyword_paths=keyword_paths,
                sensitivities=0.5)