import ast
import operator
import re
from typing import Dict, Any, List, Optional
from app.core.logging import logger

SAFE_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}


class SafeASTCalculator:
    """Safe mathematical evaluator using Python AST restricted exclusively to basic arithmetic."""

    @classmethod
    def evaluate(cls, expression_str: str) -> float:
        clean_expr = expression_str.replace(",", "").replace("%", "").strip()
        # Parse expression safely
        node = ast.parse(clean_expr, mode="eval")
        return cls._eval_node(node.body)

    @classmethod
    def _eval_node(cls, node: ast.AST) -> float:
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        elif isinstance(node, ast.BinOp):
            left = cls._eval_node(node.left)
            right = cls._eval_node(node.right)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                if op_type == ast.Div and right == 0:
                    raise ZeroDivisionError("Division by zero in formula verification")
                return float(SAFE_OPERATORS[op_type](left, right))
            raise ValueError(f"Unsupported binary operator in AST: {op_type}")
        elif isinstance(node, ast.UnaryOp):
            operand = cls._eval_node(node.operand)
            op_type = type(node.op)
            if op_type in SAFE_OPERATORS:
                return float(SAFE_OPERATORS[op_type](operand))
            raise ValueError(f"Unsupported unary operator in AST: {op_type}")
        else:
            raise ValueError(f"Forbidden AST node in mathematical evaluation: {type(node)}")


class NumericalVerifier:
    """Verifies numerical claims against raw table data extracted during ingestion."""

    def __init__(self):
        self.calculator = SafeASTCalculator()

    def verify_claim(
        self,
        claim_description: str,
        claimed_value: float,
        formula_expr: str,
        table_context: Optional[str] = None,
        tolerance: float = 0.01,
    ) -> Dict[str, Any]:
        """
        Deterministically evaluates formula_expr via AST and compares it to claimed_value.
        """
        try:
            computed_value = self.calculator.evaluate(formula_expr)
            diff = abs(computed_value - claimed_value)
            
            # Check relative or absolute tolerance (supports signed changes and magnitude drops like "decreased by 8%")
            is_verified = (diff <= tolerance) or (
                claimed_value != 0 and (diff / abs(claimed_value)) <= tolerance
            )
            if not is_verified:
                abs_diff = abs(abs(computed_value) - abs(claimed_value))
                if (abs_diff <= tolerance) or (claimed_value != 0 and (abs_diff / abs(claimed_value)) <= tolerance):
                    is_verified = True
                    diff = abs_diff

            result = {
                "claim": claim_description,
                "formula": formula_expr,
                "claimed_value": claimed_value,
                "calculated_value": round(computed_value, 4),
                "is_verified": is_verified,
                "badge": "Verified Calculation" if is_verified else "Calculation Discrepancy",
                "badge_variant": "success" if is_verified else "warning",
                "evidence": table_context[:300] if table_context else None,
                "error": None,
            }
            if not is_verified:
                result["details"] = (
                    f"Computed value {computed_value:.2f} differs from claimed {claimed_value:.2f}."
                )
            return result

        except Exception as e:
            logger.warning(f"AST verification error on formula '{formula_expr}': {e}")
            return {
                "claim": claim_description,
                "formula": formula_expr,
                "claimed_value": claimed_value,
                "calculated_value": None,
                "is_verified": False,
                "badge": "Verification Failed",
                "badge_variant": "destructive",
                "error": str(e),
            }

    def scan_and_verify_response(
        self,
        answer_text: str,
        context_chunks: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Detects numerical growth/margin/ratio statements in the generated answer,
        matches them against tabular numbers in context chunks, and executes AST verification.
        """
        verifications = []

        # Find tables in context chunks
        available_tables = []
        for c in context_chunks:
            for t in c.get("tables_extracted", []):
                available_tables.append(t)

        # Normalize markdown bold/italic asterisks for robust numerical parsing
        clean_text = answer_text.replace("**", "").replace("*", "")

        # Regex pattern for percentage growth/change/margin claim: e.g. "grew by 15.5%", "growth rate of 15.0%", "margin of 25%"
        patterns = [
            r"(\b[A-Za-z\s]+?\b)\s+(?:grew|increased|rose|decreased|fell|changed)\s+by\s+([+-]?\d+(?:\.\d+)?)\s*%",
            r"(\b[A-Za-z\s]+?\b)\s+(?:growth rate|margin|growth|rate)\s+(?:of\s+)?([+-]?\d+(?:\.\d+)?)\s*%",
        ]

        matches = []
        for pat in patterns:
            for match in re.finditer(pat, clean_text, re.IGNORECASE):
                matches.append((match.group(1).strip(), float(match.group(2))))

        for subject, pct_val in matches:
            
            # Search tables for matching subject and two sequential numerical values
            formula_found = None
            evidence_md = None

            for t in available_tables:
                raw_rows = t.get("raw_rows", [])
                for row in raw_rows:
                    row_str = " ".join(row).lower()
                    if any(term in row_str for term in subject.lower().split() if len(term) > 3):
                        # Extract row numbers robustly across currency, comma, and scale suffixes ($100M, 50k, 25.0%)
                        numbers = []
                        for cell in row[1:]:
                            for num_match in re.findall(r"[-+]?\d+(?:,\d{3})*(?:\.\d+)?", cell):
                                try:
                                    numbers.append(float(num_match.replace(",", "")))
                                except ValueError:
                                    pass
                        if len(numbers) >= 2:
                            val_old, val_new = numbers[-2], numbers[-1]
                            if val_old != 0:
                                formula = f"(({val_new} - {val_old}) / {val_old}) * 100"
                                formula_found = formula
                                evidence_md = t.get("markdown")
                                break
                if formula_found:
                    break

            if formula_found:
                ver_res = self.verify_claim(
                    claim_description=f"{subject} change of {pct_val}%",
                    claimed_value=pct_val,
                    formula_expr=formula_found,
                    table_context=evidence_md,
                )
                verifications.append(ver_res)

        return verifications


verifier = NumericalVerifier()
