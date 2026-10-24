"""Exact, non-executing verifier shared by MCTS and Stream of Search.

Grammar: non-negative decimal integer literals, parentheses, and the binary
operators +, -, *, /. Every supplied number must occur exactly once. Fractions
and negative intermediate values are allowed; unary operators are not.
"""

import ast
from collections import Counter
from fractions import Fraction
import re


MAX_EXPRESSION_LENGTH = 4096
MAX_OPERANDS = 64
MAX_LITERAL_DIGITS = 50
QUESTION = re.compile(
    r"(?:Q\s*\|\s*)?Use\s+([0-9]+(?:\s*,\s*[0-9]+)*)"
    r"\s+to\s+make\s+(-?[0-9]+)\.?\s*"
)
EQUATION = re.compile(r"([0-9\s()+*/-]+)\s*=\s*(-?[0-9]+)\.?\s*")


def _evaluate(node: ast.AST, numbers: list[int], depth: int = 0) -> Fraction:
    if depth > MAX_OPERANDS:
        raise ValueError("Expression is too deeply nested")
    if isinstance(node, ast.Constant) and type(node.value) is int:
        if node.value < 0 or len(str(node.value)) > MAX_LITERAL_DIGITS:
            raise ValueError("Invalid integer literal")
        numbers.append(node.value)
        if len(numbers) > MAX_OPERANDS:
            raise ValueError("Too many operands")
        return Fraction(node.value)
    if isinstance(node, ast.BinOp) and type(node.op) in (ast.Add, ast.Sub, ast.Mult, ast.Div):
        left = _evaluate(node.left, numbers, depth + 1)
        right = _evaluate(node.right, numbers, depth + 1)
        if isinstance(node.op, ast.Add):
            return left + right
        if isinstance(node.op, ast.Sub):
            return left - right
        if isinstance(node.op, ast.Mult):
            return left * right
        return left / right
    raise ValueError("Only integer literals and binary +, -, *, / are permitted")


def verify_equation(question: str, equation: str) -> bool:
    """Check a complete equation, never a valid-looking substring of one."""
    if not isinstance(question, str) or not isinstance(equation, str):
        return False
    if len(question) > MAX_EXPRESSION_LENGTH or len(equation) > MAX_EXPRESSION_LENGTH:
        return False
    problem = QUESTION.fullmatch(question.strip())
    answer = EQUATION.fullmatch(equation.strip())
    if problem is None or answer is None:
        return False
    literals = re.findall(r"[0-9]+", problem.group(1))
    if len(literals) > MAX_OPERANDS or any(len(n) > MAX_LITERAL_DIGITS for n in literals):
        return False
    if len(problem.group(2).lstrip("-")) > MAX_LITERAL_DIGITS:
        return False
    if len(answer.group(2).lstrip("-")) > MAX_LITERAL_DIGITS:
        return False
    try:
        target = int(problem.group(2))
        if int(answer.group(2)) != target:
            return False
        expression = ast.parse(answer.group(1).strip(), mode="eval")
        used: list[int] = []
        value = _evaluate(expression.body, used)
        return Counter(used) == Counter(map(int, literals)) and value == target
    except (SyntaxError, ValueError, ZeroDivisionError, RecursionError, OverflowError):
        return False


def verify_mcts_answer(question: str, state: str) -> bool:
    """Read the single marked final-answer line of an MCTS trajectory."""
    answers = [line.strip() for line in state.splitlines() if "The answer is:" in line]
    if len(answers) != 1 or not answers[0].startswith("The answer is:"):
        return False
    return verify_equation(question, answers[0][len("The answer is:"):].strip())


def verify_sos_answer(question: str, completion: str) -> bool:
    """Require an answer marker; vLLM may omit its terminating stop token."""
    if completion.count("<START_ANSWER>") != 1:
        return False
    answer = completion.partition("<START_ANSWER>")[2]
    if "<END_ANSWER>" in answer:
        answer, _, suffix = answer.partition("<END_ANSWER>")
        if suffix.strip():
            return False
    return verify_equation(question, answer.strip())
