from argparse import ArgumentParser, RawDescriptionHelpFormatter, BooleanOptionalAction
from models import BpfProbe, BpfTrackedContainersRegistry, Scenario, HMM
from .trace_docker import create_ebpf_map, containers_manager
from .simulation import simulate

def main():
    parser = ArgumentParser(description='Trace container syscalls', formatter_class=RawDescriptionHelpFormatter)

    parser.add_argument('-sc', '--scenario', type = int,
        help='''Scenario to use:
            0 -> yaml_load,
            1 -> sentiment_analyzer,
            2 -> log4shell
        '''
    )

    parser.add_argument('-w', '--window_size', type=int, default=3,
        help='Sliding window size for syscall context (default: 3).'
    )

    parser.add_argument('-l', '--limit', type=int, default=0,
        help='Maximum number of syscalls to trace before stopping (0 = no limit).'
    )

    parser.add_argument('-e', '--exploit', default=False, action=BooleanOptionalAction,
        help='Trigger exploit during simulation (default: disabled).'
    )

    parser.add_argument('-d', '--duration', type=int, default=0,
        help='Simulation duration in seconds (0 = run until stopped).'
    )

    parser.add_argument('--states', type=int, default=50,
        help='Number of hidden states for the HMM (default: 50).'
    )

    parser.add_argument('--iterations', type=int, default=500,
        help='Number of training iterations for the HMM (default: 500).'
    )

    parser.add_argument('-t', '--train', type=str,
        help='Path to training dataset.'
    )

    parser.add_argument( '--test', type=str,
        help='Path to testing dataset.'
    )

    parser.add_argument('-fn', '--filename', type=str,
        help='Custom filename for inputs/outputs.'
    )

    args = parser.parse_args()
    if args.scenario != None:
        print('Simulating...')
        ebpf, ebpf_map = create_ebpf_map()
        containers_registry = BpfTrackedContainersRegistry()
        BpfProbe(containers_registry, ebpf)
        queue = containers_manager(ebpf_map, containers_registry, track_scenario=Scenario(args.scenario))
        simulate(args.scenario, queue, args.limit, args.duration, args.exploit, args.window_size, args.filename)
        return

    if args.train or args.test:
        if not args.filename:
            print('Please provide a filename to save/load the HMM.')
            return

        model = HMM(args.filename, n_components=args.states, n_iter=args.iterations)
        if args.train:
            print('Training...')
            model.train(args.train)

        if args.test:
            print('Testing...')
            model.test(args.test)

        return

    # default behavior
    print('Tracing...')
    ebpf, ebpf_map = create_ebpf_map()
    containers_registry = BpfTrackedContainersRegistry()
    BpfProbe(containers_registry, ebpf)
    containers_manager(ebpf_map, containers_registry)

if __name__== '__main__':
    main()
