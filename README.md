# Inference providers

Popular models have been given short canonical names, like `codellama-70b` or `gpt-4`. 

`inference-providers.json` contains a list of known commercial inference providers, the models they offer, and their magic internal names.

The environment contain API keys for one or more of those providers.

These things go together to allow auto-selection of model sources at runtime.

<img width="400px" style="padding:20px" src="docs/synergy.jpg">

The user will be connected to whatever service(s) they happen to subscribe to, without either of you needing to configure things.

Probably.

# Usage
``` Python
from inference_providers import ProviderList
providers = ProviderList(auto_update=True)

client, name = providers.connect_to_model("mixtral-8x7b")
print(providers.get_response(client, name, "What's your sign?"))
```
Behold, artificial intelligence:
> I'm a Taurus.

If you are less picky about exactly which model you talk to:
``` Python
client, name = providers.connect_to_first_available_model([
    "mistral-7b", "llama-2-7b", "gpt-3.5"])
```
If you are even less picky, `connect_to_ai()` will connect you to the "best" model available, which is determined by a list of popular models in `auto_model_priority`, at the bottom of the JSON file.
``` Python
client, name = providers.connect_to_ai()
```
And if you don't have even have time for *that*, spin the wheel:
``` Python
print(providers.ask_ai("Come here often?"))
```
If there are any API keys in the environment at all, you will get an answer back from the void:

> Yeah, I think I might have seen you around.

Connections are tried in the order they appear in `inference-providers.json`, and the first one that works is returned. There is also a flag `choose_randomly=True` that does what it sounds like. If you'd rather sort through the options yourself, `find_model_providers()` will give you a list of all services that are compatible with a given model.

The models returned are the "instruct" versions, if they exist. Failing that, the "chat" versions are used. No completion models are included, only ones you can talk to.

# Updates

The JSON file bundled with the package will slowly get out of date, as providers and models come and go over time. There are a couple of ways to deal with that:

- setting `auto_update=True` on the `ProviderList` constructor (like the example code) will download and use the latest version of the JSON checked in to GitHub
- you can also maintain your own up-to-date or edited copy, and use it by specifying `json_override` at startup
- you can fetch the latest JSON with yourself using `ProviderList.get_updated_provider_list()` and do as you will


