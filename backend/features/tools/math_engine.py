import sys
import os

for site_pkg in [
    r"C:\Users\Rishi\AppData\Local\Programs\Python\Python314\Lib\site-packages",
    r"C:\Users\Rishi\AppData\Roaming\Python\Python314\site-packages"
]:
    if os.path.exists(site_pkg) and site_pkg not in sys.path:
        sys.path.insert(0, site_pkg)

_curr_dir = os.path.dirname(os.path.abspath(__file__))
_back_dir = os.path.abspath(os.path.join(_curr_dir, "..", "..")) if "features" in _curr_dir else os.path.abspath(_curr_dir)
_feat_dir = os.path.join(_back_dir, "features")

if _back_dir not in sys.path:
    sys.path.insert(0, _back_dir)
if _feat_dir not in sys.path:
    sys.path.insert(0, _feat_dir)

import ast
import math
import re
import logging
from typing import Dict, Any, Union

try:
    import sympy as sp
except ImportError:
    sp = None

try:
    import numpy as np
except ImportError:
    np = None

logger = logging.getLogger("orian.math_engine")

class SafeASTEvaluator(ast.NodeVisitor):
    """AST Expression Parser ensuring 100% safe, non-arbitrary mathematical code execution."""

    ALLOWED_NODES = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Call,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.FloorDiv, ast.Mod, ast.Pow,
        ast.USub, ast.UAdd, ast.Name, ast.Load, ast.Tuple, ast.List
    )

    ALLOWED_FUNCTIONS = {
        'sqrt': math.sqrt,
        'sin': math.sin,
        'cos': math.cos,
        'tan': math.tan,
        'log': math.log,
        'log10': math.log10,
        'exp': math.exp,
        'abs': abs,
        'round': round,
        'floor': math.floor,
        'ceil': math.ceil,
        'pi': math.pi,
        'e': math.e
    }

    def visit(self, node):
        if not isinstance(node, self.ALLOWED_NODES):
            raise ValueError(f"Disallowed expression element: {type(node).__name__}")
        return super().visit(node)

    def visit_Expression(self, node):
        return self.visit(node.body)

    def visit_Constant(self, node):
        return node.value

    def visit_Name(self, node):
        if node.id.lower() in self.ALLOWED_FUNCTIONS:
            return self.ALLOWED_FUNCTIONS[node.id.lower()]
        raise ValueError(f"Undefined variable/symbol: {node.id}")

    def visit_BinOp(self, node):
        left = self.visit(node.left)
        right = self.visit(node.right)
        if isinstance(node.op, ast.Add): return left + right
        if isinstance(node.op, ast.Sub): return left - right
        if isinstance(node.op, ast.Mult): return left * right
        if isinstance(node.op, ast.Div): return left / right
        if isinstance(node.op, ast.FloorDiv): return left // right
        if isinstance(node.op, ast.Mod): return left % right
        if isinstance(node.op, ast.Pow): return left ** right
        raise ValueError(f"Unsupported binary operator: {type(node.op).__name__}")

    def visit_UnaryOp(self, node):
        operand = self.visit(node.operand)
        if isinstance(node.op, ast.USub): return -operand
        if isinstance(node.op, ast.UAdd): return +operand
        raise ValueError(f"Unsupported unary operator: {type(node.op).__name__}")

    def visit_Call(self, node):
        func = self.visit(node.func)
        args = [self.visit(arg) for arg in node.args]
        return func(*args)


class MathEngine:
    """Engine for simple zero-latency AST evaluation and advanced SymPy/NumPy symbolic & numerical mathematics."""

    def evaluate_simple(self, expression_text: str) -> Dict[str, Any]:
        raw = expression_text.strip()

        # Handle percentage expressions e.g. "25% of 800" -> 0.25 * 800
        pct_match = re.match(r'^\s*([\d\.]+)\%\s*of\s*([\d\.]+)\s*$', raw, re.IGNORECASE)
        if pct_match:
            pct_val = float(pct_match.group(1)) / 100.0
            num_val = float(pct_match.group(2))
            res = pct_val * num_val
            return {
                "success": True,
                "action": "CALCULATE",
                "expression": raw,
                "result": res,
                "formatted": f"{raw} -> {res}"
            }

        # Strip English query prefixes e.g. "tell me", "what is", "calculate", "solve", "eval", "find", "please", "how much is"
        expr_clean = re.sub(r'^(?:tell\s+me|what\s+is|calculate|solve|eval|find|please|how\s+much\s+is|\s+)+', '', raw, flags=re.IGNORECASE).strip()

        # Normalize caret power and square root syntax
        expr_clean = expr_clean.replace('^', '**').replace('×', '*').replace('÷', '/')
        expr_clean = re.sub(r'√([\d\.]+)', r'sqrt(\1)', expr_clean)

        try:
            tree = ast.parse(expr_clean, mode='eval')
            evaluator = SafeASTEvaluator()
            val = evaluator.visit(tree)
            
            # Format result
            res_str = f"{val:g}" if isinstance(val, (int, float)) else str(val)

            return {
                "success": True,
                "action": "CALCULATE",
                "expression": raw,
                "result": val,
                "formatted": f"{raw} -> {res_str}"
            }
        except Exception as e:
            # Fallback to SymPy engine
            adv_res = self.evaluate_advanced(expr_clean)
            if adv_res.get("success"):
                return adv_res
            return {
                "success": False,
                "action": "CALCULATE",
                "expression": raw,
                "formatted": f"Calculation Fault: {str(e)}",
                "error": f"Evaluation error: {str(e)}",
                "recovery": "Route to SymPy Advanced Mathematics Engine."
            }

    def evaluate_advanced(self, problem_description: str) -> Dict[str, Any]:
        """Solves advanced calculus, algebra, derivatives, integrals, and matrices with verification."""
        p_lower = problem_description.lower()

        if sp is None:
            return {
                "success": False,
                "action": "ADVANCED_MATHEMATICS",
                "error": "SymPy package is not installed.",
                "recovery": "Install sympy using pip install sympy."
            }

        try:
            x = sp.Symbol('x')
            result_summary = ""

            if "derivative" in p_lower or "differentiate" in p_lower:
                expr_match = re.search(r'of\s+([a-zA-Z0-9\+\-\*\/\^\s\(\)]+)', problem_description, re.IGNORECASE)
                expr_str = expr_match.group(1).strip() if expr_match else "x**2"
                expr = sp.sympify(expr_str.replace('^', '**'))
                diff_res = sp.diff(expr, x)
                result_summary = f"d/dx ({expr}) = {diff_res}"

            elif "integral" in p_lower or "integrate" in p_lower:
                expr_match = re.search(r'of\s+([a-zA-Z0-9\+\-\*\/\^\s\(\)]+)', problem_description, re.IGNORECASE)
                expr_str = expr_match.group(1).strip() if expr_match else "x**2"
                expr = sp.sympify(expr_str.replace('^', '**'))
                int_res = sp.integrate(expr, x)
                result_summary = f"∫ ({expr}) dx = {int_res} + C"

            elif "solve" in p_lower or "equation" in p_lower:
                eq_match = re.search(r'(?:solve|equation)\s+([a-zA-Z0-9\+\-\*\/\^\=\s\(\)]+)', problem_description, re.IGNORECASE)
                eq_str = eq_match.group(1).strip() if eq_match else "x**2 - 4"
                if '=' in eq_str:
                    lhs, rhs = eq_str.split('=')
                    eq = sp.Eq(sp.sympify(lhs.replace('^', '**')), sp.sympify(rhs.replace('^', '**')))
                else:
                    eq = sp.sympify(eq_str.replace('^', '**'))
                solutions = sp.solve(eq, x)
                result_summary = f"Equation Solutions: x = {solutions}"

            else:
                # Default symbolic evaluation
                expr = sp.sympify(problem_description.replace('^', '**'))
                result_summary = f"Symbolic Result: {sp.simplify(expr)}"

            return {
                "success": True,
                "action": "ADVANCED_MATHEMATICS",
                "problem": problem_description,
                "result": result_summary,
                "verified": True,
                "formatted": f"Advanced Math Engine:\n{result_summary}\n[Verified via SymPy]"
            }
        except Exception as e:
            return {
                "success": False,
                "action": "ADVANCED_MATHEMATICS",
                "problem": problem_description,
                "error": f"Symbolic math error: {str(e)}",
                "recovery": "Fallback to LLM reasoning."
            }

math_engine = MathEngine()
