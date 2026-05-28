import matplotlib.pyplot as plt
import seaborn as sns
import csv, glob, os

def generate_custom_latex_plots():
    # find all performance tests CSVs
    csv_files = glob.glob('data/perf_tests/*.csv')

    if not csv_files:
        print('[!] No performance tests CSVs found in data/perf_tests/')
        return

    # dictionaries to hold our grouped data
    comparison_data = {
        'Legacy Latency': [],
        'ML Latency': [],
        'Agent Latency': []
    }

    wazuh_data = {
        'Wazuh Latency': []
    }

    print("[*] Extracting data across all CSVs...")

    for filepath in csv_files:
        filename = os.path.basename(filepath).lower()

        with open(filepath, mode='r') as file:
            reader = csv.reader(file)
            header = next(reader, None)

            if not header:
                continue

            rows = list(reader)
            for i, col_name in enumerate(header):
                col_clean = col_name.strip()

                # extract the valid float values for this specific column
                col_values = []
                for row in rows:
                    if i < len(row) and row[i] not in ["", "N/A"]:
                        try:
                            col_values.append(float(row[i]))
                        except ValueError:
                            pass

                # route the data to the correct plot bucket based on column name (and filename for legacy)
                if "ML Latency" in col_clean:
                    comparison_data['ML Latency'].extend(col_values)
                elif "Agent Latency" in col_clean:
                    comparison_data['Agent Latency'].extend(col_values)
                elif "Wazuh Latency" in col_clean:
                    wazuh_data['Wazuh Latency'].extend(col_values)
                elif col_clean == "Latency (ms)" and "legacy" in filename:
                    # explicitly require "legacy" in the filename so that we don't accidentally grab the ebpf attach latency column
                    comparison_data['Legacy Latency'].extend(col_values)

    # GENERATE PLOT 1: the mttd comparison
    valid_comparison_data = {k: v for k, v in comparison_data.items() if v}

    if valid_comparison_data:
        plt.figure(figsize=(8, 5))
        sns.set_theme(style="whitegrid")

        # plot the 3 metrics side-by-side
        sns.boxplot(data=list(valid_comparison_data.values()), palette="Set2", width=0.5)

        plt.xticks(ticks=range(len(valid_comparison_data)), labels=list(valid_comparison_data.keys()))
        plt.ylabel("Latency (ms)", fontweight='bold')

        plt.tight_layout()
        plt.savefig('data/perf_tests/mttd_comparison_boxplot.pdf', format='pdf', bbox_inches='tight')
        plt.close()
        print("[+] Saved Comparison Plot to: data/perf_tests/mttd_comparison_boxplot.pdf")

    # GENERATE PLOT 2: wazuh only
    if wazuh_data['Wazuh Latency']:
        plt.figure(figsize=(4, 5)) 
        sns.set_theme(style="whitegrid")

        sns.boxplot(data=list(wazuh_data.values()), palette="muted", width=0.4)

        plt.xticks(ticks=[0], labels=['Wazuh SIEM Latency'])
        plt.ylabel("Latency (ms)", fontweight='bold')

        plt.tight_layout()
        plt.savefig('data/perf_tests/wazuh_only_boxplot.pdf', format='pdf', bbox_inches='tight')
        plt.close()
        print("[+] Saved Wazuh Plot to:      data/perf_tests/wazuh_only_boxplot.pdf")

if __name__ == '__main__':
    generate_custom_latex_plots()
