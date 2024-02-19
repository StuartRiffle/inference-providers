
# Inference providers

Disclaimer: I made this for my own use, so there are **lots** of gaps and omissions, which I hope can be filled over time.

Popular models have been given short canonical [names](#canonical-model-names), like `codellama-70b` or `gpt-4`. 

`inference-providers.json` contains a list of known commercial inference [providers](#supported-inference-providers), the models they offer, and their magic internal names.

Environment variables contain API keys for one or more of those providers.

These things go together to allow **auto-selection of model sources** at runtime. The user will be connected to whatever service(s) they happen to subscribe to, and which have the model requested.

<img width="400px" style="padding:20px" src="docs/synergy.jpg" align="right">

|Provider|Key|
|----|----|
|[Anyscale](https://anyscale.com)|`ANYSCALE_API_KEY`|
|[deepinfra](https://deepinfra.com)|`DEEPINFRA_API_KEY`|
|[fireworks.ai](https://fireworks.ai)|`FIREWORKS_API_KEY`|
|[Groq](https://groq.com)|`GROQ_API_KEY`|
|[Lepton AI](https://www.lepton.ai)|`LEPTON_API_KEY`|
|[Mistral AI](https://mistral.ai/)|`MISTRAL_API_KEY`|
|[Octo AI](https://octo.ai/)|`OCTOAI_TOKEN`|
|[OpenAI](https://openai.com)|`OPENAI_API_KEY`|
|[OpenRouter AI](https://openrouter.ai)|`OPENROUTER_API_KEY`|
|[Perplexity](https://perplexity.ai)|`PERPLEXITYAI_API_KEY`|
|[together.ai](https://together.ai)|`TOGETHERAI_API_KEY`|

### Supported using OpenAI compatibility proxy

- [Gemini](https://deepmind.google) via endpoint `http://localhost:6006/v1`

Google doesn't directly support the OpenAI API, but shims are available like 
[this one](https://github.com/zhu327/gemini-openai-proxy). 
If you run a proxy server on port `6006`, it will be automatically recognized as Gemini. The easiest way to do this is Docker:
```
docker run --restart=always -it -d -p 6006:8080 --name gemini zhu327/gemini-openai-proxy:latest
```

### Almost but not quite supported 

- [Replicate](https://replicate.com)

Replicate servers require non-standard header `Authentication: Token <key>` instead of `Authentication: Bearer <key>`, which breaks OpenAI compatibility.
This is also something a local proxy could fix by rewriting the headers on outgoing requests, but I don't have a turnkey solution for that.

- [Anthropic](https://anthropic.com)

I don't have an API key to test a direct connection yet, but `claude-2` is available via OpenRouter if you have an `OPENROUTER_API_KEY`. The first-party connection will be used by default once it is available.

# Limitations

The scope of this library is to find a working connection without requiring configuration, that's all.

No attempt is made to find the *cheapest* or *fastest* provider of a given model.

First party providers take priority over resellers (like OpenRouter), and they are internally sorted very roughly by the speeds I saw while testing, but of course that changes constantly. Your results could be quite different.

# Usage
``` Python
from inference_providers import ProviderList
providers = ProviderList(auto_update=True)

client, name = providers.connect_to_model("mixtral-8x7b")
print(providers.get_response(client, name, "What's your sign?"))
```
If you are not too picky about exactly which model you use, you can submit a list of models that are known to be "good enough". If there is no source for the first model, it looks for the next, and so on. 
``` Python
client, name = providers.connect_to_first_available_model([
    "mistral-7b", "llama-2-7b", "gpt-3.5", "gemini-nano"])
```
It's fine to include models from paid subscription services in the list. They will be skipped if the user does not have access, but used opportunistically if keys are found.

If you are even less picky, `connect_to_ai()` will connect you to the "best" model available, which is determined by a list of popular models in `auto_model_priority`, at the bottom of the JSON file.
``` python
client, name = providers.connect_to_ai()
```

Connections are tried in the order they appear in `inference_providers.json`, and the first one that works is returned. There is also a flag `choose_randomly=True` that does what it sounds like. If you'd rather sort through the options yourself, `find_model_providers()` will give you a list of all services that are compatible with a given model.

# Handling updates

The JSON file bundled with the package will slowly get out of date, as providers and models come and go over time. There are a couple of ways to deal with that:

- setting `auto_update=True` on the `ProviderList` constructor (like the example code) will download and use the latest version of the JSON checked in to GitHub 
- you can also maintain your own up-to-date or edited copy, and use it by specifying `json_override` at startup
- you can fetch the latest JSON with yourself using `ProviderList.get_updated_provider_list()` and do as you will

You can also use `json_merge` in the constructor to patch user settings on top of the embedded file. Use the same schema, but sparse: only include items to merge/override. For example, to support a new model without updating the package:

``` json
{
    "providers": {
        "openai": {
            "model_names": {        
                "gpt-5": "gpt-5-instruct-preview"
            }
        }
    }
}
```
This is the most robust solution. Look inside `inference_providers.json` for details.
``` python
from inference_providers import ProviderList
providers = ProviderList(json_merge=open('my_custom_config.json').read())

client, name = providers.connect_to_model("gpt-5")
print(providers.get_response(client, name, "How long do we have?"))
```

# Notes

### API cheat sheet

A model is normally considered "working" if we can connect to the server, but the methods also have a `test` option that runs an inference sample to verify the API key is authorized and a valid response comes back. It is disabled by default because the extra check makes initialization slower, but enable it if you can for more reliable connections.

``` Python
class ProviderList(verbose=False, json_override=None, json_merge=None, auto_update=False)

    # Get a list of unique model names available
    get_canonical_model_names()

    # Scan ports on the local machine for servers/proxies
    detect_local_connections(self, refresh_cache=False)

    # Get a list of provider connection options for a model
    find_model_providers(canonical_name)

    # Send a query to an existing client, blocking until the response arrives
    get_response(client, model_name, prompt)

    # Connect to a specific model using a provider with known support
    connect_to_model(canonical_name, choose_randomly=False, test=False)

    # Connect to a model from a (prioritized) list of acceptable ones
    connect_to_first_available_model(model_names, test=False)

    # Connect to the "best" model available given the user's API keys
    connect_to_ai(test=True)
```

### Canonical model names recognized
||||||
|-------------|---------------|----------------|---------------|---------------|
| gpt-3.5     | llama-2-7b    | mistral-7b     | pplx-7b       | falcon-40b    |
| gpt-4       | llama-2-13b   | mistral-tiny   | pplx-70b      | dolphin-8x7b  |
| gpt-4-32k   | llama-2-70b   | mixtral-8x7b   | deepseek-34b  | wizard-70b    |
| gpt-4-turbo | codellama-7b  | mistral-small  | phind-34b     | openchat-7b   |
| gemini-pro  | codellama-13b | mistral-medium | yi-34b        | openhermes-7b |
| claude-2    | codellama-34b | mistral-next   | qwen-72b      |               |
|             | codellama-70b |                |               |               |

This list is arbitrary and basically represents the models I happen to have tested. 

The "instruct" versions of models will be used if they exist. Failing that, any "chat" versions. The `-instruct` and `-chat` suffixes on model names are left off the canonical names, but the presence of one of them is always implied. **No base/completion models** are specified, only ones you can talk to. 

