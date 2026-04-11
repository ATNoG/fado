FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

# This is a single command to reduce the final image size considerably.
RUN apt update && \
  # install dependencies
  apt install -y --no-install-recommends zip bison build-essential cmake flex git libedit-dev \
    libllvm18 llvm-18-dev libclang-18-dev python3 zlib1g-dev libelf-dev libfl-dev python3-setuptools \
    liblzma-dev libdebuginfod-dev arping netperf iperf libpolly-18-dev luajit libluajit-5.1-dev python3-pip && \
  # build and install BCC
  git clone https://github.com/iovisor/bcc.git && \
  mkdir bcc/build && \
  cd bcc/build && \
  cmake .. && \
  make -j$(nproc) && \
  make install && \
  cmake -DPYTHON_CMD=python3 .. && \
  cd src/python/ && \
  make -j$(nproc) && \
  make install && \
  # cleanup
  cd / && rm -rf /bcc && \
  apt remove -y cmake git build-essential flex bison zip libedit-dev llvm-18-dev libclang-18-dev \
    libfl-dev libpolly-18-dev libluajit-5.1-dev && \
  apt autoremove -y && apt clean && \
  rm -rf /var/lib/apt/lists/*

# cleanup and app setup
WORKDIR /app
COPY . .

# install app dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt
