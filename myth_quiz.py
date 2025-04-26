import pandas as pd
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

class MythQuiz:
    def __init__(self, path):
        self.df = pd.read_csv(path, sep=";", encoding="utf-8")

    def get_total(self):
        return len(self.df)

    def get_question(self, index):
        row = self.df.iloc[index]
        statement = row['statement']
        is_true = str(row['is_true'])
        explanation = row['explanation']
        return index, statement, is_true, explanation

    def get_keyboard(self, question_index):
        return InlineKeyboardMarkup(inline_keyboard=[
            [
                InlineKeyboardButton("✅ Правда", callback_data=f"quiz:{question_index}:True"),
                InlineKeyboardButton("❌ Миф", callback_data=f"quiz:{question_index}:False")
            ]
        ])
