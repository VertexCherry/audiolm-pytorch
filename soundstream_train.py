#%%
# imports
import math
import wave
import struct
import os
import urllib.request
import tarfile
import random

import logging

import hydra
logging.basicConfig(level=logging.INFO)

from audiolm_pytorch import (
    SoundStream, SoundStreamTrainer, HubertWithKmeans, SemanticTransformer, SemanticTransformerTrainer, HubertWithKmeans,
    CoarseTransformer, CoarseTransformerWrapper, CoarseTransformerTrainer, FineTransformer, FineTransformerWrapper, 
    FineTransformerTrainer, AudioLM )
from torch import nn
import torch
import torchaudio
import ray
from random import shuffle
from fs.osfs import OSFS
from fs.mountfs import MountFS
from fs import open_fs
import math
from email.mime import audio
from io import BytesIO
import os
import random
import itertools
from time import time
from einops import rearrange
import fs.info
from torchaudio.functional import resample
from torch import Tensor
import torch.nn.functional as F
from audiolm_pytorch.soundstream import cast_tuple
from audiolm_pytorch.utils import curtail_to_multiple

soundstream = SoundStream(
    codebook_size = 1024,
    rq_num_quantizers = 8,
)

sample_rate = 24000
dataset_folder = "placeholder_dataset"
soundstream_ckpt = "results/soundstream.8.pt" # this can change depending on number of steps

ray.init(num_cpus=16, num_gpus=1)

#%%
# Scan dataset
from loader import DistributedSampleLoader, DistributedSampleLoaderConfig, SourcesConfig, SampleLoadConfig
from loader import SeabassIterableDataset


# Setup dataloader
effects = [
    ["norm", "1"],
]

#needed_clip_len = float(320 * 40)/sample_rate
#train_subset = music_files[:-1000]
#val_subset = music_files[-1000:]
#
#ds_t = SeabassIterableDataset(start=0, end=len(train_subset), files=train_subset, 
#                            fs=dataset_fs, effects=effects, clip_len=needed_clip_len)

#ds_v = SeabassIterableDataset(start=0, end=len(val_subset), files=val_subset, 
#                            fs=dataset_fs, effects=effects, clip_len=2.0, tick_char='*')

#ds_t.run()
#sample = ds_t.getSample(0)
#time.sleep(3)
#ds_v.run()

#%%
# Do training
def do_training():
    trainer = SoundStreamTrainer(
        soundstream,
        #folder = dataset_folder,
        #train_dataloader=dl_train,
        #val_dataloader=dl_val,
        train_dataset=dst,
        val_dataset=dsv,
        #lr = 0.001,
        batch_size = 12,
        grad_accum_every = 8,         # effective batch size of 32
        data_max_length = 320 * 32,
        save_results_every = 20,
        save_model_every = 100,
        num_train_steps = 2000,
    ).cuda()
    # NOTE: I changed num_train_steps to 9 (aka 8 + 1) from 10000 to make things go faster for demo purposes
    # adjusting save_*_every variables for the same reason

    trainer.train()

@hydra.main(config_path="config", config_name="config")
def main(cfg):
    global dataset_folder, soundstream_ckpt, sample_rate
    dataset_folder = cfg.dataset_folder
    soundstream_ckpt = cfg.soundstream_ckpt
    sample_rate = cfg.sample_rate
    dataset_fs = open_fs(dataset_folder)
    logging.info(f"Dataset folder: {dataset_folder}")
    logging.info(f"Soundstream checkpoint: {soundstream_ckpt}")
    logging.info(f"Sample rate: {sample_rate}")
    logging.info(f"Dataset filesystem: {dataset_fs}")
    logging.info(f"Dataset filesystem info: {fs.info.info(dataset_fs)}")

    # Scan dataset
    logging.info("Scanning dataset")
    music_files = []
    for path in dataset_fs.walk.files(filter=["*.mp3", "*.flac", "*.wav"]):
        music_files.append(path)
    logging.info(f"Found {len(music_files)} music files in dataset")
    shuffle(music_files)
    needed_clip_len = float(320 * 40)/sample_rate
    train_subset = music_files[:-1000]
    val_subset = music_files[-1000:]

    # Setup dataloader
    logging.info("Setting up dataloader")
    effects = [
        ["norm", "1"],
    ]
    dl_train = DistributedSampleLoader(
        DistributedSampleLoaderConfig(
            sources=SourcesConfig(
                files=train_subset,
                fs=dataset_fs,
                effects=effects,
                clip_len=needed_clip_len,
                tick_char='*',
            ),
            sample_load=SampleLoadConfig(
                sr=sample_rate,
                channels=2,
                dtype="float32",
            ),
            batch_size=12,
            shuffle=True,
            num_workers=8,
            prefetch_factor=2,
            persistent_workers=True,
            pin_memory=True,
            drop_last=True,
        )
    )
    dl_val = DistributedSampleLoader(
        DistributedSampleLoaderConfig(
            sources=SourcesConfig(
                files=val_subset,
                fs=dataset_fs,
                effects=effects,
                clip_len=2.0,
                tick_char='*',
            ),
            sample_load=SampleLoadConfig(
                sr=sample_rate,
                channels=2,
                dtype="float32",
            ),
            batch_size=12,
            shuffle=False,
            num_workers=8,
            prefetch_factor=2,
            persistent_workers=True,
            pin_memory=True,
            drop_last=True,
        )
    )
    logging.info("Setting up dataset")
    dst = SeabassIterableDataset(start=0, end=len(train_subset), files=train_subset,
                                 fs=dataset_fs, effects=effects, clip_len=needed_clip_len)
    dsv = SeabassIterableDataset(start=0, end=len(val_subset), files=val_subset,
                                 fs=dataset_fs, effects=effects, clip_len=2.0, tick_char='*')
    dst.run()
    dsv.run()
    
    # Do training
    do_training()