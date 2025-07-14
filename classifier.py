from transformers import pipeline

# Load a fake news classifier model (you can test others too)
classifier = pipeline("text-classification", model="microsoft/propaganda-detection")

def detect_misinformation(text):
    result = classifier(text)[0]
    return result['label'], float(result['score'])