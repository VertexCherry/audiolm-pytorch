from dataclasses import dataclass
from hashlib import md5
import json
from os import name
import random
from string import hexdigits
from uuid import uuid3
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools import Metrics
import boto3
from sympy import Ray
import augly.audio as audaugs
from hydra import compose, initialize
from omegaconf import OmegaConf
import torchaudio
from random import shuffle
from fs.osfs import OSFS
from fs.mountfs import MountFS
from fs import open_fs
from typing import List
import pandas as pd
from time import sleep
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn
from rich.table import Table

@dataclass
class SourcesConfig:
    name: str
    fs_url: str

@dataclass
class SampleLoadConfig:
    sampling_rate: int

@dataclass
class DistributedSampleLoaderConfig:
    sources: List[SourcesConfig]
    prefetch_count: int

@ray.remote
def load_sample(file, SampleLoadConfig):
    pass

@Ray.remote
class DistributedSampleLoader:
    def __init__(self, config: DistributedSampleLoaderConfig):
        self.config = config
        
        self.prefecth = []
        self.prefecth_index = 0
        
        self.build_dataset_fs()
        self.enumerate_files()
        
    def prefetch_samples(self):
        if len(self.prefecth) < self.config.prefetch_count:
            self.prefecth.extend(self.files[self.prefecth_index:self.prefecth_index + self.config.prefetch_count])
            self.prefecth_index += self.config.prefetch_count
        
    def enumerate_files(self):
        self.files = list(self.dataset_fs.walk.files(filter=['*.mp3']))
        random.shuffle(self.files)

        #shuffle(self.files)
        #self.files_df = pd.DataFrame({
        #    "idx": range(len(self.files)),
        #    "uid": [md5(file.encode('utf-8').hexdigits()) for _, file in enumerate(self.files)]
        #    "file": self.files,
        #})
        #ds = ray.data.from_pandas(df)
    
    def build_dataset_fs(self):
        self.dataset_fs = MountFS()
        for source in self.config.sources:
            self.dataset_fs.mount(source.name, open_fs(source.fs_url))
    
    def get_sample(self, index: int):
        pass
    
    def start(self):
        self.prefetch_samples()
        
        
@ray.remote
class SeabassBatcherComputer():
    def __init__(self, clip_len:float = 2.0, sample_rate=16000):
        self.clip_len = clip_len
        self.sample_rate = sample_rate

    def getSample(self, filename):
        with self.fs.open(filename, 'rb') as f:
            reader = torchaudio.io.StreamReader(src = f)
            reader.add_basic_audio_stream(
                frames_per_chunk=self.sample_rate//10,
                stream_index=0,
                sample_rate=self.sample_rate,
            )

            audio_tensor = None
            for i, waveform in enumerate(reader.stream()):
                if audio_tensor is None:
                    audio_tensor = waveform[0]
                else:
                    audio_tensor = torch.cat((audio_tensor, waveform[0]), 0)
                
                streamed_len = (audio_tensor.shape[0] / self.sample_rate) 
                if streamed_len >= self.clip_len:
                    break # we have enough data

            audio_tensor = audio_tensor.reshape(1, -1) 
            if audio_tensor.shape[0] > 1:
                # the audio has more than 1 channel, convert to mono
                audio_tensor = torch.mean(audio_tensor, dim=0).unsqueeze(0)

            output = []
            audio_length = audio_tensor.size(1)

            ## pad or curtail
            #max_length = 99999999999999
            #if audio_length > max_length:
            #    max_start = audio_length - max_length
            #    start = torch.randint(0, max_start, (1, ))
            #    audio_tensor = audio_tensor[:, start:start + max_length]
            #else:
            #    audio_tensor = F.pad(audio_tensor, (0, max_length - audio_length), 'constant')

            audio_tensor = rearrange(audio_tensor, '1 ... -> ...')
            output = audio_tensor.float()
            return output

class SeabassIterableDataset(torch.utils.data.IterableDataset):
    def __init__(self, start, end, files: list[str], fs: MountFS, effects, clip_len:float = 2.0, tick_char='.', sample_rate=16000, sample_buffer_size=128):
        super(SeabassIterableDataset).__init__()
        self.start = start
        self.end = end
        self.effects = effects
        self.files = files
        self.fs = fs
        self.clip_len = clip_len
        self.tick_char = tick_char
        self.sample_rate = sample_rate
        self.sample_buffer_size = sample_buffer_size
        self.batcher = SeabassBatcherComputer.remote(clip_len, sample_rate)
        self.pending_samples = []
        
    # Start producing sasmples
    def run(self):
        self.pending_samples.extend(self.batcher.getSample.remote(self.files[i]) for i in range(self.sample_buffer_size))

    def getSample(self, index):
        ready_refs, self.pending_samples = ray.wait(self.pending_samples, num_returns=1)
        sample = ray.get(*ready_refs)
        ready_refs.append(self.batcher.getSample.remote(self.files[index + self.sample_buffer_size]))
        return sample
    
    def __iter__(self):
        worker_info = torch.utils.data.get_worker_info()
        if worker_info is None:  # single-process data loading, return the full iterator
            iter_start = self.start
            iter_end = self.end
        else:  # in a worker process
            # split workload
            per_worker = int(math.ceil((self.end - self.start) / float(worker_info.num_workers)))
            worker_id = worker_info.id
            iter_start = self.start + worker_id * per_worker
            iter_end = min(iter_start + per_worker, self.end)

        for i in range(iter_start, iter_end):
            sample = self.getSample(i)
            yield sample
