"""
Base service class with common functionality
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

class BaseService(ABC):
    """Base service class"""
    
    def __init__(self):
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def log_info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(message, extra=kwargs)
    
    def log_error(self, message: str, error: Exception = None, **kwargs):
        """Log error message"""
        if error:
            self.logger.error(f"{message}: {str(error)}", extra=kwargs)
        else:
            self.logger.error(message, extra=kwargs)
    
    def log_warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(message, extra=kwargs)
    
    def handle_error(self, error: Exception, context: str = "") -> Dict[str, Any]:
        """Handle service errors consistently"""
        error_msg = f"Error in {context}: {str(error)}" if context else str(error)
        self.log_error(error_msg, error)
        
        return {
            "success": False,
            "error": error_msg,
            "error_type": type(error).__name__
        }
    
    def success_response(self, data: Any = None, message: str = "Success") -> Dict[str, Any]:
        """Create success response"""
        response = {
            "success": True,
            "message": message
        }
        if data is not None:
            response["data"] = data
        return response