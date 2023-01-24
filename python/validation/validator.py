# Run all of the questions marked correct or incorrect and output a confusion
# matrix and accracy

from prisma.enums import FeedbackState

from python.utils.connections import Connections


class Validator:
    def run(self):
        connections = Connections()
        connections.open()

        db = connections.db

        # Run through each marked question
        questions = db.question.find_many(
            {
                "OR": [
                    {"feedbackState": FeedbackState.CORRECT},
                    {"feedbackState": FeedbackState.INCORRECT},
                ]
            }
        )

        for question in questions:
            


if __name__ == "__main__":
    Validator().run()
