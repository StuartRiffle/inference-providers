# inference-providers.py
# https://github.com/stuartriffle/inference-providers

import difflib
from openai import OpenAI
import os, random, json, requests
from jsonmerge import Merger

json_update_download_url  = "https://raw.githubusercontent.com/StuartRiffle/inference-providers/main/inference-providers.json"
common_oia_server_ports   = [1234, 3000, 5000, 7860, 7861, 8000, 8111, 8080, 8888, 9997, 11434, 18888]
common_key_var_substrings = ["_API", "_KEY", "_SECRET", "_TOKEN", "ACCESSKEY", "SECRETKEY"]
common_api_key_prefixes   = ["esecret_", "sk-", "pplx-", "r8_", "gsk-"]
default_system_prompt     = "Just play along."

class ProviderList:
    """A class for managing a list of LLM inference providers."""
    def __init__(self, verbose=False, json_override=None, json_merge=None, auto_update=False):
        self.verbose = verbose
        if auto_update:
            json_override = ProviderList.get_updated_provider_list(verbose=verbose) or json_override
        json_text = json_override

        if not json_text:
            root = os.path.dirname(os.path.abspath(__file__))
            default_path = os.path.join(root, "inference_providers.json")
            with open(default_path, "r") as f:
                json_text = f.read()
                
        self.config = json.loads(json_text)
        if json_merge:
            schema = { "properties": { "providers": { "mergeStrategy": "objectMerge" } } }
            merger = Merger(schema)
            self.config = merger.merge(self.config, json.loads(json_merge))

        self.provider_info = self.config.get("providers", {})
        self.cached_clients = {}

    @staticmethod
    def get_updated_provider_list(verbose=False):
        """Download the latest provider list JSON file from the GitHub repo."""
        json = None
        try:
            response = requests.get(json_update_download_url)
            json = response.text
        except: pass
        if verbose:
            status = "updated" if json else "WARNING: unable to update"
            print(f'[inference-providers] {status} list from {json_update_download_url}')
        return json

    def get_canonical_names_in_use(self):
        """Return a list of all known model names."""
        model_names = set()
        for _, info in self.provider_info.items():
            model_names.update(info.get("model_names", {}).keys())
        return sorted(list(model_names))

    def detect_local_api_keys(self):
        potential_keys = []
        for var_name in os.environ:
            var_value = os.environ[var_name]
            if any(invalid_char in var_value for invalid_char in "\\ "):
                continue # Might be a path
            if os.path.isfile(var_value) or os.path.isdir(var_value):
                continue # Definitely a path
            if len(var_value) < 24:
                continue # 128 bit key uuencoded

            typical_name = any(sub in var_name for sub in common_key_var_substrings)
            typical_value = any(var_name.startswith(sub) for sub in common_key_var_substrings)
            if typical_name or typical_value:
                potential_keys.append(var_value)
        return potential_keys

    def detect_local_endpoints(self):
        # Scan the default ports that common proxy servers use
        open_ports = []
        for port in common_oia_server_ports:
            try:
                response = requests.get(f"http://localhost:{port}")
                if response.status_code == 200:
                    open_ports.append(port)
            except: pass
        return open_ports

    def fuzzy_match_model_name(self, internal_name, names):
        """Find the canonical name that's the closest match to a provider's internal model name"""
        # Ignore any "path"-style prefix on the provider's internal model name           
        last_sep = max(internal_name.rfind("/"), internal_name.rfind("\\"))
        if last_sep > -1:
            internal_name = internal_name[last_sep+1:]

        # Ignore anything after a colon
        first_colon = internal_name.find(":")
        if first_colon > -1:
            internal_name = internal_name[:first_colon]
        
        candidates = []
        for name in names:
            # Every element in the simplified canonical name must appear *somewhere*
            elements = name.split("-")
            if all(element in internal_name.lower() for element in elements):
                candidates.append(name)

        if self.verbose:
            if len(candidates) == 0:    status = f'no canonical names match internal model name "{internal_name}"'
            elif len(candidates) == 1:  status = f'fuzzy matching {candidates[0]} to internal model name "{internal_name}"'
            else:                       status = f'fuzzy matching to internal model name "{internal_name}" failed, candidates: {candidates}'
            print(f'[inference-providers] {status}')

        if candidates:
            candidates = difflib.get_close_matches(internal_name, candidates, n=1, cutoff=0.5)

        return candidates[0] if candidates else None

    # Exhaustive search for local port/key/model combinations that talk back
    #
    # - Invalid ones fail quickly, but this process may still be slow
    # - The results are cached after the first call, override with refresh_cache=True
    # - The server may use weird internal names for the models. If a different
    #   provider uses the same internal name, we assume the same mapping.
    # - If not, we try fuzzy matching to find the closest canonical name.
    # - If that fails, the model will still be accessible by its internal name.
    #
    def detect_local_connections(self, refresh_cache=False):
        if refresh_cache or not self.local_connections:
            keys = self.detect_local_api_keys()
            ports = self.detect_local_endpoints()
            canonical_names = self.get_canonical_names_in_use()
            self.local_connections = {}

            local_connection_info = {
                "name": "localhost",
                "website": "",
                "connection": {
                    "protocol": "openai",
                    "endpoint": "http://localhost:$PORT",
                    "api_key": "$API_KEY"
                },
                "model_names": {}
            }

            for port in ports:
                for key in keys:
                    try:
                        url = f"http://localhost:{port}"
                        client = OpenAI(api_key=key, base_url=url)
                        for model in client.models.list():
                            model_name = model.get("name", None)
                            canonical_name_guess = self.fuzzy_match_model_name(model_name, canonical_names)
                            if canonical_name_guess:
                                if self.get_response(client, model_name, "Got your ears on, good buddy?"):
                                    self.local_connections[canonical_name_guess] = ("openai", url, model_name, key)
                    except: pass
            
        return self.local_connections

    def find_model_providers(self, canonical_name=None):
        """Find providers that support a given model."""
        candidates = []
        for provider_name, info in self.provider_info.items():
            targets = [canonical_name] if canonical_name else self.get_canonical_names_in_use()
            model_names = info.get("model_names", {})
            
            for target in targets:
                if target in model_names.keys():
                    true_name = model_names[target]
                    config    = info.get("connection", {})
                    protocol  = config.get("protocol", None)
                    key_var   = config.get("api_key",  None)
                    url       = config.get("endpoint", None)
                    url       = url.replace("$MODEL_NAME", true_name) if url else None
                    api_key   = os.environ.get(key_var, None) if key_var else None
                    if api_key and protocol == "openai":
                        connection = (provider_name, url, target, true_name, api_key)
                        candidates.append(connection)

        return candidates
    
    def find_all_model_providers(self):
        """Find all providers that support any model."""
        return self.find_model_providers(None)

    def connect_to_model_endpoint(self, endpoint, api_key, internal_name, verify=False, allow_cached=True):
        """Create an OpenAI client for a model using a specific provider."""
        ident = api_key + (endpoint or "")
        try:
            if allow_cached and ident in self.cached_clients:
                client = self.cached_clients[ident]
            else:
                client = OpenAI(api_key=api_key, base_url=endpoint)
                self.cached_clients[ident] = client
            if verify:
                if not self.get_response(client, internal_name, "Who's your daddy?"):
                    print(f'[inference-providers] WARNING: no response from model "{internal_name}" at "{endpoint}"')
                    return None
            return client
        except Exception as e:
            if self.verbose:
                print(f'[inference-providers] WARNING: failed to connect to model "{internal_name}" at "{endpoint}"\n{e}')
        return None

    def connect_to_model(self, canonical_name, choose_randomly=False, verify=False):
        """Create an OpenAI client for a model using one of the known compatible providers."""
        candidates = self.find_model_providers(canonical_name)
        if choose_randomly:
             random.shuffle(candidates)
        for connection in candidates:
            _, endpoint, _, internal_name, api_key = connection
            client = self.connect_to_model_endpoint(endpoint, api_key, internal_name, verify=verify)
            if client:
                return client, internal_name
            
        return None, None
    
    def connect_to_first_available_model(self, model_names, verify=False):
        """Create an OpenAI client for a model using one of the known compatible providers."""
        for canonical_name in model_names:
            client, internal_name = self.connect_to_model(canonical_name, verify=verify)
            if client:
                return client, internal_name
        return None, None
    
    def connect_to_ai(self, verify=True):
        """Create an OpenAI client for whatever is available to the user."""
        priority_order = self.config.get("auto_model_priority", [])
        client, internal_name = self.connect_to_first_available_model(priority_order, verify=verify)
        return client, internal_name
    
    def get_response(self, client, model_name, prompt):
        """Get a response from an AI model."""
        try:
            response = client.chat.completions.create(
                model=model_name, 
                messages=[
                    {"role": "system", "content": default_system_prompt},
                    {"role": "user",   "content": prompt}
                ])
            content = response.choices[0].message.content.strip()
            return content
        except Exception as e:
            if self.verbose:
                print(f'[inference-providers] WARNING: exception running inference on model "{model_name}"\n{e}')            
        return None



