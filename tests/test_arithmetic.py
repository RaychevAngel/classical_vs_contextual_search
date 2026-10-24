import unittest

from utils.arithmetic import verify_equation, verify_mcts_answer, verify_sos_answer
from utils.mcts_base import MCTSNode
from _scripts_sos.sos import evaluate_solution


class ArithmeticTests(unittest.TestCase):
    def test_valid_basic_operations_and_reordering(self):
        for expression in ("(1+3)*(2+4)=24", "(4+2)*(3+1)=24."):
            self.assertTrue(verify_equation("Use 1, 2, 3, 4 to make 24.", expression))

    def test_fractional_intermediate_is_exact(self):
        self.assertTrue(verify_equation("Use 3, 3, 8, 8 to make 24.", "8/(3-8/3)=24"))
        self.assertTrue(verify_equation("Use 1, 3, 3 to make 1.", "1/3*3=1"))

    def test_negative_intermediate_and_target(self):
        self.assertTrue(verify_equation("Use 2, 3, 4 to make -4.", "(2-3)*4=-4"))

    def test_repeated_number_multiplicity(self):
        self.assertTrue(verify_equation("Use 2, 2, 3 to make 7.", "2+2+3=7"))
        self.assertFalse(verify_equation("Use 2, 2, 3 to make 7.", "2+3+1+1=7"))

    def test_rejects_old_operator_loopholes(self):
        self.assertFalse(verify_equation("Use 2, 3, 3, 4 to make 7.", "2**3+3-4=7"))
        self.assertFalse(verify_equation("Use 11, 4, 3, 2 to make 7.", "11//4+3+2=7"))

    def test_rejects_other_language_constructs(self):
        for expression in ("1%2=1", "1^2=3", "abs(1)=1", "True+1=2", "1_0=10",
                           "1.0=1", "+1=1", "-1+2=1", "__import__('os')=1"):
            with self.subTest(expression=expression):
                self.assertFalse(verify_equation("Use 1, 2 to make 1.", expression))

    def test_rejects_wrong_targets_and_unused_or_concatenated_numbers(self):
        for expression in ("1+2+3+4=25", "1+2+3=6", "12+3+4=19"):
            self.assertFalse(verify_equation("Use 1, 2, 3, 4 to make 24.", expression))

    def test_rejects_valid_substring_in_malformed_answer(self):
        for expression in ("garbage (1+3)*(2+4)=24", "(1+3)*(2+4)=24 and another answer",
                           "(1+3)*(2+4)=24=25", "(1+3)*(2+4)=24.."):
            self.assertFalse(verify_equation("Use 1, 2, 3, 4 to make 24.", expression))

    def test_zero_division_and_malformed_expression(self):
        self.assertFalse(verify_equation("Use 1, 2, 2 to make 1.", "1/(2-2)=1"))
        self.assertFalse(verify_equation("Use 1, 2 to make 3.", "(1+2=3"))

    def test_near_zero_is_not_exactly_zero(self):
        self.assertFalse(verify_equation("Use 1, 10000000 to make 0.", "1/10000000=0"))

    def test_size_limits(self):
        self.assertFalse(verify_equation("Use 1 to make 1.", "(" * 5000 + "1=1"))
        operands = ", ".join(["1"] * 65)
        self.assertFalse(verify_equation(f"Use {operands} to make 65.", "+".join(["1"] * 65) + "=65"))

    def test_mcts_and_sos_use_the_same_equation_contract(self):
        question = "Use 1, 2, 3, 4 to make 24.\n"
        expression = "(1+3)*(2+4)=24."
        state = "intermediate steps\nThe answer is: " + expression + "\n"
        sos = "search trace\n<END_THOUGHT>\n<START_ANSWER>\n" + expression
        self.assertTrue(verify_mcts_answer(question, state))
        self.assertTrue(verify_sos_answer("Q | " + question, sos))
        self.assertTrue(verify_sos_answer(question, sos + "<END_ANSWER>"))
        self.assertEqual(MCTSNode(state, None, 0, 0, 0).evaluate_terminal_state(question), 1.0)
        self.assertTrue(evaluate_solution("Q | " + question, sos))

    def test_answer_markers_are_required_and_unambiguous(self):
        question = "Use 1, 2, 3, 4 to make 24."
        answer = "(1+3)*(2+4)=24"
        self.assertFalse(verify_mcts_answer(question, answer))
        self.assertFalse(verify_sos_answer(question, answer))
        self.assertFalse(verify_sos_answer(question, "<START_ANSWER>" + answer + "<START_ANSWER>" + answer))
        self.assertFalse(verify_sos_answer(question, "<START_ANSWER>" + answer + "<END_ANSWER>trailing text"))
        self.assertFalse(verify_mcts_answer(question, "The answer is: " + answer + "\nThe answer is: " + answer))


if __name__ == "__main__":
    unittest.main()
