from decouple import config


def ranker_datasets_path():
    datasets_path = config("DATASETS_PATH", cast=str)
    assert datasets_path is not None, "DATASETS_PATH must be set"
    return datasets_path


def ranker_models_path():
    models_path = config("MODEL_DATA_PATH", cast=str)
    assert models_path is not None, "MODEL_DATA_PATH must be set"
    return models_path
