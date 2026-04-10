FROM ubuntu:24.04
ENV DEBIAN_FRONTEND=noninteractive

# install the dependencies
RUN apt install -y zip bison build-essential cmake flex git libedit-dev \
  libllvm18 llvm-18-dev libclang-18-dev python3 zlib1g-dev libelf-dev libfl-dev python3-setuptools \
  liblzma-dev libdebuginfod-dev arping netperf iperf libpolly-18-dev luajit luajit-5.1-dev python3-pip

# compile and install BCC
RUN git clone https://github.com/iovisor/bcc.git
RUN mkdir bcc/build; cd bcc/build
RUN cmake ..
RUN make
RUN make install
RUN cmake -DPYTHON_CMD=python3 ..
RUN pushd src/python/
RUN make
RUN make install
RUN popd

# setup the app
WORKDIR /app
COPY . .
