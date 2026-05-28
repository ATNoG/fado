import csv, statistics, glob, math
import matplotlib.pyplot as plt
import seaborn as sns

def calculate_stats(data_list, metric_name):
    count = len(data_list)
    if count == 0:
        return f"  [!] No valid numeric data for '{metric_name}'"

    mean_val   = statistics.mean(data_list)
    median_val = statistics.median(data_list)
    min_val    = min(data_list)
    max_val    = max(data_list)

    std_dev    = statistics.stdev(data_list) if count > 1 else 0.0
    std_error  = (std_dev / math.sqrt(count)) if count > 0 else 0.0

    quartiles = statistics.quantiles(data_list, n=4, method='inclusive')
    q1_val = quartiles[0]
    q3_val = quartiles[2]

    p95_val = statistics.quantiles(data_list, n=100, method='inclusive')[94]
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
        f'  Std Error:    ±{std_error:.2f} ms\n'
        f'  95th Pctl:     {p95_str}\n'
    )

    return report

def generate_boxplots(metrics_dict, filepath):
    if not metrics_dict:
        return

    # set up the visual style
    plt.figure(figsize=(10, 6))
    sns.set_theme(style="whitegrid")

    data_arrays = list(metrics_dict.values())
    labels = list(metrics_dict.keys())

    # create the boxplot
    ax = sns.boxplot(data=data_arrays, palette="Set2", width=0.5)

    # Customize the labels and title
    plt.xticks(ticks=range(len(labels)), labels=labels)
    plt.ylabel("Latency (ms)", fontweight='bold')

    # save the plot next to the CSV file
    plot_filename = filepath.replace('.csv', '_boxplot.pdf')
    plt.tight_layout()
    plt.savefig(plot_filename, format='pdf', bbox_inches='tight')
    plt.close()

    print(f"  [+] Saved box plot graphic to: {plot_filename}")

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

            if not latency_columns:
                continue

            data_stores = {i: [] for i in latency_columns.keys()}

            # read all rows and extract the data
            for row in reader:
                if not row:
                    continue

                for col_idx in latency_columns.keys():
                    if col_idx < len(row):
                        val = row[col_idx]
                        try:
                            data_stores[col_idx].append(float(val))
                        except ValueError:
                            pass 

            print(f'\nFILE: {filepath}')
            print('=' * 60)

            plot_data = {}
            for col_idx, col_name in latency_columns.items():
                clean_data = data_stores[col_idx]
                plot_data[col_name] = clean_data

                stats_output = calculate_stats(clean_data, col_name)
                print(stats_output)

            # generate the visualization for this file
            generate_boxplots(plot_data, filepath)

if __name__ == '__main__':
    analyze_all_csvs()
