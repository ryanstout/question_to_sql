# Future place of prompt experiments


class Prompt:
    def __init__(self, schema: str, question: str):
        self.prompt_text = f"\n\n-- {question}\nSELECT "

    def text(self):
        return self.prompt_text
