#  Function-level Anomaly Detection Observer (FADO): Detecting Anomalies in Serverless Functions via eBPF System Call Tracing

FADO is a framework designed to perform fine-grained anomaly detection in serverless functions by modeling the normal behavior of system calls using Hidden Markov Models (HMMs). It enables reliable detection of both known exploits and potential zero-day attacks with minimal false positives, low latency, and a lightweight resource footprint. By leveraging function-specific system call traces and n-gram sequence modeling, FADO provides real-time observability and security in serverless computing environments.

FADO is tested in multiple real-world scenarios provided under the [scenarios](./scenarios/) folder.


## Getting Started 

### Prerequisites
```
python -m venv fado_env
source fado_env/bin/activate

pip install -r requirements.txt
```
>**Follow the BCC install described [here](https://github.com/iovisor/bcc/blob/master/INSTALL.md#ubuntu---source)**

> ⚠️ **Important:**  
> To allow eBPF to probe syscall logs, all commands must be executed with sudo using the virtual environment’s Python.

### Filtering Syscalls from Containers

To ensure the framework traces **only the system calls executed inside containers**, we use an eBPF hash map (`BPF_HASH`) that stores the mount namespace ID (`mnt_ns`) of the container we want to monitor.  

At runtime, the tracing logic will filter syscalls so that **only the ones matching the stored `mnt_ns` ID are recorded**.  

> ⚠️ **Current Limitation:**  
> The framework supports **only one container at a time**. Every time you launch a new container, you must manually update the map with the namespace ID of that container and stop or remove the previous one. Otherwise, syscalls from the new container will not be captured.  

### Setup Instructions
This script can be used to tell FADO the container namespace to trace. It automatically passes the one corresponding to the firts container ID it finds, to specify it set the CONTAINERID accordingly.

> ⚠️ **Launch the container to be traced prior to this setup**

```
sudo bpftool map create /sys/fs/bpf/mnt_ns_set type hash key 8 value 4 entries 128 \
        name mnt_ns_set flags 0

FILE=/sys/fs/bpf/mnt_ns_set
if [ $(printf '\1' | od -dAn) -eq 1 ]; then
 HOST_ENDIAN_CMD=tac
else
  HOST_ENDIAN_CMD=cat
fi

# ENTER MANUALLY IF MORE THAN ONE CONTAINER ACTIVE
CONTAINERID="$(docker ps -q | head -n 1)" 

NS_ID_HEX="$(printf '%016x' $(sudo stat -Lc '%i' /proc/$(docker inspect --format '{{.State.Pid}}' $CONTAINERID)/ns/mnt) | sed 's/.\{2\}/&\n/g' | $HOST_ENDIAN_CMD)"
sudo bpftool map update pinned $FILE key hex $NS_ID_HEX value hex 00 00 00 00 any

```

To check the entries already in the map
```
 sudo bpftool map dump pinned /sys/fs/bpf/mnt_ns_set
```


## Execution Flow

1. **Simulation Mode (`--simulation`)**  
   Runs a scenario-based container simulation. 
   - Executes exploit if `--exploit` is set.  
   - Applies sliding-window tracing (`--window_size`).  
   - Saves output under `--filename` if provided.  
   - Exits unless `--train` or `--test` are also requested.  

2. **Model Training (`--train`)**  
   - Requires `--model_file` (where to save/load the model).  
   - Requires train data file `--train`.  
   - Builds an HMM with parameters:  
     - Hidden states: `--states`  
     - Iterations: `--iterations`  
   - Saves the trained model to `--model_file`.  

3. **Model Testing (`--test`)**  
   - Requires `--model_file` and `--test`.  
   - Loads the HMM from file.  

4. **Live Tracing (default fallback)**  
   - If no `--simulation`, `--train`, or `--test` is specified:  
   - Attaches to kernel probes to trace syscalls in real-time.  
   - Performs anomaly detection using `--model_file`.  

> **Note:** The performance values presented in the associated document were obtained using a specialized venv with only the __hmmlearn__ lib installed. To allow its use, comment the first 2 lines [here](utils/__init__.py)


## Example Commands

### Run a Simulation
```
sudo venv/bin/python3 -m src.main \
    -sc 1 \                       # Scenario ID
    -d 60 \                       # Duration in seconds
    -l 10000 \                    # Stop after 10000 syscalls (0 = unlimited)
    -e \                          # Trigger exploit during simulation
    -fn output                    # Custom output filename
```

### Train Model
```
sudo venv/bin/python3 -m src.main -m hmm \
    -t train_data \                # Enable training mode
    --states 100 \                 # Number of hidden states
    --iterations 200               # Training iterations
```

### Test Model
```
sudo venv/bin/python3 -m src.main -m hmm \
    --test test_data \     # Enable test mode
```

### Dynamic Anomaly Detection 
```
sudo venv/bin/python3 -m src.main -m hmm
```

## Directory Tree
```
├── data/                   # Containing generated files during training and testing
|   ├── figs/               # Plots, figures
|   ├── files/              # Saved models
|   ├── logs/               # Generated data
|   └── stats/              # Model statistics
├── models/
│   ├── __init__.py
│   └── hmm.py              # Classification model (train/test routines)
├── probe/
│   ├── bcc/
│   ├── __init__.py
│   └── probe.py            # Probe logic with filtering and processing
├── scenarios/              # Test scenarios
│   ├── log4jpwn/           # S3
│   ├── sentiment_analyzer/ # S1
│   └── yaml_load/          # S2
├── tools/                  # Additional tools
├── src/                       
│   ├── __init__.py
|   ├── cleanup_data.py     # Apply the STIDE algorithm 
│   ├── main.py             # Entry point
│   ├── simulation.py       # Data Generation
│   └── trace.py            # Dynamic Anomaly Detection
├── utils/
├── README.md
└── requirements.txt
```

## Licensing

This repository is licensed under the GNU GENERAL PUBLIC LICENSE 3.0. For the complete license text, see the file LICENSE. This license applies to all files in this distribution, except as noted below.

The bcc sub-directory within the probe directory is licensed under the Apache License. See the [bcc](./probe/bcc/) for the complete license text.
The log4shell scenario reutilizes code that is licensed under the same license GNU GENERAL PUBLIC LICENSE 3.0.