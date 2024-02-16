# inference-providers.py
# https://github.com/stuartriffle/inference-providers

import difflib
from openai import OpenAI
from natsort import natsorted
import os, random, json, requests

json_update_download_url  = "https://raw.githubusercontent.com/StuartRiffle/inference-providers/main/inference-providers.json"
common_oia_server_ports   = [1234, 3000, 5000, 7860, 7861, 8000, 8080, 9997, 11434, 18888]
common_key_var_substrings = ["_API", "_KEY", "_SECRET", "_TOKEN", "ACCESSKEY", "SECRETKEY"]
common_api_key_prefixes   = ["esecret_", "sk-", "pplx-", "r8_", "gsk-"]

class ProviderList:
    """A class for managing a list of LLM inference providers."""
    def __init__(self, verbose=False, json_override=None, auto_update=False):
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
        self.provider_info = self.config.get("providers", {})

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
        return list(model_names)

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
        # Scan the default ports common proxy servers use
        port_to_check = set(common_oia_server_ports)

        # Also scrape anything that looks like a port number at the end of a var
        for key in os.environ:
            value = os.environ[key]
            if "port" in key.lower() and value.isdigit():
                port_to_check.add(int(value))
                continue
            colon_index = value.rfind(":")
            if colon_index != -1 and value[colon_index+1:].isdigit():
                port = int(value[colon_index+1:])
                port_to_check.add(port)

        open_ports = []
        for port in port_to_check:
            try:
                response = requests.get(f"http://localhost:{port}")
                if response.status_code == 200:
                    open_ports.append(port)
            except: pass
        return open_ports

    def fuzzy_match_model_name(self, internal_name, canonical_names):
        """Find the canonical name that's the closest match to a provider's internal model name"""

        # Ignore any "path"-style prefix on the provider's internal model name           
        last_sep = max(internal_name.rfind("/"), internal_name.rfind("\\"))
        if last_sep > -1:
            internal_name = internal_name[last_sep+1:]

        if internal_name == canonical_name:
            return canonical_name
        
        candidates = []
        for canonical_name in canonical_names:
            # Every element in the simplified canonical name must appear *somewhere*
            elements = canonical_name.split("-")
            if not all(element in internal_name.lower() for element in elements):
                continue

            # Parameter count must also match (if present)
            param_match_failed = False
            for element in elements:
                if element.endswith("b") and element[:-1].isdigit:
                    expected = '-' + element
                    if not expected in internal_name.lower():
                        param_match_failed = True
                        break
            if param_match_failed:
                continue

            candidates.append(canonical_name)

        # Prefer canonical names that are a prefix match for the internal name (if any are)
        if len(candidates) > 1:
            prefix_matches = []
            for candidate in candidates:
                prefix = candidate.split("-")[0]
                if internal_name.startswith(prefix):
                    prefix_matches.append(candidate)
            if len(prefix_matches) > 0:
                candidates = prefix_matches

        if self.verbose:
            if len(candidates) == 0:    status = f'no canonical names match internal model name "{internal_name}"'
            elif len(candidates) == 1:  status = f'fuzzy matching {candidates[0]} to internal model name "{internal_name}"'
            else:                       status = f'fuzzy matching to internal model name "{internal_name}" failed, candidates: {candidates}'
            print(f'[inference-providers] {status}')

        if len(candidates) == 1:
            return candidates[0]
        
        if len(candidates) > 1:
            best_match = difflib.get_close_matches(internal_name, candidates, n=1, cutoff=0.5)
            if best_match:
                return best_match[0]
        
        return None
    

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
        gather_all = not canonical_name
        candidates = []

        for provider_name, info in self.provider_info.items():
            model_names = info.get("model_names", {})
            if gather_all or canonical_name in model_names:
                true_name = model_names[canonical_name]
                config    = info.get("connection", {})
                protocol  = config.get("protocol", None)
                key_var   = config.get("api_key",  None)
                url       = config.get("endpoint", None)
                url       = url.replace("$MODEL_NAME", true_name) if url else None
                api_key   = os.environ.get(key_var, None) if key_var else None

                if api_key and protocol == "openai":
                    connection = (provider_name, url, true_name, api_key)
                    candidates.append(connection)

        return candidates
    

    def connect_to_model_endpoint(self, endpoint, api_key, model_name, verify=False):
        """Create an OpenAI client for a model using a specific provider."""
        try:
            client = OpenAI(api_key=api_key, base_url=endpoint)
            if verify:
                if not self.get_response(client, model_name, "Who's your daddy?"):
                    print(f'[inference-providers] WARNING: no response from model "{model_name}" at "{endpoint}"')
                    return None, None
            return client, model_name
        except Exception as e:
            if self.verbose:
                print(f'[inference-providers] WARNING: failed to connect to model "{model_name}" at "{endpoint}"\n{e}')
        return None, None

    
    def connect_to_model(self, canonical_name, choose_randomly=False, verify=False):
        """Create an OpenAI client for a model using one of the known compatible providers."""
        candidates = self.find_model_providers(canonical_name)
        if choose_randomly:
             random.shuffle(candidates)
        for connection in candidates:
        
            provider, endpoint, internal_name, api_key = connection
            try:
                client = OpenAI(api_key=api_key, base_url=endpoint)
                if verify:
                    if not self.get_response(client, internal_name, "Who's your daddy?"):
                        print(f'[inference-providers] WARNING: no response from model "{canonical_name}" at "{endpoint}"')
                        continue
                return client, internal_name
            except Exception as e:
                if self.verbose:
                    print(f'[inference-providers] WARNING: failed to connect to model "{canonical_name}" at "{endpoint}"\n{e}')
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
                    {"role": "system", "content": "Just play along"},
                    {"role": "user",   "content": prompt}
                ])
            content = response.choices[0].message.content.strip()
            print(content)
            return content
        except Exception as e:
            if self.verbose:
                print(f'[inference-providers] WARNING: exception running inference on model "{model_name}"\n{e}')            
        return None

    def ask_ai(self, question, test=True):
        """Scream into the void."""
        client, true_name = self.connect_to_ai(test=test)
        response = self.get_response(client, true_name, question)
        return response or "?"
    
