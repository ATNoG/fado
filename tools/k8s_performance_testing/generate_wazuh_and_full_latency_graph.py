import csv, glob, os, math, statistics
import matplotlib.pyplot as plt
import seaborn as sns

def generate_propagation_plot():
    csv_files = glob.glob('data/perf_tests/*.csv')

    if not csv_files:
        print('[!] No performance tests CSVs found in data/perf_tests/')
        return

    # Our two specific buckets for this plot
    plot_data = {
        'Wazuh Latency': [],
        'Total Agent Latency': []
    }

    print("[*] Searching for End-to-End MTTD data...")
    found_data = False

    for filepath in csv_files:
        with open(filepath, mode='r') as file:
            reader = csv.reader(file)
            header = next(reader, None)

            if not header:
                continue

            header_lower = [h.lower() for h in header]

            # Ensure the file has both Agent and Wazuh/Pipeline cumulative metrics
            has_agent = any('agent latency' in h for h in header_lower)
            has_wazuh = any('pipeline latency' in h or 'wazuh latency' in h for h in header_lower)

            if has_agent and has_wazuh:
                found_data = True
                print(f"[+] Found Pipeline Data in: {os.path.basename(filepath)}")

                # Find the exact column indexes
                agent_idx = next(i for i, h in enumerate(header_lower) if 'agent latency' in h)
                wazuh_idx = next(i for i, h in enumerate(header_lower) if 'pipeline latency' in h or 'wazuh latency' in h)

                for row in reader:
                    # Ensure the row has data and Wazuh didn't timeout ("N/A")
                    if len(row) > max(agent_idx, wazuh_idx) and row[wazuh_idx] not in ["", "N/A"]:
                        try:
                            agent_lat = float(row[agent_idx])
                            total_lat = float(row[wazuh_idx])

                            # The true network/SIEM propagation delay
                            propagation_delay = total_lat - agent_lat

                            # Append to our plotting dictionaries
                            plot_data['Wazuh Latency'].append(propagation_delay)
                            plot_data['Total Agent Latency'].append(total_lat)
                        except ValueError:
                            pass

    if not found_data or not plot_data['Total Agent Latency']:
        print("[!] Could not find valid data. Make sure your CSV has 'Agent Latency' and 'Wazuh Latency' columns.")
        return

    # calculate metrics for console output
    count = len(plot_data['Total Agent Latency'])

    prop_data = plot_data['Wazuh Latency']
    prop_mean = statistics.mean(prop_data)
    prop_stdev = statistics.stdev(prop_data) if count > 1 else 0.0
    prop_stderr = (prop_stdev / math.sqrt(count)) if count > 0 else 0.0

    total_data = plot_data['Total Agent Latency']
    total_mean = statistics.mean(total_data)
    total_stdev = statistics.stdev(total_data) if count > 1 else 0.0
    total_stderr = (total_stdev / math.sqrt(count)) if count > 0 else 0.0

    print("\n" + "="*50)
    print("📊 METRICS SUMMARY (PROPAGATION VS TOTAL)")
    print("="*50)
    print(f"Total Runs: {count}")
    print("-" * 50)
    print("Real Wazuh Latency (Propagation Delay):")
    print(f"  Average:   {prop_mean:.2f} ms")
    print(f"  Std Error: ±{prop_stderr:.2f} ms")
    print("-" * 50)
    print("Total Pipeline Latency (Cumulative):")
    print(f"  Average:   {total_mean:.2f} ms")
    print(f"  Std Error: ±{total_stderr:.2f} ms")
    print("="*50 + "\n")

    # generate plot: wazuh vs total
    plt.figure(figsize=(6, 5))
    sns.set_theme(style="whitegrid")

    custom_palette = ["#fc8d62", "#e78ac3"]
    sns.boxplot(data=list(plot_data.values()), palette=custom_palette, width=0.4)
    plt.xticks(ticks=[0, 1], labels=list(plot_data.keys()))
    plt.ylabel("Latency (ms)")

    plt.tight_layout()
    pdf_path = 'data/perf_tests/propagation_vs_total_boxplot.pdf'
    plt.savefig(pdf_path, format='pdf', bbox_inches='tight')
    plt.close()

    print(f"[+] Saved 2-Stage Plot to: {pdf_path}")

if __name__ == '__main__':
    generate_propagation_plot()
