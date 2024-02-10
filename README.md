**UNDER DEVELOPMENT - DO NOT USE THIS FOR IMPORTANT THINGS**

# LLM Inference Provider List

Popular models have been given short canonical names, like `codellama-70b` or `gpt-4`. 

`inference-providers.json` contains a list of known commercial inference providers, the models they offer, and their magic internal names.

Environment variables contain API keys for one or more of those providers.

These things go together to allow auto-selection of model sources at runtime.

<img width="400px" style="padding:20px" src="docs/synergy3.jpg">

The user will be connected to whatever service(s) they happen to subscribe to, without either of you needing to configure things.

# Usage
```
from inference_providers import ProviderList

providers = ProviderList(auto_update=True)
openai_client = providers.connect_to_model("mixtral-8x7b")

# ...insert artificial intelligence here
```

Connections are tried in the order they appear in `inference-providers.json`, and the first one that works is returned. There is also a flag `choose_randomly=True` that does what it sounds like. If you'd rather sort through the options yourself, `find_model_providers()` will give you a list of all services that are compatible with a given model.

# Updates

The JSON file bundled with the package will slowly get out of date, as providers and models come and go over time. There are a couple of ways to deal with that:

- by default, `auto_update=True` on the `ProviderList` constructor will download and use the latest version of the JSON posted to GitHub
- you can also maintain your own up-to-date or edited copy, and supply it with `json_override` at startup
- you can fetch the latest JSON with yourself at runtime using `ProviderList.get_updated_provider_list()` and do as you will


