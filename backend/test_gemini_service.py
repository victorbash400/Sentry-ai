import sys
import os
from pathlib import Path

# Add backend to path
sys.path.append(str(Path(__file__).parent.parent))

from backend.services.gemini_service import GeminiService
from backend.services.pdf_service import PDFService

def test_gemini_service():
    print("Initializing Gemini Service...")
    try:
        gemini = GeminiService()
        pdf_service = PDFService()
        
        print("Generating test polygon image...")
        # Create a dummy polygon
        polygon = [
            {'lat': -1.2921, 'lng': 36.8219}, # Nairobi
            {'lat': -1.2925, 'lng': 36.8225},
            {'lat': -1.2930, 'lng': 36.8215},
            {'lat': -1.2921, 'lng': 36.8219}
        ]
        
        img_buffer = pdf_service._create_polygon_image(polygon)
        if not img_buffer:
            print("Failed to generate image")
            return

        print("Analyzing image with Gemini...")
        prompt = "What area is this? Identify the likely location based on the shape and coordinates if possible, or search for 'Nairobi agricultural areas'. Provide a brief description and any relevant agricultural details."
        
        result = gemini.analyze_image_with_search(img_buffer.getvalue(), prompt)
        
        print("\n--- Analysis Result ---")
        print(result['text'])
        
        print("\n--- Grounding Metadata ---")
        metadata = result.get('grounding_metadata', {})
        print(f"Queries: {metadata.get('queries')}")
        print("Sources:")
        for source in metadata.get('sources', []):
            print(f" - {source['title']}: {source['uri']}")
            
    except Exception as e:
        print(f"Test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gemini_service()
