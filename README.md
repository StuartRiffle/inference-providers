# Inference providers

Popular models have been given short canonical [names](#canonical-model-names), like `codellama-70b` or `gpt-4`. 

`inference-providers.json` contains a list of known commercial inference [providers](#supported-inference-providers), the models they offer, and their magic internal names.

Environment variables contain API keys for one or more of those providers.

These things go together to allow **auto-selection of model sources** at runtime.

<img width="400px" style="padding:20px" src="docs/synergy.jpg">

The user will be connected to whatever service(s) they happen to subscribe to, without either of you needing to configure things.

# Usage
``` Python
from inference_providers import ProviderList
providers = ProviderList(auto_update=True)

client, name = providers.connect_to_model("mixtral-8x7b")
print(providers.get_response(client, name, "What's your sign?"))
```
Behold, artificial intelligence:
> I'm a Taurus.

If you are not too picky about exactly which model you use, you can submit a list of models that are known to be "good enough". If there is no source for the first model, it looks for the next, and so on. 
``` Python
client, name = providers.connect_to_first_available_model([
    "mistral-7b", "llama-2-7b", "gpt-3.5", "gemini-nano"])
```
- For trivial tasks, start with the cheapest/fastest model that can do the job, and fall back to slower ones.
- For complex tasks, put the smartest models first, and fall back to less capable ones.
- It's fine to include models from paid subscription services in the list. They will be skipped if the user does not have access, but used opportunistically if keys are found.



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


# Handling updates

The JSON file bundled with the package will slowly get out of date, as providers and models come and go over time. There are a couple of ways to deal with that:

- setting `auto_update=True` on the `ProviderList` constructor (like the example code) will download and use the latest version of the JSON checked in to GitHub
- you can also maintain your own up-to-date or edited copy, and use it by specifying `json_override` at startup
- you can fetch the latest JSON with yourself using `ProviderList.get_updated_provider_list()` and do as you will


# Notes

### API cheat sheet

A model is normally considered "working" if we can connect to the server, but the methods also have a `test` option that runs an inference sample to verify the API key is authorized and a valid response comes back. It is disabled by default because the extra check makes initialization slower, but enable it if you can for more reliable connections.

``` Python
class ProviderList(verbose=False, json_override=None, auto_update=False)

    # Get a list of unique model names available
    get_canonical_model_names()

    # Get a list of provider connection options for a model
    find_model_providers(canonical_name)

    # Send a query to an existing client, blocking until the response arrives
    get_response(client, model_name, prompt)

    # Connect to a specific model using a provider with known support
    connect_to_model(canonical_name, choose_randomly=False, test=False)

    # Connect to a model from a (prioritized) list of acceptable ones
    connect_to_first_available_model(model_names, test=False)

    # Connect to the "best" model possible given the available API keys
    connect_to_ai(test=True)

    # If you gaze long enough into an abyss, the abyss will gaze back into you
    ask_ai(question, test=True)
```




### Canonical model names
||||||||
|-----|-----|-----|-----|-----|-----|-----|
|gpt-4          ||llama-2-70b           ||gemini-pro    ||falcon-40b|
|gpt-3.5        ||llama-2-7b            ||palm          ||yi-34b|
|               |                       ||              ||
|codellama-70b  ||codellama-python-70b  ||mistral-medium||
|codellama-34b  ||codellama-python-34b  ||mistral-small ||mixtral-8x7b|
|phind-34b      ||wizard-python-34b     ||mistral-tiny  ||mistral-7b|

The "instruct" versions of models will be used if they exist. Failing that, any "chat" versions. The `-instruct` and `-chat` suffixes on model names are left off the canonical names, but the presence of one of them is implied.

**No completion models** are included, only ones you can talk to. 

If you add a model, but it's insane and keeps repeating itself, you might be talking to the base/completion version. Try one of the instruct/chat-specialized variants instead.

### Supported inference providers

||||||
|-----|-----|-----|----|----|
|[OpenAI](https://platform.openai.com/) ||[Anyscale](https://anyscale.com)  ||[fireworks.ai](https://www.fireworks.ai/)|
|[Google](https://deepmind.google)      ||[Lepton AI](https://www.lepton.ai)||[perplexity.ai](https://perplexity.ai)   |
|[Mistral AI](https://mistral.ai)       ||[Replicate](https://replicate.com)||[together.ai](https://www.together.ai/)  |

If you use (or run) an OpenAI-compatible inference service that isn't listed here, please let me know so I can add support. This software is supposed to "just work" in any environment, which it does by recognizing provider API keys. No single provider supports every model, but multiple providers with overlapping model support _can_ provide complete coverage, and prevent downtime when there are service outages at individual providers. Every additional source makes the whole system more resilient.

Wasn't there a word for that?

<img width="400px" style="padding:20px" src="docs/synergy-also.jpg">

Damn right.


