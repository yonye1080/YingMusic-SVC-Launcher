import os
from huggingface_hub import hf_hub_download

# Absolute cache root: a shortcut can start the app with any working directory,
# and a relative "./checkpoints" then points somewhere else entirely, making
# the bundled rmvpe/campplus weights look missing and triggering a re-download.
CACHE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "checkpoints")


def load_custom_model_from_hf(repo_id, model_filename="pytorch_model.bin", config_filename=None):
    os.makedirs(CACHE_DIR, exist_ok=True)
    model_path = hf_hub_download(repo_id=repo_id, filename=model_filename, cache_dir=CACHE_DIR)
    if config_filename is None:
        return model_path
    config_path = hf_hub_download(repo_id=repo_id, filename=config_filename, cache_dir=CACHE_DIR)

    return model_path, config_path
