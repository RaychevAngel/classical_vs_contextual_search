import asyncio
import tempfile
from pathlib import Path
import unittest

from evaluate.mcts_evaluator import MCTSForest_Evaluate, MCTSTree_Evaluate, RunMCTS_Evaluate
from utils.mcts_base import MCTSNode


class SearchContractTests(unittest.TestCase):
    def test_mocked_forest_records_each_question_once_per_budget(self):
        completions = {
            "Use 1, 2 to make 3.\n": "The answer is: 1+2=3.\n",
            "Use 2, 3 to make 5.\n": "The answer is: 2+3=5.\n",
            "Use 3, 4 to make 7.\n": "The answer is: 3-4=7.\n",
        }
        calls = []

        def fixed_policy_value(batch):
            calls.extend(question for question, state in batch)
            return [[(completions[question], 0.9)] for question, state in batch]

        budgets = [1, 2, 5]
        forest = MCTSForest_Evaluate(list(completions), budgets, 0.3, fixed_policy_value, 2)
        self.assertEqual(asyncio.run(forest.run_forest()), {budget: 2 / 3 for budget in budgets})
        for budget in budgets:
            self.assertEqual(len(forest.results[budget]), 3)
            self.assertEqual(sorted(forest.results[budget]), [0, 1, 1])
        self.assertCountEqual(calls, completions)
        self.assertEqual(forest.ended_questions_count, 3)

    def test_mocked_forest_batches_without_models_or_network(self):
        calls = []

        def fixed_policy_value(batch):
            calls.append(batch)
            return [[("The answer is: 1+2=3.\n", 0.9)] for _ in batch]

        forest = MCTSForest_Evaluate(["Use 1, 2 to make 3.\n"] * 2,
                                     [1], 0.3, fixed_policy_value, 2)
        self.assertEqual(asyncio.run(forest.run_forest()), {1: 1.0})
        self.assertEqual(forest.results, {1: [1, 1]})
        self.assertEqual(sum(len(batch) for batch in calls), 2)

    def test_favourite_child_preserves_historical_max_q_rule(self):
        parent = MCTSNode("", None, 0, 0, 0)
        high_visits = MCTSNode("visits", parent, 100, 0.2, 0.2)
        high_q = MCTSNode("q", parent, 1, 0.8, 0.8)
        parent.children = [high_visits, high_q]
        self.assertIs(parent.favourite_child, high_q)

    def test_evaluation_search_uses_learned_terminal_value(self):
        tree = MCTSTree_Evaluate("Use 1, 2 to make 3.", [1], 0.3, asyncio.Queue())
        wrong = MCTSNode("The answer is: 1-2=3.", tree.root, 1, 0.9, 0.9)
        correct = MCTSNode("The answer is: 1+2=3.", tree.root, 1, 0.1, 0.1)
        tree.root.children = [wrong, correct]
        self.assertEqual(tree._handle_terminal_node(wrong), 0.9)
        self.assertEqual(tree._get_search_result(), 0)

    def test_export_summary_preserves_actual_budgets_and_denominators(self):
        with tempfile.TemporaryDirectory() as directory:
            question_file = Path(directory) / "questions.txt"
            question_file.write_text("Use 1, 2 to make 3.\n" * 3)
            config = {"questions_path": str(question_file), "max_expansions": [1, 5],
                      "c_explore": 0.3, "batch_size": 1, "export_data_path": directory}
            run = RunMCTS_Evaluate(config, lambda requests: [])
            run.forest.results = {1: [0, 1], 5: [1, 1]}
            result = run.evaluation_summary({1: 0.5, 5: 1.0})
            self.assertNotIn("accuracy", result)
            self.assertEqual(result["accuracy_by_expansions"], {1: 0.5, 5: 1.0})
            self.assertEqual(result["results_by_expansions"][1], {
                "correct": 1, "completed": 2, "requested": 3, "uncompleted": 1})

    def test_empty_outcomes_are_unavailable_not_zero_accuracy(self):
        forest = MCTSForest_Evaluate([], [1], 0.3, lambda requests: [], 1)
        self.assertEqual(asyncio.run(forest.run_forest()), {1: None})

    def test_backpropagation_keeps_per_step_terminal_labels(self):
        tree = MCTSTree_Evaluate("Use 1, 2 to make 3.", [1], 0.3, asyncio.Queue())
        leaf = MCTSNode("The answer is: 1+2=3.", tree.root, 0, 0.2, 0.2)
        tree.backpropagate(leaf, 1.0, True)
        self.assertEqual(leaf.labels, [1.0])
        self.assertEqual(tree.root.labels, [1.0])
        self.assertEqual(leaf.action_value, 1.0)


if __name__ == "__main__":
    unittest.main()
