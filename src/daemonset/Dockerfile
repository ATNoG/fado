FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

# crictl version 1.35.0 (latest version at the time of writing)
ENV CRICTL_VERSION="v1.35.0"

# This is a single command to reduce the final image size considerably.
RUN apt update && \
  # install dependencies
  apt install -y --no-install-recommends zip bison build-essential cmake flex git libedit-dev wget kmod \
    libllvm18 llvm-18-dev libclang-18-dev python3 zlib1g-dev libelf-dev libfl-dev python3-setuptools xz-utils \
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
  # install crictl
  wget https://github.com/kubernetes-sigs/cri-tools/releases/download/${CRICTL_VERSION}/crictl-${CRICTL_VERSION}-linux-amd64.tar.gz && \
  tar zxvf crictl-${CRICTL_VERSION}-linux-amd64.tar.gz -C /usr/local/bin && \
  # cleanup
  cd / && rm -rf /bcc && \
  apt remove -y cmake git build-essential flex bison zip libedit-dev llvm-18-dev libclang-18-dev \
    libfl-dev libpolly-18-dev libluajit-5.1-dev wget && \
  apt autoremove -y && apt clean && \
  rm -rf /var/lib/apt/lists/*

# cleanup and app setup
WORKDIR /app
COPY . .

# install app dependencies
RUN pip3 install --no-cache-dir --break-system-packages -r requirements.txt

CMD ["python3", "-m", "src.trace_k8s"]
