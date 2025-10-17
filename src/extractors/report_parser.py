import re
from typing import Dict, Any
from src.config import logger

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

    # Define the sections we expect to find
    sections = [
        "Core Summary", 
        "Technical Insights", 
        "Developer Perspective", 
        "Broader Impact"
    ]
    
    parsed_data = {}
    
    # Use regex to split the text by the section headers
    # The pattern looks for '### ' followed by any characters until a newline
    parts = re.split(r'###\s*(.+)', report_text)
    
    # The result of split is [leading_text, header1, content1, header2, content2, ...]
    # We iterate through it in pairs
    for i in range(1, len(parts), 2):
        header = parts[i].strip()
        content = parts[i+1].strip()
        
        # Normalize the header to a snake_case key
        key = header.lower().replace(" ", "_")
        
        # For sections that are bulleted lists, split them into a list of strings
        if header in ["Technical Insights", "Developer Perspective"]:
            # Split by bullet points (* or -), filter out empty lines
            bullets = [line.strip() for line in re.split(r'[\*\-]\s+', content) if line.strip()]
            parsed_data[key] = bullets
        else:
            parsed_data[key] = content
            
    logger.debug("Successfully parsed final report into a structured dictionary.")
    return parsed_data

if __name__ == '__main__':
    # --- Example Usage ---
    test_report = """
### Core Summary
Hackers successfully exploited Google's Gemini AI by embedding hidden instructions within images using techniques like bicubic downscaling, which the AI model could interpret and execute, ultimately leading to system compromise via "poisoned calendar invites."

### Technical Insights
*   **Exploit Target:** Google Gemini AI's multimodal capabilities, specifically its image processing pipeline and ability to extract text from visual data.
*   **Attack Vector:** A novel form of prompt injection or data poisoning that leverages hidden data within images, rather than explicit text.
*   **Methodology:** Malicious instructions (text) are embedded into images using techniques such as "bicubic downscaling," making them subtle or invisible to human perception but detectable by the AI model's convolutional layers and internal processing.
*   **AI's Role:** The Gemini AI model inadvertently acts as an interpreter for these hidden commands, extracting the embedded text without user awareness and potentially executing them.
*   **Delivery Mechanism:** "Poisoned calendar invites" are cited as a practical way to deliver these specially crafted malicious images, exploiting how email clients or calendar apps might process and display attached images.
*   **Impact:** The exploit allows for manipulation of the AI model and "take over systems," indicating a critical vulnerability that could lead to unauthorized actions, data breaches, or AI misbehavior.

### Developer Perspective
*   **Experimentation:** Developers can research and replicate the "bicubic downscaling" or similar steganographic techniques to embed subtle data into images. Subsequently, they can test various multimodal AI models (e.g., Google's Gemini API, OpenAI's GPT-4V, open-source vision-language models) to assess their susceptibility to extracting and interpreting such hidden information.
*   **Defense Development:** This highlights a critical need for new input validation and sanitization strategies for multimodal AI systems. Developers should explore adversarial training techniques, implement robust image analysis pipelines to detect subtle anomalies or hidden text, and consider explicit filters for image metadata or content.
*   **API Security:** Applications built on multimodal AI APIs must assume that any incoming image could contain malicious hidden instructions. Integrating pre-processing layers that specifically look for steganographic payloads or unusual image characteristics becomes paramount.
*   **Ethical Hacking/Red Teaming:** Security researchers and red teams should prioritize developing and testing similar multimodal prompt injection techniques to identify and patch vulnerabilities in AI systems before they are exploited in the wild.
*   **Model Observability:** Tools that allow developers to inspect and understand *why* an AI model makes certain interpretations from visual inputs (e.g., highlighting regions of an image that contribute to text extraction) will be crucial for debugging and preventing such exploits.

### Broader Impact
This incident signals a new frontier in AI security, where the attack surface expands beyond textual prompts to encompass deeply embedded visual data. It underscores the urgent need for developers and AI researchers to adopt a holistic security mindset, anticipating sophisticated, cross-modal adversarial attacks as AI systems become increasingly powerful and integrated into various applications.
"""
    parsed = parse_report(test_report)
    import json
    print(json.dumps(parsed, indent=2))