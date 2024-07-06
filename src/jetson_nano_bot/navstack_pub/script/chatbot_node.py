#!/usr/bin/env python


import pandas as pd
import re
import random
from fuzzywuzzy import fuzz
from fuzzywuzzy import process

class Chatbot:
    def __init__(self, filepath):
        self.responses = self.load_responses_from_excel(filepath)

    def load_responses_from_excel(self, filepath):
        df = pd.read_excel(filepath)
        responses = {}
        for _, row in df.iterrows():
            question = row['question'].strip().lower()
            response = row['response'].strip()
            if question in responses:
                responses[question].append(response)
            else:
                responses[question] = [response]
        return responses

    def respond(self, message):
        message = message.lower()
        best_match, confidence = process.extractOne(message, self.responses.keys(), scorer = fuzz.token_sort_ratio)
        if confidence > 60: 
           return random.choice(self.responses[best_match])
        tra_ve = "Xin lỗi, tôi không hiểu bạn đang nói gì. bạn có thế nói lại không?"
        return tra_ve

def main():
    bot = Chatbot('/home/rasp/catkin_ws/src/jetson_nano_bot/navstack_pub/script/chatbot.xlsx')
    print("Chatbot: Hello! Type 'bye' to exit.")
    while True:
        userinput = input("You: ")
        if userinput.lower() == 'bye':
            print("Chatbot: Goodbye!")
            break
        print(f"Chatbot: {bot.respond(userinput)}")

if __name__ == '__main__':
    main()
