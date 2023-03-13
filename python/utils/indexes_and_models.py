from python.questions.indexes_and_models import IndexesAndModels

INDEXES_AND_MODELS = None


def application_indexes_and_models():
    """
    A singleton instance for the embedding indexes and ranker models
    """
    global INDEXES_AND_MODELS  # pylint: disable=global-statement

    if INDEXES_AND_MODELS is None:
        INDEXES_AND_MODELS = IndexesAndModels()

    return INDEXES_AND_MODELS
