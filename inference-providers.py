# inference-providers.py
# https://github.com/stuartriffle/inference-providers

import os, random, json, tempfile, urllib.request, shutil
from openai import OpenAI

update_download_url = "https://raw.githubusercontent.com/StuartRiffle/inference-providers/main/providers.json"

class ProviderList:
    """A class for managing a list of LLM inference providers."""
    def __init__(self, verbose=False, json_override=None, auto_update=False):
        self.verbose = verbose
        json = json_override
        if auto_update:
            json = ProviderList.get_updated_provider_data(verbose=verbose) or json
        if not json:
            root = os.path.dirname(os.path.abspath(__file__))
            default_path = os.path.join(root, "providers.json")
            with open(default_path, "r") as f:
                json = f.read()
        self.providers = json.loads(json)

    def get_canonical_model_names(self):
        """Return a list of all known model names."""
        model_names = set()
        for provider in self.providers:
            model_names.update(provider.get("model_names", {}).keys())
        return list(model_names)

    def find_model_providers(self, canonical_name):
        """Find all known providers that support a given model."""
        candidates = []
        for provider in self.providers:
            model_names = provider.get("model_names", {})
            internal_name = model_names.get(canonical_name, None)
            if internal_name:
                connection_info = provider.get("connection", {})
                key_var = connection_info.get("api_key", None)
                api_key = os.environ.get(key_var, None)
                if api_key:
                    endpoint = connection_info.get("endpoint", None)
                    endpoint = endpoint.replace("{{model_name}}", internal_name)
                    connection = (provider, endpoint, internal_name, api_key)
                    candidates.append(connection)
        return candidates
    
    def connect_to_model(self, canonical_name, choose_randomly=False):
        """Create an OpenAI client for a model using one of the known compatible providers."""
        candidates = self.find_model_providers(canonical_name)
        if choose_randomly:
             random.shuffle(candidates)
        for connection in candidates:
            provider, endpoint, internal_name, api_key = connection
            try:
                client = OpenAI(api_key=api_key, base_url=endpoint)
                if internal_name in client.models():
                    return client
                else:
                    if self.verbose:
                        warning  = f'provider "{provider['name']}" does not support model "{canonical_name}", update providers.json'
                        print(f'[inference-providers] WARNING: {warning}')
            except: pass
        return None
    
    @staticmethod
    def get_updated_provider_list(verbose=False):
        """Download the latest provider list from the GitHub repo."""
        json = None
        temp_folder = None
        try:
            temp_folder = tempfile.mkdtemp()
            download_path = os.path.join(temp_folder, "providers.json")
            urllib.request.urlretrieve.urlretrieve(update_download_url, download_path)
            with open(download_path, "r") as f:
                json = f.read()
        except: pass
            
        if temp_folder:
            try:    shutil.rmtree(temp_folder)
            except: pass

        if verbose:
            status = "updated" if json else "WARNING: unable to update"
            print(f'[inference-providers] {status} list from {update_download_url}')
        return json
    