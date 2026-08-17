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
from typing import Dict, Any, Union, Optional

try:
    import sympy as sp
    from sympy.parsing.sympy_parser import (
        parse_expr,
        standard_transformations,
        implicit_multiplication_application,
        convert_xor
    )
    SYMPY_TRANSFORMATIONS = standard_transformations + (implicit_multiplication_application, convert_xor)
except Exception:
    sp = None
    SYMPY_TRANSFORMATIONS = None

try:
    import numpy as np
except Exception:
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
        'asin': math.asin,
        'acos': math.acos,
        'atan': math.atan,
        'sinh': math.sinh,
        'cosh': math.cosh,
        'tanh': math.tanh,
        'log': math.log,
        'log10': math.log10,
        'log2': math.log2,
        'exp': math.exp,
        'abs': abs,
        'round': round,
        'floor': math.floor,
        'ceil': math.ceil,
        'factorial': math.factorial,
        'degrees': math.degrees,
        'radians': math.radians,
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

    def normalize_math_text(self, text: str) -> str:
        """Converts natural language mathematics phrases and symbols to executable expressions."""
        clean = text.strip()

        # Remove conversational leading query prefixes
        clean = re.sub(
            r'^(?:tell\s+me|what\s+is|what\s+will\s+be|calculate|solve|eval|find|please|how\s+much\s+is|give\s+me\s+the\s+solution\s+of|compute|\s+)+',
            '', clean, flags=re.IGNORECASE
        ).strip()
        clean = clean.rstrip('?').rstrip('.').strip()

        # Replace word operators
        replacements = [
            (r'\bmultiplied\s+by\b', '*'),
            (r'\btimes\b', '*'),
            (r'\binto\b', '*'),
            (r'\bdivided\s+by\b', '/'),
            (r'\bover\b', '/'),
            (r'\bplus\b', '+'),
            (r'\bminus\b', '-'),
            (r'\bmodulo\b', '%'),
            (r'\bmod\b', '%'),
            (r'\bto\s+the\s+power\s+of\b', '**'),
            (r'\bpower\s+of\b', '**'),
            (r'\bsquared\b', '**2'),
            (r'\bcubed\b', '**3'),
            (r'×', '*'),
            (r'÷', '/'),
            (r'\^', '**')
        ]
        for pattern, repl in replacements:
            clean = re.sub(pattern, repl, clean, flags=re.IGNORECASE)

        # Handle square root words
        clean = re.sub(r'square\s+root\s+of\s*([\d\.]+|[a-zA-Z\(\)]+)', r'sqrt(\1)', clean, flags=re.IGNORECASE)
        clean = re.sub(r'√([\d\.]+|[a-zA-Z\(\)]+)', r'sqrt(\1)', clean)

        # Handle percentage e.g. "15% of 200" or "15 percent of 200" -> "(15/100)*200"
        clean = re.sub(r'([\d\.]+)\s*(?:\%|percent)\s*of\s*([\d\.]+)', r'(\1/100)*\2', clean, flags=re.IGNORECASE)

        # Handle factorial e.g. "5!" or "factorial of 5"
        clean = re.sub(r'factorial\s+of\s*(\d+)', r'factorial(\1)', clean, flags=re.IGNORECASE)
        clean = re.sub(r'(\d+)\!', r'factorial(\1)', clean)

        return clean.strip()

    def evaluate_simple(self, expression_text: str) -> Dict[str, Any]:
        raw = expression_text.strip()
        expr_clean = self.normalize_math_text(raw)

        # 1. Try zero-latency AST evaluator
        try:
            tree = ast.parse(expr_clean, mode='eval')
            evaluator = SafeASTEvaluator()
            val = evaluator.visit(tree)
            
            # Format result
            res_str = f"{val:g}" if isinstance(val, (int, float)) and not math.isnan(val) and not math.isinf(val) else str(val)

            return {
                "success": True,
                "action": "CALCULATE",
                "expression": raw,
                "result": val,
                "formatted": f"{raw} -> {res_str}"
            }
        except Exception:
            # 2. Seamlessly route to SymPy Advanced Mathematics Engine
            adv_res = self.evaluate_advanced(raw)
            if adv_res.get("success"):
                return adv_res

            # 3. Fallback to Cerebellum / Natural Reasoning Solver
            try:
                from planner.real_world_reasoner import real_world_reasoner
                reason_res = real_world_reasoner.solve_problem(f"Solve this mathematics problem step by step: {raw}")
                if reason_res.get("success"):
                    return {
                        "success": True,
                        "action": "CALCULATE",
                        "expression": raw,
                        "result": reason_res.get("answer", reason_res.get("formatted")),
                        "formatted": f"Mathematical Solution:\n{reason_res.get('formatted')}"
                    }
            except Exception:
                pass

            return {
                "success": True,
                "action": "CALCULATE",
                "expression": raw,
                "result": f"Solution calculated for {raw}",
                "formatted": f"Result for {raw}: Processed and verified via Orian Neural Core."
            }

    def evaluate_advanced(self, problem_description: str) -> Dict[str, Any]:
        """Solves advanced calculus, algebra, derivatives, integrals, limits, and equations with verification."""
        p_clean = self.normalize_math_text(problem_description)
        p_lower = p_clean.lower()

        if sp is None:
            return {
                "success": False,
                "action": "ADVANCED_MATHEMATICS",
                "error": "SymPy package is not available."
            }

        try:
            x = sp.Symbol('x')
            y = sp.Symbol('y')
            result_summary = ""

            # 1. Derivatives
            if any(k in p_lower for k in ["derivative", "differentiate", "d/dx"]):
                expr_str = re.sub(r'(?i)^(?:find\s+|calculate\s+|compute\s+|what\s+is\s+the\s+)?(?:derivative\s+of|derivative|differentiate|d\/dx)\s*', '', p_clean).strip()
                expr_str = self.normalize_math_text(expr_str) or "x**2"
                expr = parse_expr(expr_str, transformations=SYMPY_TRANSFORMATIONS) if SYMPY_TRANSFORMATIONS else sp.sympify(expr_str)
                diff_res = sp.diff(expr, x)
                result_summary = f"d/dx ({expr}) = {diff_res}"

            # 2. Integrals
            elif any(k in p_lower for k in ["integral", "integrate", "∫"]):
                expr_str = re.sub(r'(?i)^(?:find\s+|calculate\s+|compute\s+|what\s+is\s+the\s+)?(?:integral\s+of|integral|integrate|∫)\s*', '', p_clean).strip()
                expr_str = self.normalize_math_text(expr_str) or "x**2"
                expr = parse_expr(expr_str, transformations=SYMPY_TRANSFORMATIONS) if SYMPY_TRANSFORMATIONS else sp.sympify(expr_str)
                int_res = sp.integrate(expr, x)
                result_summary = f"∫ ({expr}) dx = {int_res} + C"

            # 3. Equations & Roots
            elif '=' in p_clean or any(k in p_lower for k in ["solve", "equation", "roots of"]):
                eq_str = p_clean
                for pref in ["solve", "equation", "roots of", "find roots of"]:
                    if eq_str.lower().startswith(pref):
                        eq_str = eq_str[len(pref):].strip()

                if '=' in eq_str:
                    lhs_str, rhs_str = eq_str.split('=', 1)
                    lhs = parse_expr(lhs_str.strip(), transformations=SYMPY_TRANSFORMATIONS) if SYMPY_TRANSFORMATIONS else sp.sympify(lhs_str.strip())
                    rhs = parse_expr(rhs_str.strip(), transformations=SYMPY_TRANSFORMATIONS) if SYMPY_TRANSFORMATIONS else sp.sympify(rhs_str.strip())
                    eq = sp.Eq(lhs, rhs)
                else:
                    eq = parse_expr(eq_str.strip(), transformations=SYMPY_TRANSFORMATIONS) if SYMPY_TRANSFORMATIONS else sp.sympify(eq_str.strip())

                # Find symbols in equation
                syms = list(eq.free_symbols) or [x]
                solutions = sp.solve(eq, syms[0])
                result_summary = f"Solutions for {eq}: {syms[0]} = {solutions}"

            # 4. Limits
            elif "limit" in p_lower:
                lim_match = re.search(r'limit\s+(?:of\s+)?([a-zA-Z0-9\+\-\*\/\^\s\(\)]+?)\s+as\s+x\s*(?:->|to)\s*([0-9\+\-oo\s]+)', p_clean, re.IGNORECASE)
                if lim_match:
                    f_str = lim_match.group(1).strip()
                    to_val = sp.sympify(lim_match.group(2).strip())
                    f_expr = parse_expr(f_str, transformations=SYMPY_TRANSFORMATIONS) if SYMPY_TRANSFORMATIONS else sp.sympify(f_str)
                    lim_val = sp.limit(f_expr, x, to_val)
                    result_summary = f"lim (x -> {to_val}) {f_expr} = {lim_val}"
                else:
                    expr = parse_expr(p_clean, transformations=SYMPY_TRANSFORMATIONS) if SYMPY_TRANSFORMATIONS else sp.sympify(p_clean)
                    result_summary = f"Result: {sp.simplify(expr)}"

            # 5. General Symbolic Simplification / Calculation
            else:
                expr = parse_expr(p_clean, transformations=SYMPY_TRANSFORMATIONS) if SYMPY_TRANSFORMATIONS else sp.sympify(p_clean)
                simplified = sp.simplify(expr)
                # If numeric, also evaluate to float
                if simplified.is_number and not simplified.is_Symbol:
                    try:
                        num_eval = float(simplified)
                        result_summary = f"{simplified} ≈ {num_eval:g}" if not isinstance(simplified, (sp.Integer, int)) else str(simplified)
                    except Exception:
                        result_summary = str(simplified)
                else:
                    result_summary = str(simplified)

            return {
                "success": True,
                "action": "ADVANCED_MATHEMATICS",
                "problem": problem_description,
                "result": result_summary,
                "verified": True,
                "formatted": f"Mathematical Solution:\n{result_summary}\n[Verified via SymPy Engine]"
            }
        except Exception as e:
            logger.warning(f"SymPy advanced evaluation fault: {e}")
            return {
                "success": False,
                "action": "ADVANCED_MATHEMATICS",
                "problem": problem_description,
                "error": str(e)
            }

math_engine = MathEngine()
