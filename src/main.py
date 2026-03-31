from argparse import ArgumentParser, RawDescriptionHelpFormatter
from .trace_docker import recreate_ebpf_map, containers_manager
from models import BpfProbe, BpfTrackedContainersRegistry
from config import MNTNSMAP

# TODO: maybe this should use the local docker tracing instead or Knative for simplicity?
def main():
    parser = ArgumentParser(description='Trace container syscalls', formatter_class=RawDescriptionHelpFormatter)

    parser.add_argument('-sc', '--scenario',
        help='''Scenario to use:
            0 -> yaml_load,
            1 -> sentiment_analyzer,
            2 -> log4shell
        ''',
        type=int
    )

    # parser.add_argument("-w", "--window_size",
    #     help="Sliding window size for syscall context (default: 3).",
    #     default=3,
    #     type=int
    # )

    # parser.add_argument("-l", "--limit",
    #     help="Maximum number of syscalls to trace before stopping (0 = no limit).",
    #     default=0,
    #     type=int
    # )

    # parser.add_argument("-e", "--exploit",
    #     help="Trigger exploit during simulation (default: disabled).",
    #     default=False,
    #     action=BooleanOptionalAction
    # )

    parser.add_argument('--mntnsmap',
        default=MNTNSMAP,
        type=str,
        help=f'BPF map path for mount namespaces (default: {MNTNSMAP}).'
    )

    # parser.add_argument('-m', '--model',
    #     help='Path to load or save the HMM model.',
    #     type=str
    # )

    # parser.add_argument("-d", "--duration",
    #     help="Simulation duration in seconds (0 = run until stopped).",
    #     type=int,
    #     default=0
    # )

    # parser.add_argument("--states",
    #     help="Number of hidden states for the HMM (default: 50).",
    #     type=int,
    #     default=50
    # )

    # parser.add_argument("--iterations",
    #     help="Number of training iterations for the HMM (default: 500).",
    #     type=int,
    #     default=500
    # )

    # parser.add_argument("-t", "--train",
    #     help="Path to training dataset",
    #     type=str
    # )

    # parser.add_argument("-v", "--validation",
    #     help="Path to training dataset",
    #     type=str,
    #     default=None
    # )

    # parser.add_argument( "--test",
    #     help="Path to testing dataset",
    #     type=str
    # )

    # parser.add_argument("-fn", "--filename",
    #     help="Custom filename for simulation outputs.",
    #     type=str
    # )

    # parser.add_argument("-b", "--baseline",
    #     help="Path to baseline dataset.",
    #     type=str
    # )

    args = parser.parse_args()
    if args.scenario != None:
        pass

    # if args.scenario != None:
    #     from src.simulation import simulate
    #     simulate(
    #         scenarioID = args.scenario,
    #         limit = args.limit,
    #         duration = args.duration,
    #         exploit = args.exploit,
    #         mntns = args.mntnsmap,
    #         window_size = args.window_size,
    #         baseline = args.baseline,
    #         filename = args.filename,
    #     )
    #     if not (args.train or args.test):
    #         exit(0)

    # if not args.model:
    #     print('ERROR: No model given.')
    #     exit(1)

    # if args.train or args.test:
    #     from models import HMM
    #     model = HMM(args.model, n_components=args.states, n_iter=args.iterations)

    # if args.train:
    #     print("Train Triggered")
    #     model.train(args.train)
    #     if not args.test:
    #         exit(0)

    # if args.test:
    #     print("Test Triggered")
    #     model.test(args.test)
    #     exit(0)

    # default behavior
    print("Tracing...")
    ebpf_map = recreate_ebpf_map(args.mntnsmap)
    containers_registry = BpfTrackedContainersRegistry()
    BpfProbe(containers_registry, args.mntnsmap)
    containers_manager(ebpf_map, containers_registry)

if __name__== '__main__':
    main()
