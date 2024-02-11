# inference-providers.py
# https://github.com/stuartriffle/inference-providers

from openai import OpenAI
import os, random, json, requests

update_download_url = "https://raw.githubusercontent.com/StuartRiffle/inference-providers/main/inference-providers.json"

class ProviderList:
    """A class for managing a list of LLM inference providers."""
    def __init__(self, verbose=False, json_override=None, auto_update=False):
        self.verbose = verbose
        json_text = json_override
        if auto_update:
            json_text = ProviderList.get_updated_provider_list(verbose=verbose) or json_text
        if not json_text:
            root = os.path.dirname(os.path.abspath(__file__))
            default_path = os.path.join(root, "inference_providers.json")
            with open(default_path, "r") as f:
                json_text = f.read()
        self.provider_info = json.loads(json_text)

    @staticmethod
    def get_updated_provider_list(verbose=False):
        """Download the latest provider list from the GitHub repo."""
        json = None
        try:
            response = requests.get(update_download_url)
            json = response.text
        except: pass
        if verbose:
            status = "updated" if json else "WARNING: unable to update"
            print(f'[inference-providers] {status} list from {update_download_url}')
        return json

    def get_canonical_model_names(self):
        """Return a list of all known model names."""
        model_names = set()
        for provider in self.provider_info:
            model_names.update(provider.get("model_names", {}).keys())
        return list(model_names)

    def find_model_providers(self, canonical_name):
        """Find providers that support a given model."""
        candidates = []
        provider_lookup = self.provider_info.get("providers", {})
        for provider_name, info in provider_lookup.items():
            model_names = info.get("model_names", {})
            internal_name = model_names.get(canonical_name, None)
            if internal_name:
                connection_info = info.get("connection", {})
                protocol = connection_info.get("protocol", None)
                key_var = connection_info.get("api_key", None)
                url = connection_info.get("endpoint", None)
                if protocol == "openai":
                    api_key = os.environ.get(key_var, None)
                    if api_key:
                        if url:
                            url = url.replace("{{model_name}}", internal_name)
                        connection = (provider_name, url, internal_name, api_key)
                        candidates.append(connection)
        return candidates
    
    def connect_to_model(self, canonical_name, choose_randomly=False, test=False):
        """Create an OpenAI client for a model using one of the known compatible providers."""
        candidates = self.find_model_providers(canonical_name)
        if choose_randomly:
             random.shuffle(candidates)
        for connection in candidates:
            provider, endpoint, internal_name, api_key = connection
            try:
                client = OpenAI(api_key=api_key, base_url=endpoint)
                if test:
                    response = client.chat.completions.create(model=internal_name, 
                        messages=[{"role": "system", "content": "Answer precisely."},
                                  {"role": "user",   "content": "What's your sign, baby?"}])
                    inference_working = response.choices[0]
                    if not inference_working:
                        continue
                else:
                    if self.verbose:
                        warning  = f'provider "{provider["name"]}" does not support model "{canonical_name}"'
                        print(f'[inference-providers] WARNING: {warning}')
                return client, internal_name
            except Exception as e:
                if self.verbose:
                    print(f'[inference-providers] WARNING: failed to connect to model "{canonical_name}" at "{endpoint}"')
        return None, None
    
    def connect_to_first_available_model(self, model_names, test=False):
        """Create an OpenAI client for a model using one of the known compatible providers."""
        for canonical_name in model_names:
            client, internal_name = self.connect_to_model(canonical_name, test=test)
            if client:
                return client, internal_name
        return None, None
    
    def connect_to_ai(self, test=True):
        """Create an OpenAI client for whatever is available to the user."""
        priority_order = self.provider_info.get("auto_model_priority", [])
        client, internal_name = self.connect_to_first_available_model(priority_order, test=test)
        return client, internal_name
    
    def get_response(self, client, model_name, prompt):
        """Get a response from an AI model."""
        try:
            response = client.chat.completions.create(model=model_name, messages=[
                {"role": "system", "content": "Just play along."},
                {"role": "user",   "content": prompt}])
            return response.choices[0].message.content.strip()
        except: pass
        return None

    def ask_ai(self, question, test=True):
        """Scream into the void."""
        client, true_name = self.connect_to_ai(test=test)
        response = self.get_response(client, true_name, question)
        return response or "?"
    
