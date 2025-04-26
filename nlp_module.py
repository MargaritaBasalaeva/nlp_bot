from transformers import AutoTokenizer, AutoModelForSequenceClassification
import torch
import re
import emoji

class SentimentAnalyzer:
    def __init__(self):
        self.model_name = "cointegrated/rubert-tiny-sentiment-balanced"
        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModelForSequenceClassification.from_pretrained(self.model_name)

        self.labels = ['negative', 'neutral', 'positive']
        self.emojis = {'negative': '🙁', 'neutral': '😐', 'positive': '😊'}

        self.negative_triggers = [
            "не понравилось", "ужасно", "отстой", "не зашло", "ненавижу", "разочарован", "разочарование"
        ]

    def preprocess_emojis(self, text):
        return emoji.demojize(text, delimiters=(" ", " "))

    def clean_text(self, text):
        return re.sub(r'[^\w\s]', '', text.lower())

    def post_correct_label(self, text, label):
        cleaned_text = self.clean_text(text)
        if label == "neutral":
            for phrase in self.negative_triggers:
                if phrase in cleaned_text:
                    return "negative"
        return label

    def analyze(self, text):
        # Препроцессинг эмодзи
        processed_text = self.preprocess_emojis(text)

        inputs = self.tokenizer(processed_text, return_tensors="pt", truncation=True)
        with torch.no_grad():
            logits = self.model(**inputs).logits
        probs = torch.nn.functional.softmax(logits, dim=1)
        label_idx = torch.argmax(probs, dim=1).item()
        initial_label = self.labels[label_idx]
        confidence = probs[0][label_idx].item()

        # Посткоррекция
        corrected_label = self.post_correct_label(text, initial_label)

        return corrected_label, confidence, self.emojis[corrected_label]

    def generate_response(self, label):
        responses = {
            "positive": "Спасибо за тёплый отзыв! 😊 Очень приятно 💖",
            "neutral": "Спасибо за отзыв! Если есть идеи для улучшения — напиши 💡",
            "negative": "Жаль, что не понравилось 🙁 Если расскажешь подробнее — обязательно улучшим!"
        }
        return responses.get(label, "Спасибо за обратную связь!")

