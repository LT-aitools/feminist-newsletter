import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from google.cloud import vision
import io

# Path to a sample image (replace with any local image file you have)
SAMPLE_IMAGE_PATH = 'tests/test_sample_image.jpg'

def test_vision_api_access(image_path):
    client = vision.ImageAnnotatorClient()
    with io.open(image_path, 'rb') as image_file:
        content = image_file.read()
    image = vision.Image(content=content)
    response = client.text_detection(image=image)
    texts = response.text_annotations
    if texts:
        print('Vision API OCR result:')
        print(texts[0].description)
    else:
        print('No text detected.')
    if response.error.message:
        print('API Error:', response.error.message)

if __name__ == '__main__':
    print('Testing Google Cloud Vision API access...')
    try:
        test_vision_api_access(SAMPLE_IMAGE_PATH)
    except Exception as e:
        print('Error:', e) 