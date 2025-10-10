import seaborn as sns
from tqdm import tqdm
from hmmlearn.hmm import CategoricalHMM
from hmmlearn.base import ConvergenceMonitor
import pandas as pd
import pickle
import numpy as np
from collections import defaultdict
import os
from collections import deque
from time import time_ns, time
import matplotlib.pyplot as plt
from matplotlib.ticker import EngFormatter
from matplotlib.colors import LogNorm
from sklearn.metrics import confusion_matrix, accuracy_score, classification_report

STATS = os.path.join(os.path.abspath(os.curdir), "data/stats")
FIGS = os.path.join(os.path.abspath(os.curdir), "data/figs")
FILES = os.path.join(os.path.abspath(os.curdir), "data/files")
DB = os.path.join(os.path.abspath(os.curdir), "data/logs")

class EarlyStop(ConvergenceMonitor):
    def __init__(self, n_iter=100, tol=1e-2, patience=5, verbose=False):
        super().__init__(n_iter=n_iter, tol=tol, verbose=verbose)
        self.patience = patience
        self._best_log_prob = -np.inf
        self._wait = 0

    @property
    def converged(self):
        if self.iter == self.n_iter: return True
        if len(self.history) < 2: return False
        improvement = self.history[-1] - self.history[-2]
        if improvement < self.tol:
            self._wait += 1
        else:
            self._wait = 0
        if self._wait >= self.patience:
            return True
        return False


class HMM:
    def __init__(self, model_file, n_components=10, n_iter=10):
        self.n_features = 337
        self.model_file = os.path.join(FILES, model_file) + ".pkl"
        self.components = n_components
        self.iter = n_iter
        self.threshold = 0
        self.window_size = None
        self.name = model_file
        self.stide = set()

        if os.path.exists(self.model_file):
            print("Loading Model...")
            with open(self.model_file, 'rb') as f:
                saved_data = pickle.load(f)
            self.model = saved_data['model']
            self.threshold = saved_data['threshold']
            self.window_size = saved_data['window_size']
        else:
            print("Creating Model...")
            self.model = CategoricalHMM(n_components=self.components, n_features=self.n_features, n_iter=self.iter, random_state=42, verbose=True)
            self.model.monitor_ = EarlyStop(self.model.n_iter, 0.1, 5, True)

    def train(self, train_data):
        seq_counter = defaultdict(int)
        train_data = os.path.join(DB, train_data.removesuffix(".csv")) + ".csv"
        train_data = pd.read_csv(train_data, header=None)
        train_data.drop(train_data.columns[-1], axis=1, inplace=True)
        self.window_size = train_data.shape[1]

            # Numpy array (ensure contiguous)
        arr = np.ascontiguousarray(train_data.to_numpy())
        n_rows = arr.shape[0]
        if n_rows == 0:
            # Nothing to do
            return np.empty((0, 1)), self.window_size

        # ---- Count identical sequences efficiently ----
        # Structured view: treat each row as a single item for hashing/unique
        row_dtype = np.dtype([('f'+str(i), arr.dtype) for i in range(arr.shape[1])])
        structured = arr.view(row_dtype).ravel()

        # Unique rows + counts
        uniq_rows, counts = np.unique(structured, return_counts=True)
        freqs = counts / n_rows

        # Identify frequent sequences (> threshold)
        frequent_mask = freqs > 0.1
        frequent_structs = uniq_rows[frequent_mask]

        # Update STIDE set (store as tuples for readability/interoperability)
        # NOTE: `stide` is assumed to be a mutable set-like (e.g., set()).
        if len(frequent_structs):
            # Convert structured back to tuples only for the frequent ones (small)
            frequent_arr = frequent_structs.view(arr.dtype).reshape(-1, arr.shape[1])
            for row in frequent_arr:
                self.stide.add(tuple(row.tolist()))

        # ---- Filter out frequent sequences in one vectorized shot ----
        to_drop_mask = np.isin(structured, frequent_structs, assume_unique=False)
        filtered = arr[~to_drop_mask]
        print(len(filtered))
        X = filtered.reshape(-1, 1)
        lengths = [self.window_size] * len(filtered)
        stime = time()
        self.model.fit(X, lengths=lengths)
        train_time = (time() - stime) // 60
        print(f"Training time: {train_time}min")

        predictions = []
        avg = 0

        for sequence in tqdm(filtered):
            seq = np.array(sequence).reshape(-1,1)
            stime = time_ns()
            prediction = self.model.score(seq, [self.window_size])
            avg += time_ns() - stime
            predictions.append(prediction)

        self.threshold = min(predictions)
        avg_pred_time = (avg / len(train_data)) / 1e6
        print(f"\nAvg prediction time: {(avg_pred_time):.3f}ms")

            


        with open(os.path.join(STATS, f"{self.name}_train.txt"), 'w') as stats:
            stats.write(
                f"Training Time: {train_time} min\n"
                f"Avg Prediction Time: {avg_pred_time}ms\n"
                f"{self.components} States\n"
                f"{self.iter} Iterations\n"
                f"{self.threshold} Threshold\n"
                f"{len(train_data)} Entries\n"
            )

        with open(self.model_file, 'wb') as f:
            pickle.dump({'model': self.model, 'threshold': self.threshold, 'window_size': self.window_size, 'stide': self.stide}, f)

    def test(self, test_data, tolerance=0.6):
        test_data = os.path.join(DB, test_data) + ".csv"
        test_data = pd.read_csv(test_data, header=None)
        flags = test_data.iloc[:, -1].copy()
        test_data.drop(test_data.columns[-1], axis=1, inplace=True)
        Y = test_data.to_numpy()

        predictions = []
        scores = []
        tolerant_predictions = []
        avg = 0
        tolerant_queue = deque([0] * 10, maxlen=10)
        tolerant_flags = deque([0] * 10, maxlen=10)
        tolerant_prediction_flags = []

        for flag, sequence in enumerate(tqdm(Y)):
            tolerant_flags.append(flags[flag])
            if str(sequence.tolist()) in self.stide:
                scores.append(0)
                predictions.append(0)
                tolerant_queue.append(0)
                if sum(tolerant_flags) > (len(tolerant_queue) * tolerance):
                    tolerant_prediction_flags.append(1)
                else:
                    tolerant_prediction_flags.append(0)


                if sum(tolerant_queue) > (len(tolerant_queue) * tolerance):
                    tolerant_predictions.append(1)
                else:
                    tolerant_predictions.append(0)
                continue

            seq = np.array(sequence).reshape(-1,1)
            stime = time_ns()
            score = self.model.score(seq, [self.window_size])
            avg += time_ns() - stime
            # tolerant_flags.append(flags[flag])

            if np.isneginf(score):
                scores.append(self.threshold - 100)
            else:
                scores.append(score)
            
            if score < self.threshold or np.isneginf(score):
                predictions.append(1)
                tolerant_queue.append(1)
            else:
                predictions.append(0)
                tolerant_queue.append(0)

            if sum(tolerant_flags) > (len(tolerant_queue) * tolerance):
                tolerant_prediction_flags.append(1)
            else:
                tolerant_prediction_flags.append(0)


            if sum(tolerant_queue) > (len(tolerant_queue) * tolerance):
                tolerant_predictions.append(1)
            else:
                tolerant_predictions.append(0)

        plt.figure(figsize=(14, 8))
        plt.rcParams.update({'font.size': 23})
        colors = ['red' if flag == 1 else 'green' for flag in flags]
        plt.scatter(range(len(scores)), scores, c=colors, s=100)
        plt.axhline(y=self.threshold, color='blue', linestyle='dashed', label="Threshold")
        plt.xlabel("Sequence Index")
        plt.ylabel("Log-Likelihood Score")
        ax = plt.gca()
        ax.xaxis.set_major_formatter(EngFormatter())
        ax.margins(x=0, y=0)
        plt.savefig(
            os.path.join(FIGS, f"{self.name}_log_likelihood.pdf"),
            bbox_inches="tight",
            pad_inches=0)

        avg_pred_time = (avg / len(Y)) / 1e6

        print(f"\nAvg prediction time: {(avg_pred_time):.3f}ms")

        print("\nConfusion Matrix:")
        cm = confusion_matrix(flags, predictions)
        print(cm)

        print("\nTolerant Confusion Matrix:")
        tcm = confusion_matrix(tolerant_prediction_flags, tolerant_predictions)
        print(tcm)

        tn, fp, fn, tp = cm.ravel()
        mcc = (tp*tn - fp*fn)/((tp+fp)*(tp+fn)*(tn+fp)*(tn+fn))**0.5
        print(f"\nMatthews Correlation Coefficient (MCC): {mcc}")

        ttn, tfp, tfn, ttp = tcm.ravel()
        tmcc = (ttp*tn - tfp*tfn)/((ttp+tfp)*(ttp+tfn)*(ttn+tfp)*(ttn+tfn))**0.5
        print(f"\nTolerant Matthews Correlation Coefficient (MCC): {tmcc}")

        plt.figure(figsize=(14, 8))
        plt.rcParams.update({'font.size': 23})
        # Avoid log(0) by replacing zeros with small epsilon
        tcm_for_display = np.copy(tcm).astype(float)
        tcm_for_display[tcm_for_display == 0] = 0.5

        vmin = tcm_for_display.min()
        vmax = tcm_for_display.max()

        # Avoid vmin == vmax (would crash LogNorm)
        if vmin >= vmax:
            vmax = vmin + 1

        ax = sns.heatmap(tcm, annot=True, fmt='d',
                    cmap='YlGnBu',
                    norm=LogNorm(vmin=vmin, vmax=vmax),
                    cbar=True,
                    xticklabels=['Normal', 'Anomalous'],
                    yticklabels=['Normal', 'Anomalous'])

        # Axis labels and title
        plt.xlabel('Predicted')
        plt.ylabel('Actual')

        for text in ax.texts:
            value = int(text.get_text())
            # If cell is light (small value), use black text; else white
            if value == 0:
                text.set_color('black')

        # Table-like styling
        plt.xticks(rotation=0)
        plt.yticks(rotation=0)
        plt.tight_layout()
        ax.margins(x=0, y=0)
        plt.savefig(
            os.path.join(FIGS, f"{self.name}_cm.pdf"),
            bbox_inches="tight",
            pad_inches=0)

        print("\nClassification Report:")
        print(classification_report(flags, predictions))

        print(f"\nAccuracy: {accuracy_score(flags, predictions):.2f}")

        with open(os.path.join(STATS, f"{self.name}_test.txt"), 'w') as stats:
            stats.write(
                f"Avg Prediction Time: {avg_pred_time}ms\n"
                f"{len(test_data)} Entries\n"
                "\tNon Tolerant\n"
                f"TN = {tn}\tFP = {fp}\tFN = {fn}\tTP = {tp}\n"
                f"MCC = {mcc}\n"
                "\tTolerant\n"
                f"TN = {ttn}\tFP = {tfp}\tFN = {tfn}\tTP = {ttp}\n"
                f"MCC = {tmcc}\n"
            )