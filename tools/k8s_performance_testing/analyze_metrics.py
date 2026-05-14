import csv, statistics, glob
# from numpy import percentile

def calculate_stats(data_list, metric_name):
    count = len(data_list)
    if count == 0:
        return f"  [!] No valid numeric data for '{metric_name}'"

    mean_val   = statistics.mean(data_list)
    median_val = statistics.median(data_list)
    min_val    = min(data_list)
    max_val    = max(data_list)
    std_dev    = statistics.stdev(data_list) if count > 1 else 0.0

    quartiles = statistics.quantiles(data_list, n=4, method='inclusive')
    q1_val = quartiles[0]
    q3_val = quartiles[2]

    p95_val = statistics.quantiles(data_list, n=100, method='inclusive')[94] # percentile(data_list, 95)
    p95_str = f"{p95_val:.2f} ms"

    report = (
        f'  Metric: {metric_name} (Based on {count} runs)\n'
        f'  --------------------------------------------------\n'
        f'  Fastest:       {min_val:.2f} ms\n'
        f'  Lower Q (Q1):  {q1_val:.2f} ms\n'
        f'  Upper Q (Q3):  {q3_val:.2f} ms\n'
        f'  Slowest:       {max_val:.2f} ms\n'
        f'  Average:       {mean_val:.2f} ms\n'
        f'  Median:        {median_val:.2f} ms\n'
        f'  Std Dev:      ±{std_dev:.2f} ms\n'
        f'  95th Pctl:     {p95_str}\n'
    )

    return report

def analyze_all_csvs():
    # find all performance tests CSVs
    csv_files = glob.glob('data/perf_tests/*.csv')

    if not csv_files:
        print('[!] No performance tests CSVs found')
        return

    print('\n' + '=' * 60)
    print('UNIVERSAL BENCHMARK METRICS REPORT')
    print('=' * 60)

    for filepath in csv_files:
        with open(filepath, mode='r') as file:
            reader = csv.reader(file)
            header = next(reader, None)

            if not header:
                continue

            # find all column indexes that contain the word "latency"
            latency_columns = {i: col_name for i, col_name in enumerate(header) if 'latency' in col_name.lower()}

            # skip any possible files that might not have latency metrics
            if not latency_columns:
                continue

            # initialize lists to hold the data for each metric
            data_stores = {i: [] for i in latency_columns.keys()}

            # read all rows and extract the data
            for row in reader:
                if not row:
                    continue

                for col_idx in latency_columns.keys():
                    if col_idx < len(row):
                        val = row[col_idx]
                        data_stores[col_idx].append(float(val))

            # print the report for this specific file
            print(f'\nFILE: {filepath}')
            print('=' * 60)

            for col_idx, col_name in latency_columns.items():
                stats_output = calculate_stats(data_stores[col_idx], col_name)
                print(stats_output)

if __name__ == '__main__':
    analyze_all_csvs()
