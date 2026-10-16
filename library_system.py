
"""Library loan tracking and fine calculation system."""

import ast
import json
import operator
from datetime import datetime

loans = {}
FINE_PER_DAY = 2

_ALLOWED_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


def add_book_loan(student_id, book_id, dates=None):
    """Record a book loan for a student."""
    if not student_id:
        return

    if not isinstance(book_id, str):
        raise TypeError("Book ID must be a string.")

    if dates is None:
        dates = []

    dates.append(str(datetime.now()))
    loans.setdefault(student_id, []).append(book_id)
    print(
        f"{student_id} borrowed {book_id} "
        f"(loan dates on record: {len(dates)})"
    )


def return_book(student_id, book_id):
    """Remove a returned book from a student's loans."""
    student_loans = loans.get(student_id)

    if student_loans is None or book_id not in student_loans:
        return False

    student_loans.remove(book_id)

    if not student_loans:
        del loans[student_id]

    return True


def calculate_fine(days_overdue):
    """Calculate a fine for nonnegative overdue days."""
    if not isinstance(days_overdue, int) or isinstance(days_overdue, bool):
        raise TypeError("Overdue days must be an integer.")

    if days_overdue < 0:
        raise ValueError("Overdue days cannot be negative.")

    return days_overdue * FINE_PER_DAY


def renew_book(student_id, book_id, extra_days):
    """Renew a book and adjust the daily fine for long renewals."""
    global FINE_PER_DAY

    if extra_days < 0:
        raise ValueError("Extra days cannot be negative.")

    if extra_days > 14:
        FINE_PER_DAY += 1

    print(
        f"Renewed {book_id} for {student_id} "
        f"by {extra_days} days"
    )


def load_records(file="loans.json"):
    """Load loan records from a JSON file."""
    global loans

    with open(file, "r", encoding="utf-8") as record_file:
        records = json.load(record_file)

    if not isinstance(records, dict):
        raise ValueError("Loan records must be a JSON object.")

    if not all(
        isinstance(student, str)
        and isinstance(books, list)
        and all(isinstance(book, str) for book in books)
        for student, books in records.items()
    ):
        raise ValueError("Loan records contain invalid data.")

    loans = records


def save_records(file="loans.json"):
    """Save loan records to a JSON file."""
    with open(file, "w", encoding="utf-8") as record_file:
        json.dump(loans, record_file, indent=2)


def _evaluate_rule_node(node):
    """Evaluate only permitted arithmetic expression nodes."""
    if isinstance(node, ast.Expression):
        return _evaluate_rule_node(node.body)

    if isinstance(node, ast.Constant) and type(node.value) in (int, float):
        return node.value

    if isinstance(node, ast.BinOp) and type(node.op) in _ALLOWED_OPERATORS:
        left = _evaluate_rule_node(node.left)
        right = _evaluate_rule_node(node.right)

        if isinstance(node.op, ast.Pow) and abs(right) > 10:
            raise ValueError("Exponent is too large.")

        return _ALLOWED_OPERATORS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _ALLOWED_OPERATORS:
        return _ALLOWED_OPERATORS[type(node.op)](
            _evaluate_rule_node(node.operand)
        )

    raise ValueError("Rule contains an unsupported expression.")


def fine_from_rule(rule, days):
    """Calculate a fine from a restricted arithmetic rule."""
    if not isinstance(rule, str):
        raise TypeError("Rule must be a string.")

    expression = rule.replace("days", str(days))

    try:
        parsed_expression = ast.parse(expression, mode="eval")
        result = _evaluate_rule_node(parsed_expression)
    except (SyntaxError, TypeError, ZeroDivisionError, OverflowError) as error:
        raise ValueError("Invalid fine rule.") from error

    if not isinstance(result, (int, float)) or not __import__(
        "math"
    ).isfinite(result):
        raise ValueError("Fine rule must produce a finite number.")

    return result


def print_report():
    """Print all currently recorded loans."""
    print("Loan Report")
    for student_id, book_ids in loans.items():
        print(student_id, "->", book_ids)


def main():
    """Run a demonstration of the library loan system."""
    add_book_loan("S101", "B-ALGO")
    add_book_loan("S102", "B-NETW")
    add_book_loan("", "B-DBMS")
    add_book_loan("S103", "B-DBMS")

    return_book("S999", "B-NONE")
    renew_book("S101", "B-ALGO", 21)

    print("Fine for 5 days:", calculate_fine(5))

    try:
        print("Fine for -3 days:", calculate_fine(-3))
    except ValueError as error:
        print("Invalid overdue days:", error)

    print("Fine via rule:", fine_from_rule("days * 2 + 10", 4))

    days_input = input("Days overdue for S102 (press Enter for 0): ") or "0"

    try:
        days = int(days_input)
        print("S102 owes:", calculate_fine(days))
    except (ValueError, TypeError) as error:
        print("Invalid overdue days:", error)

    save_records()
    load_records()
    print_report()


if __name__ == "__main__":
    main()
