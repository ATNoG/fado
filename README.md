# Function-level Anomaly Detection Observer (FADO): Detecting Anomalies in Serverless Functions via eBPF System Call Tracing

FADO is a framework designed to perform fine-grained anomaly detection in serverless functions by modeling the normal behavior of system calls using Hidden Markov Models (HMMs). It enables reliable detection of both known exploits and potential zero-day attacks with minimal false positives, low latency, and a lightweight resource footprint. By leveraging function-specific system call traces and n-gram sequence modeling, FADO provides real-time observability and security in serverless computing environments.

FADO is tested in multiple real-world scenarios provided under the [scenarios](./scenarios/) folder.

## Getting Started

### Prerequisites
```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
>**Follow the BCC install described [here](https://github.com/iovisor/bcc/blob/master/INSTALL.md#ubuntu---source)**

>**For local execution, Docker is required however, it is also possible to run this on a Kubernetes/Knative cluster.**

> ⚠️ **Important:**  
> To allow eBPF to probe syscall logs, all commands must be executed with sudo using the virtual environment’s Python.

## Execution Flow (for local usage/training)

Running this locally will trace containers running in Docker.

1. **Simulation Mode (`--scenario`/`-sc`)**  
   Runs a scenario-based container simulation. 
   - Executes exploit if `--exploit`/`-e` is set.  
   - Applies sliding-window tracing with size: `--window_size`/`-w`.  
   - Saves output under `--filename`/`-fn` if provided.  

2. **Model Training (`--train`/`-t`)**  
   - Requires `--filename`/`-fn` (where to save/load the model).  
   - Requires train data file `--train`/`-t`.  
   - Builds an HMM with parameters:  
     - Hidden states: `--states`  
     - Iterations: `--iterations`  

3. **Model Testing (`--test`)**  
   - Requires `--filename`/`-fn` and `--test`.  
   - Loads the HMM from file.  

4. **Live Tracing (default fallback)**  
   - Attaches to kernel probes to trace syscalls in real-time.  

## Example Usage (for local usage/training)

### Run a Simulation
```bash
sudo venv/bin/python3 -m src.main \
    -sc 0 \                       # Scenario ID
    -d 60 \                       # Duration in seconds
    -l 10000 \                    # Stop after 10000 syscalls (0 = unlimited)
    -e \                          # Trigger exploit during simulation
    -fn output                    # Custom output filename
```

### Train Model
```bash
sudo venv/bin/python3 -m src.main \
    -fn hmm \                     # Save the model as 'hmm'
    -t train_data \               # Enable training mode
    --states 100 \                # Number of hidden states
    --iterations 200              # Training iterations
```

### Test Model
```bash
sudo venv/bin/python3 -m src.main \
    -fn hmm \                     # Use the 'hmm' model
    --test test_data \            # Enable test mode
```

### Dynamic Anomaly Detection 
```bash
sudo venv/bin/python3 -m src.main
```

## Execution Flow (in Kubernetes/Knative cluster)

To run this in Knative (run in each node):
```bash
sudo venv/bin/python3 -m src.trace_k8s
```

Run the policy controller (in a single place):
```bash
sudo venv/bin/python3 -m src.policy_controller
```

## Directory Tree
```
├── config/                 # Contains the runtime configurations for the whole project (almost)
├── data/                   # Contains generated files during training and testing
│   ├── logs/               # Data captured for training and testing
│   ├── models/             # Trained models
│   └── stats/              # Trained Model statistics
├── models/
│   ├── bpf/
│   │   ├── 
│   │   └── 
│   ├── __init__.py
│   └── hmm.py              # Classification model (train/test routines)
├── probe/
│   ├── bcc/
│   ├── __init__.py
│   └── probe.py            # Probe logic with filtering and processing
├── scenarios/              # Test scenarios
│   ├── log4shell/          # S3
│   ├── sentiment_analyzer/ # S1
│   └── yaml_load/          # S2
├── tools/                  # Additional tools
├── src/                       
│   ├── __init__.py
│   ├── cleanup_data.py     # Apply the STIDE algorithm 
│   ├── main.py             # Entry point
│   ├── simulation.py       # Data Generation
│   └── trace.py            # Dynamic Anomaly Detection
├── README.md
└── requirements.txt
```

## Licensing

This repository is licensed under the GNU GENERAL PUBLIC LICENSE 3.0. For the complete license text, see the file LICENSE. This license applies to all files in this distribution, except as noted below.

The bcc sub-directory within the probe directory is licensed under the Apache License. See the [bcc](./probe/bcc/) for the complete license text.
The log4shell scenario reutilizes code that is licensed under the same license GNU GENERAL PUBLIC LICENSE 3.0.
