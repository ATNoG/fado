from src.simulation import simulate
from src.trace import trace
from models import HMM
import argparse

def main():
    parser = argparse.ArgumentParser(
        description="Trace container syscalls",
        formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("-sc", "--scenario",
        help="""Scenario to use:
            0 → yaml_load
            1 → sentiment_analyzer
            2 → log4jpwn
        """,
        type=int)
    parser.add_argument("-w", "--window_size",
        help="Sliding window size for syscall context (default: 3).",
        default=3,
        type=int)
    parser.add_argument("-l", "--limit",
        help="Maximum number of syscalls to trace before stopping (0 = no limit).",
        default=0,
        type=int)
    # parser.add_argument("-tol", "--tolerance",
    #     help="Classification tolerance threshold (default: 0.6).",
    #     default=0.6,
    #     type=float)
    # parser.add_argument("-g", "--generalization",
    #     help="Abstract most frequent sequences (default: 0.02).",
    #     default=0.02,
    #     type=float)
    parser.add_argument("-e", "--exploit",
        help="Trigger exploit during simulation (default: disabled).",
        default=False,
        action=argparse.BooleanOptionalAction)
    parser.add_argument("--mntnsmap",
        default="/sys/fs/bpf/mnt_ns_set",
        type=str,
        help="BPF map path for mount namespace (default: /sys/fs/bpf/mnt_ns_set).")
    parser.add_argument("-m", "--model_file",
        help="Path to load or save the HMM model.",
        type=str)
    parser.add_argument("-d", "--duration",
        help="Simulation duration in seconds (0 = run until stopped).",
        type=int,
        default=0)
    parser.add_argument("--states",
            help="Number of hidden states for the HMM (default: 50).",
            type=int,
            default=50)
    parser.add_argument("--iterations",
            help="Number of training iterations for the HMM (default: 500).",
            type=int,
            default=500)
    parser.add_argument("-t", "--train",
            help="Path to training dataset",
            type=str)
    parser.add_argument("-v", "--validation",
            help="Path to training dataset",
            type=str,
            default=None)
    parser.add_argument( "--test",
            help="Path to testing dataset",
            type=str)
    parser.add_argument("-fn", "--filename",
            help="Custom filename for simulation outputs.",
            type=str)
    parser.add_argument("-b", "--baseline",
            help="Path to baseline dataset.",
            type=str)
    # parser.add_argument("-s", "--simulation",
    #         help="Enable simulation mode.",
    #         action=argparse.BooleanOptionalAction)
    # parser.add_argument("-t", "--train",
    #         help="Train Prediction Model",
    #         action=argparse.BooleanOptionalAction)
    # parser.add_argument("--test",
    #         help="Test Prediction Model",
    #         action=argparse.BooleanOptionalAction)
    args = parser.parse_args()
    
    if args.scenario != None:
        simulate(
            scenarioID = args.scenario,
            limit = args.limit,
            duration = args.duration,
            exploit = args.exploit,
            mntns = args.mntnsmap,
            window_size = args.window_size,
            baseline = args.baseline,
            filename = args.filename,
        )
        if not (args.train or args.test):
            exit()
        
    if not args.model_file:
        print("No model given")
        exit(-1)

    if args.train or args.test:
        model = HMM(args.model_file,
                     n_components=args.states,
                     n_iter=args.iterations)

    if args.train:
        # if not args.train_data:
        #     print("Missing train data")
        #     exit(-1)

        print("Train Triggered")
        model.train(args.train)
        if not args.test:
            exit(0)

    if args.test:
        # if not args.test_data:
        #     print("Missing test data")
        #     exit(-1)

        print("Test Triggered")
        model.test(args.test)
        exit(0)

    print("Tracing...")
    trace(
        model_file = args.model_file, 
        mntns = args.mntnsmap)
    exit(0)

if __name__== '__main__':
    main()