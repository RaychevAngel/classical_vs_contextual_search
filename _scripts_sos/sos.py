from argparse import ArgumentParser
from pathlib import Path
import shutil
import json
from typing import List, Dict
import random
from utils.arithmetic import verify_sos_answer

parser = ArgumentParser()
parser.add_argument("--iter", type=int, required=True)
parser.add_argument("--gpu", type=int, required=True)
parser.add_argument("--port", type=int, required=True)
parser.add_argument("--mode", type=str, required=True, choices=["gen", "eval_train", "eval_dev", "eval_test"])
parser.add_argument("--b", type=int, required=False)
parser.add_argument("--e", type=int, required=False)
parser.add_argument("--attemps", type=int, required=False)


def configure(parsed_args):
    """Set historical CLI paths without parsing arguments during import."""
    global args, sos_port, sos_data_path, sos_questions_path
    args = parsed_args
    sos_port = 8050 + 4*args.gpu + args.port
    sos_data_path = f"data/sos/iteration_{args.iter}/b{args.b}_e{args.e}_a{args.attemps}" if args.mode == "gen" else None
    sos_questions_path = (f"questions/train_{4*args.iter + args.port}.txt" if args.mode == "gen"
                         else f"questions/train_{4*(args.iter-1)}.txt" if args.mode == "eval_train"
                         else "questions/dev.txt" if args.mode == "eval_dev"
                         else "questions/test.txt")

def print_config():
    print(f"Mode: {args.mode}")
    print(f"Checkpoint: {args.iter}")
    print(f"SoS port: {sos_port}")
    if sos_data_path:
        print(f"SoS data path: {sos_data_path}")
    print(f"SoS questions path: {sos_questions_path}")

def evaluate_solution(question: str, result: str) -> bool:
    """Verify the final marked expression using the shared exact checker."""
    return verify_sos_answer(question, result)

def export_data(data: List[Dict]):
    from datasets import Dataset

    p = Path(sos_data_path); p.parent.mkdir(parents=True, exist_ok=True)
    try:
        old = Dataset.load_from_disk(p).to_list()
    except:
        old = []
    for attempt in range(1, 4):
        shutil.rmtree(p, ignore_errors=True)
        Dataset.from_list(old + data).save_to_disk(str(p))
        print(f"[INFO] saved {p} (attempt {attempt})")
        break

def plot_tokens_usage(stats: Dict):
    import numpy as np
    import matplotlib.pyplot as plt

    if not stats["correct_tokens_usage"]:
        print("No correct completions to plot; no token-threshold curve written.")
        return
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    
    # Calculate statistics
    mean = np.mean(stats["correct_tokens_usage"])
    std = np.std(stats["correct_tokens_usage"])
    
    # Combined histogram
    ax1.hist(stats["correct_tokens_usage"], bins=50, alpha=0.5, label=f"Correct (μ={mean:.1f}, σ={std:.1f})", color='green')
    ax1.set_title("Token Usage Distribution")
    ax1.set_xlabel("Number of Tokens")
    ax1.set_ylabel("Frequency")
    ax1.legend()
    
    # Accuracy vs Token Usage plot
    x_values = [i for i in range(min(stats["correct_tokens_usage"]), max(stats["correct_tokens_usage"]) + 1)]
    y_values = [sum(1 for x in stats["correct_tokens_usage"] if x <= t) / (stats["correct"] + stats["incorrect"]) for t in x_values]
    
    ax2.plot(x_values, y_values)
    ax2.set_title("Correct completions within token threshold")
    ax2.set_xlabel("Token Usage Threshold")
    ax2.set_ylabel("Accuracy")
    ax2.grid(True)
    ax2.set_xscale('log')
    
    plt.tight_layout()
    save_path = Path(f"logs/evaluation/sos/iterations_{args.iter}_{args.mode}_gpu{args.gpu}_port{args.port}.png")
    save_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(save_path)
    plt.close()

def main_eval():
    import requests

    print_config()
    with open(sos_questions_path, "r") as f:
        questions = ["Q | " + line.strip() + "\n" for line in f]
    
    random.shuffle(questions)
    
    stats = {"correct": 0, "incorrect": 0, "correct_tokens_usage": [], "incorrect_tokens_usage": []}
    batch_size = 50
    attemps = args.attemps if args.attemps else 5
    
    for j in range(attemps):
        for i in range(0, len(questions), batch_size):
            batch = questions[i:min(i+batch_size, len(questions))]
            sos_results = requests.post(
                url=f"http://127.0.0.1:{sos_port}/sos-prediction",
                json={"questions": batch, "temperature": 1.0},
            ).json()
            
            for question, completion, tokens_used in zip(batch, sos_results['completions'], sos_results['tokens_usage']):
                if evaluate_solution(question, completion):
                    stats["correct"] += 1
                    stats["correct_tokens_usage"].append(tokens_used)
                else:
                    stats["incorrect"] += 1
                    stats["incorrect_tokens_usage"].append(tokens_used)
            
            print(f"Batch {i//batch_size+1} done")
            print(f"Current Accuracy: {stats['correct']/(stats['correct'] + stats['incorrect'])*100:.2f}%")
        print(f"Final Accuracy: {stats['correct']/(stats['correct'] + stats['incorrect'])*100:.2f}%")
        plot_tokens_usage(stats)

def main_gen():
    import requests

    print_config()
    with open(sos_questions_path, "r") as f:
        questions = ["Q | " + line.strip() + "\n" for line in f]
    
    random.shuffle(questions)
    
    stats = {"collected": []}
    batch_size = 50
    attemps = args.attemps if args.attemps else 5

    unsolved_questions = questions.copy()  # Create a copy to avoid modifying original list
    gen_data = []
    
    for j in range(attemps):
        # Process only unsolved questions
        for i in range(0, len(unsolved_questions), batch_size):
            batch = unsolved_questions[i:min(i+batch_size, len(unsolved_questions))]
            sos_results = requests.post(
                url=f"http://127.0.0.1:{sos_port}/sos-prediction",
                json={"questions": batch, "temperature": 1.0},
            ).json()
            
            questions_to_remove = []
            
            for question, completion, tokens_used in zip(batch, sos_results['completions'], sos_results['tokens_usage']):
                if evaluate_solution(question, completion):
                    gen_data.append({
                        "prompt": question,
                        "completion": f"<START_THOUGHT>\nN1->Q | {completion}<END_ANSWER>"
                    })
                    questions_to_remove.append(question)
            
            for question in questions_to_remove:
                unsolved_questions.remove(question)
                
            print(f"Batch {i//batch_size+1} done")
            print(f"SoS examples collected: {len(gen_data)}")
            print(f"Remaining unsolved questions: {len(unsolved_questions)}")

    export_data(gen_data)

if __name__ == "__main__":
    configure(parser.parse_args())
    if args.mode == "gen":
        main_gen()
    elif args.mode == "eval_train":
        main_eval()
    elif args.mode == "eval_dev":
        main_eval()
    elif args.mode == "eval_test":
        main_eval()
