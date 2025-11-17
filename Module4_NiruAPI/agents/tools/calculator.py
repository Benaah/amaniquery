"""
Calculator Tool - Performs mathematical calculations
"""
from typing import Dict, Any, Union
import math
from loguru import logger


class CalculatorTool:
    """Tool for performing mathematical calculations"""
    
    def execute(
        self,
        expression: str,
        precision: int = 10
    ) -> Dict[str, Any]:
        """
        Evaluate a mathematical expression
        
        Args:
            expression: Mathematical expression to evaluate
            precision: Decimal precision for results
            
        Returns:
            Calculation result
        """
        try:
            # Safe evaluation - only allow math operations
            allowed_names = {
                k: v for k, v in math.__dict__.items() if not k.startswith("__")
            }
            allowed_names.update({
                'abs': abs,
                'round': round,
                'min': min,
                'max': max,
                'sum': sum,
                'pow': pow
            })
            
            # Evaluate expression
            result = eval(expression, {"__builtins__": {}}, allowed_names)
            
            # Round to precision
            if isinstance(result, float):
                result = round(result, precision)
            
            return {
                'expression': expression,
                'result': result,
                'success': True
            }
        except Exception as e:
            logger.error(f"Error calculating {expression}: {e}")
            return {
                'expression': expression,
                'result': None,
                'error': str(e),
                'success': False
            }

