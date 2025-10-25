import re
from typing import Dict, Any
# from src.config import logger

def parse_report(report_text: str) -> Dict[str, Any]:
    """
    Parses a formatted Markdown report string into a structured dictionary.

    Args:
        report_text: The string containing the final summary report.

    Returns:
        A dictionary with keys for each section of the report.
    """
    if not report_text or not report_text.strip():
        return {}

    parsed_data = {}
    
    # Use regex to split the text by the section headers
    parts = re.split(r'###\s*(.+)', report_text)
    
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        content = parts[i+1].strip()
        
        key = header.lower().replace(" ", "_")
        
        if header in ["Technical Insights", "Developer Perspective"]:
            
            # We split on NEWLINES that are followed by a bullet (* or -).
            # This correctly keeps nested bullets (like '- detail 1')
            # as part of their parent bullet point.
            lines = re.split(r'\n\s*[\*\-]\s+', content)
            
            bullets = []
            for idx, line in enumerate(lines):
                line = line.strip()
                if not line:
                    continue
                
                # The first item in 'lines' might still have its leading
                # bullet. We must strip it.
                if idx == 0:
                    line = re.sub(r'^[\*\-]\s+', '', line) # Remove leading bullet
                
                # Re-join lines that were part of the same bullet
                line = re.sub(r'\n\s+', ' ', line)
                bullets.append(line.strip())
                
            parsed_data[key] = bullets
            
        else:
            parsed_data[key] = content
            
    # logger.debug("Successfully parsed final report into a structured dictionary.")
    return parsed_data