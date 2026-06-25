import os
from PIL import Image
import logging

logger = logging.getLogger("indusbrain")

try:
    import pytesseract
    # Try to locate Tesseract on Windows standard paths if not in PATH
    if os.name == 'nt':
        tess_paths = [
            r"C:\Program Files\Tesseract-OCR\tesseract.exe",
            r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
            r"C:\Users\Pooja\AppData\Local\Programs\Tesseract-OCR\tesseract.exe"
        ]
        for path in tess_paths:
            if os.path.exists(path):
                pytesseract.pytesseract.tesseract_cmd = path
                break
    HAS_TESSERACT = True
except ImportError:
    HAS_TESSERACT = False

class OCRService:
    @staticmethod
    def extract_text(image_path: str) -> str:
        """
        Extract text from an image/pdf frame using Tesseract.
        Falls back to a mockup parser if Tesseract binaries are not found locally.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image not found at path: {image_path}")

        if not HAS_TESSERACT:
            logger.warning("pytesseract package not installed. Using mock text extraction.")
            return OCRService._mock_extraction(image_path)

        try:
            # Test run
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text
        except Exception as e:
            logger.warning(f"Tesseract OCR failed: {e}. Falling back to mock extraction.")
            return OCRService._mock_extraction(image_path)

    @staticmethod
    def _mock_extraction(image_path: str) -> str:
        """
        Mock extraction based on filename keyword checks for clean demonstration.
        """
        filename = os.path.basename(image_path).lower()
        if "pump" in filename or "pmp" in filename:
            return (
                "STANDARD OPERATING PROCEDURE: FEED PUMP OPERATION (PMP-101)\n"
                "1. Pre-start check: Ensure lube oil pressure is > 1.8 bar.\n"
                "2. Suction valve: Must be 100% open.\n"
                "3. Discharge valve: Keep closed until motor is started.\n"
                "4. Warning: Cavitation risk if intake suction pressure drops below 1.4 bar."
            )
        elif "valve" in filename or "vlv" in filename:
            return (
                "OEM MANUAL SECTION 4.7: CONTROL VALVE PNEUMATIC ACTUATORS (VLV-204)\n"
                "Model: VLV-204-Pneumatic\n"
                "Input Air Pressure: 5.5 bar nominal. Sticking risk observed if pressure < 5.2 bar.\n"
                "Maintenance: Check filters quarterly for moisture and lubrication."
            )
        elif "boiler" in filename or "blr" in filename:
            return (
                "BOILER BLOCK C SAFETY PROCEDURES (BLR-302)\n"
                "Under OISD-STD-189 Section 6.2, boilers must undergo annual relief valve certification.\n"
                "Operating Temperature Limit: 620 degrees C. Exceeding limit triggers tube creep deformation."
            )
        else:
            return (
                "INDUSTRIAL ASSET LOG MANIFEST\n"
                "Location: Jamnagar Refinery Complex Sector 3\n"
                "Extracted Tag references: PMP-101, VLV-204, BLR-302, T-104\n"
                "Regulatory mapping: PESO rules, OISD-STD-105, Indian Factory Act 1948."
            )
