import json
import random
from aws_lambda_powertools import Logger
from aws_lambda_powertools import Tracer
from aws_lambda_powertools import Metrics
import boto3
import augly.audio as audaugs
from hydra import compose, initialize
from omegaconf import OmegaConf
import torchaudio
from random import shuffle
from fs.osfs import OSFS
from fs.mountfs import MountFS
from fs import open_fs
from typing import List


@dataclass 
class SampleConfig:
    sources: List[str]
    sample_rate: int
    min_length: float
    max_length: float
    augmentations: List[str]

@dataclass
class DataSourceConfig:
    name: str
    fs_url: str

@dataclass 
class Config:
    sample_cfg: SampleConfig
    batch_size: int
    sources: List[DataSourceConfig]
    augmentations: List[str]
    use_cache: bool
    cache_dir: str

class BatchMaker():
    def __init__(self, batcher_id: str, config: Config):
            self.batcher_id = batcher_id
            self.config = config

            self.mount_sources()

            # db schema:
            # batcher_id: string
            # batch_id: string  # (None if batch is not used yet)
            # s3_key: string # Key of the actual data in the S3 bucket
            #self.dynamo_db = boto3.resource('dynamodb')
            #self.filedb_name = f'batcher-files-{self.batcher_id}'
            #self.filedb_table = self.dynamo_db.Table(self.filedb_name)

    def initialize(self, config: dict):
        #self.create_file_db(drop_old=True, scan_files=True)
        pass

    def mount_sources(self):
        # Setup filesystem
        self.dataset_fs = MountFS()

        for filesource in self.config.sources:
            source_fs = open_fs(filesource.fs_url)
            self.dataset_fs.mount(filesource.name, source_fs)

    #def get_status(self) -> str:
    #    status = {
    #        'batcher_id': self.batcher_id,
    #        'sources': self.config.sources,
    #    }
    #    
    #    return json.dumps(status)

    def create_file_db(self, drop_old: bool = True, scan_files: bool = True):
        ## Drop the old DB if it exists
        #if self.filedb_table and drop_old:
        #    self.filedb_table.delete()
        #
        #self.filedb_table = self.dynamo_db.create_table(
        #    TableName=self.filedb_table_name,
        #    KeySchema=[
        #        {
        #            'AttributeName': 'batcher_id',
        #            'KeyType': 'HASH'  # Partition key
        #        },
        #        {
        #            'AttributeName': 'file_id',
        #            'KeyType': 'HASH'  # Sort key
        #        }
        #    ],
        #    AttributeDefinitions=[
        #        {
        #            'AttributeName': 'batcher_id',
        #            'AttributeType': 'S'
        #        },
        #        {
        #            'AttributeName': 'file_id',
        #            'AttributeType': 'S'
        #        },
        #        {
        #            'AttributeName': 'file_bucket',
        #            'AttributeType': 'S'
        #        },
        #        {
        #            'AttributeName': 'file_key',
        #            'AttributeType': 'S'
        #        },
        #    ],
        #    ProvisionedThroughput={
        #        'ReadCapacityUnits': 5,
        #        'WriteCapacityUnits': 5
        #    }
        #)
        
        # Get all music files and shuffle them
        if scan_files:
            music_files = []
            for path in self.dataset_fs.walk.files(filter=['*.mp3']):
                music_files.append(path)
            random.shuffle(music_files)
            
            # TODO: Add to DB
            self.file_list = music_files

    # Pick a random batch from the files database
    def get_file(self, index:int):
        #if self.table:
        #    self.table.scan().ge
        #
        file = self.file_list[index]
        return file

    def get_file_obj(self, index:int):
        file = self.get_file(index)
        with self.dataset_fs.open(file):
        return files

    # Pushes the batch info to the pool of available batches on the DynamoDB table
    def push_batch(self, batch):
        #self.table.put_item(Item=batch)
        pass
    
    def pop_batch(self):
        #batch = self.table.get_item(Key={'batch_id': self.batch_id})
        #return batch['Item']
        return {}