FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-runtime
#FROM public.ecr.aws/lambda/python:3.9

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone && \
    apt update -y && \
    apt upgrade -y && \
    apt install -y software-properties-common curl wget ffmpeg zip bzip2 p7zip-full ca-certificates sudo git git-lfs python3-pip python-is-python3 &&\
    apt clean all -y && \
    pip install --no-cache-dir torch==2.0.* torchaudio==2.0.* torchvision==0.15.* boto3 aws_lambda_powertools[all] aws_xray_sdk awscli aws-sam-cli awslambdaric &&\
    pip cache purge && \
    rm -rf /var/lib/apt/lists/*

RUN NONINTERACTIVE=1 /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" &&\
    (echo; echo 'eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)"') >> /root/.bashrc
RUN eval "$(/home/linuxbrew/.linuxbrew/bin/brew shellenv)" && brew install zsh nushell oh-my-posh aws-sam-cli
RUN eval "$(oh-my-posh init bash --config $(brew --prefix oh-my-posh)/themes/easy-term.omp.json)" >> ~/.bashrc 

#WORKDIR /
#COPY . ./
#RUN pip install -r ./seabassai-api/app/requirements.txt
