from setuptools import setup, find_packages
exec(open('audiolm_pytorch/version.py').read())

setup(
  name = 'audiolm-pytorch',
  packages = find_packages(exclude=[]),
  version = __version__,
  license='MIT',
  description = 'AudioLM - Language Modeling Approach to Audio Generation from Google Research - Pytorch',
  author = 'Phil Wang',
  author_email = 'lucidrains@gmail.com',
  long_description_content_type = 'text/markdown',
  url = 'https://github.com/lucidrains/audiolm-pytorch',
  keywords = [
    'artificial intelligence',
    'deep learning',
    'transformers',
    'attention mechanism',
    'audio generation'
  ],
  install_requires=[
        # --------- pytorch --------- #
        'torch==2.0.*',
        'torchaudio==2.0.*',
        #'torchmetrics>=0.11.4',
        'accelerate',
        'beartype',
        'einops>=0.6.1',
        'ema-pytorch>=0.2.2',
        'lion-pytorch',
        'local-attention>=1.8.4',
        'scikit-learn',

        # --------- hydra / ray --------- #
        'hydra-core==1.3.*',
        'hydra-colorlog==1.2.*',
        'hydra-optuna-sweeper==1.2.*',

        # --------- misc --------- #
        'ray[data]==2.6.*',
        'numpy',
        'pandas',
        "wandb",
        'encodec',
        'fairseq',
        'joblib',
        'sentencepiece',
        #'augly[audio]',
        'fs',
        'fs-s3fs',
        'transformers',
        'tqdm',
        'vector-quantize-pytorch'
  ],
  classifiers=[
    'Development Status :: 4 - Beta',
    'Intended Audience :: Developers',
    'Topic :: Scientific/Engineering :: Artificial Intelligence',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.6',
  ],
)
