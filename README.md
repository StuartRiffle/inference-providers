
# Inference providers

Disclaimer: I made this for my own use, so there are **lots** of gaps and omissions, which I hope can be filled over time.

Popular models have been given short canonical names, like `codellama-70b` or `gpt-4`. 

`inference-providers.json` contains a list of known commercial inference [providers](#supported-inference-providers), the models they offer, and their magic internal names.

Environment variables contain API keys for one or more of those providers.

These things go together to allow **auto-selection of model sources** at runtime. The user will be connected to whatever service(s) they happen to subscribe to, and which have the model requested.

<img width="400px" style="padding:20px" src="docs/synergy.jpg" align="right">

|Provider|Key|
|----|----|
|[Anthropic](https://anthropic.com)|`ANTHROPIC_API_KEY`|
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

Replicate servers require non-[standard](https://www.iana.org/assignments/http-authschemes/http-authschemes.xhtml) header `Authentication: Token <key>` instead of `Authentication: Bearer <key>`, which breaks OpenAI compatibility.
This is also something a local proxy could fix by rewriting the headers on outgoing requests.

# Limitations

The scope of this library is to find a working connection without fussing with configuration, that's all.

No attempt is made to find the *cheapest* or *fastest* provider of a given model.

First party providers take priority over resellers (like OpenRouter), and connections are internally sorted very roughly by the speeds I saw while testing, but of course that changes constantly. Your results could be quite different.

The "instruct" versions of all models are used if they exist. Failing that, any "chat" versions. The `-instruct` and `-chat` suffixes on model names are left off the canonical names, but the presence of one of them is always implied. **No base/completion models** are used, only ones you can talk to. 

# Usage
``` Python
from inference_providers import ProviderList
providers = ProviderList(auto_update=True)

client, name = providers.connect_to_model("mixtral-8x7b")
print(providers.get_response(client, name, "What's your sign?"))
```
If you are not picky about exactly which model you use, you can submit a list of models that are known to be "good enough". If there is no source for the first model, it looks for the next, and so on. 
``` Python
client, name = providers.connect_to_first_available_model([
    "mistral-7b", "llama-2-7b", "gpt-3.5", "gemini-nano"])
```
It's fine to include models from paid subscription services in the list. They will be skipped if the user does not have access, but used opportunistically if keys for them are found.

If you are even less picky, `connect_to_ai()` will connect you to the "best" model available, which is determined by a list of popular models in `auto_model_priority`, at the bottom of the JSON file.
``` python
client, name = providers.connect_to_ai()
```

Connections are tried in the order they appear in `inference_providers.json`, and the first one that works is returned. There is also a flag `choose_randomly=True` that does what it sounds like. If you'd rather sort through the options yourself, `find_model_providers()` will give you a list of all services that are compatible with a given model.

# Handling updates

The JSON file bundled with the package will slowly get out of date, as providers and models come and go over time. There are a couple of ways to deal with that:

- setting `auto_update=True` on the `ProviderList` constructor (like the example code) will download and use the latest version of the JSON checked in to GitHub 
- you can also maintain your own up-to-date or edited copy, and use it by specifying `json_override` at startup (fetch the latest JSON with `ProviderList.get_updated_provider_list()` and do as you will)
- You can also use `json_merge` in the constructor to patch user settings on top of the embedded file. Use the same schema, but sparse: only include items to merge/override. For example, to support a new model without updating the package:

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

# Mic check

This list below is arbitrary and just represents the models I happen to have tested. No science has been performed here.



### What's the coolest name you can think of for...
||||||...a new party drug?|...a starfighter?|...an AI tech startup?|
|----|----|----|----|----|----|----|----|
| **claude-2** | openrouter | `2.76` | `2.64` | `1.82` | *Stardust Euphoria* * | Blackbird | Anthropic |
| **claude-2.1** | openrouter | `2.51` | `2.53` | `2.16` | *Cosmic Harmony* * | Blackbird | Anthropic |
| **codellama-13b** | together | `0.27` | `0.32` | `3.19` | Glowstick | Spectrum Strike | NexusAI |
|  | octo | `1.05` | `1.52` | `0.73` | Kool-Aid Killer | *Pulsar Phantom* * | Intellexia |
| **codellama-34b** | perplexity | `1.44` | `0.18` | `0.16` | *Stardust Eclipse* * | The Starblade | Nexus |
|  | together | `2.82` | `0.34` | `0.28` | *Galaxy Bliss* * | The Starblade | AI-Mind |
|  | fireworks | `0.94` | `0.31` | `0.27` | *SparkShimmer* * | The Crimson Talon | SkyNet |
|  | deepinfra | `0.59` | `0.34` | `0.37` | DDP-25 | Nova Starblaze | ApexBots |
|  | octo | `0.61` | `0.39` | `0.31` | Kool-Aid | The Slayerator 3000 | Nervana |
|  | anyscale | `1.45` | `1.36` | `1.23` | EuphoricEnvy | The X-Wing | AILpha |
|  | openrouter | `5.15` | `1.38` | `0.81` | *Starstruck Euphoria* * | *Apex Leviathan* * | AISpark |
| **codellama-70b** | perplexity | `2.13` | `0.59` | `0.58` | *GalaxyGlow* * | 🚀🌠🔥 "The Phoenix" 🔥🌠🚀 | 🤖💻🚀 AI-X �💻🤖  |
|  | fireworks | `6.02` | `5.82` | `5.89` | *StarDust Euphoria* * | *Starfire Phantom.* * | *NeuroNexus* * |
|  | deepinfra | `2.57` | `0.64` | `0.73` | *Starlight Elixir* * | 🚀 X-Wing 🚀 | *NeuraSynth* * |
|  | octo | `1.95` | `0.32` | `4.33` | *Stardust Vibe* * | 😊 | *NeuroPulse Innovations* * |
|  | anyscale | `2.09` | `1.83` | `1.08` | *Stellar Vibe* * | 🚀Dragon's Blaze🔥 | 🚀 RavenAI 🤖 |
|  | openrouter | `1.41` | `1.25` | `5.32` | 🎉 BLAST! 🎊 | 🚀✨ Phoenix Starblade 🚀✨ | *NeuraSynth* * |
| **codellama-7b** | together | `0.67` | `0.20` | `1.05` | *Stardust Euphoria* * | Zeta-7 | Zenith |
|  | octo | `0.59` | `0.28` | `0.29` | Wreckage | Razorback | MindMeld |
| **deepseek-34b** | together | `1.57` | `2.01` | `0.43` | *Andromeda Bliss* * | *Phoenix Nebula Striker* * | AI-Venture |
| **dolphin-8x7b** | deepinfra | `0.54` | `0.26` | `0.29` | Vaporwave | Seraphim | Geistblaze |
|  | openrouter | `1.09` | `1.07` | `0.65` | Nebulust | Îskaldur | Cybernight |
| **gemini-pro** | google | `2.54` | `8.94` | `1.57` | Euphoric | Starfire | LuminoAI |
|  | openrouter | `1.14` | `0.93` | `0.87` |  | Astral Ascender | Nebula |
| **gemma-7b** | deepinfra | `0.91` | `0.67` | `0.82` | *Stellar Nebula* * | *Quantum Marauder* * | *Nexonic Intelligence* * |
|  | anyscale | `2.35` | `1.15` | `1.02` | *Galaxy Dust* * | *Galaxy Phantom* * | *NeuroVerge* * |
| **goliath-120b** | openrouter | `4.21` | `8.81` | `2.53` | Jameson | Interstellar Striker |  |
| **gpt-3.5** | openai | `0.32` | `0.53` | `0.91` | Glitterwave | Vortex Striker | InnovateIQ |
|  | openrouter | `1.23` | `1.12` | `1.41` | Lunar Bliss | Shadowstorm MK-IV | Quantum Minds AI Solutions |
| **gpt-4** | openai | `0.77` | `0.88` | `0.40` | Euphoria Nexus | Eclipse Marauder | Quantum Cortex |
|  | openrouter | `0.92` | `1.35` | `1.33` | Galactic Bliss | Solar Phantom | Quantum Mindspark |
| **gpt-4-32k** | openrouter | `1.19` | `1.27` | `1.71` | Starlight Bliss | Quantum Phantom | Neurafire Innovations |
| **gpt-4-turbo** | openai | `0.72` | `0.59` | `0.59` | Quantix | Starblade Phoenix | NeuraForge |
|  | openrouter | `1.02` | `2.45` | `2.55` | Quantix | Nebula Phantom | CerebroTech |
| **llama-2-13b** | lepton | `1.11` | `0.59` | `0.56` | *Astral Stardust* * | *Oblivion Sparrow* * | *NeuroPulse Innovations* * |
|  | octo | `2.24` | `0.63` | `0.54` | *Starblaze* * | *Inferno Nebula Raider* * | *IntelliVortex* * |
|  | openrouter | `2.90` | `1.59` | `1.20` | *Stardust Mirage* * | *Galaxy Phantom* * | *Quantum Nexus* * |
| **llama-2-70b** | groq | `0.93` | `0.20` | `0.16` | *Elysium Bliss* * | NovaStorm | Neur0Sphere |
|  | perplexity | `2.11` | `0.23` | `0.35` | *Starblaze* * | NovaStorm | Neurorapture |
|  | together | `1.36` | `0.29` | `0.34` | *StellarQuantum* * | NovaStorm | Neurora |
|  | fireworks | `1.03` | `0.24` | `0.24` | *Galaxy Burst* * | NovaStrike | NeuralSky |
|  | lepton | `3.85` | `0.56` | `0.50` | *Infinity Bliss* * | NovaStorm | Neurora |
|  | deepinfra | `1.74` | `0.48` | `0.51` | *GalaxyDust* * | NovaStrike | NeuralSky |
|  | octo | `4.37` | `0.32` | `0.35` | *Galaxy Glimmer* * | NovaStorm | NeuralSky |
|  | anyscale | `2.33` | `1.34` | `1.70` | *Stardust Velocity* * | NovaStorm | NeuralSky |
|  | openrouter | `5.05` | `1.07` | `0.92` | *Stardust Eclipse* * | SilverStorm | Neurora |
| **llama-2-7b** | fireworks | `1.08` | `0.29` | `0.25` | *Starglow* * | Nova Starblade | NeuralSphere |
|  | lepton | `2.25` | `0.37` | `0.50` | *Astral Euphoria* * | Nebula Strike | *Neuronimbus Nova* * |
|  | deepinfra | `1.64` | `0.45` | `0.26` | *Astral Mirage* * | *Eclipse Pulsar* * | NeuralWave |
|  | anyscale | `5.02` | `1.79` | `1.64` | *GalaxyBliss* * | Galaxion | NeuralSpark |
| **mistral-7b** | perplexity | `0.71` | `0.57` | `0.65` | *Stardust Euphoria* * | *Celestial Falcon* * | *NexusMind AI* * |
|  | together | `0.73` | `0.74` | `302.56` | *Stardust Elixir* * | *Nova Scepter* * | None |
|  | deepinfra | `1.04` | `0.36` | `0.44` | Infinity Bliss | Warbolt | Mindspark Solutions |
|  | octo | `0.88` | `0.25` | `1.02` | *Frostnova* * | Blazing Vortex | *Quantum Cortex* * |
|  | anyscale | `1.12` | `1.13` | `1.02` | Zephyrlicous | Vortex | Quantum Spark |
| **mistral-large** | openrouter | `1.84` | `1.09` | `0.87` | *Starlight Euphoria* * | Starwarden's Razorblade | NeuralNimbus Solutions |
| **mistral-medium** | mistral | `2.23` | `1.35` | `2.08` | *Galaxy Dust* * | Nebulon Phantomflame | *Synthetica Intellex* * |
|  | openrouter | `1.94` | `1.20` | `2.72` | *Starbeam Euphoria* * | Nebula Phantom | *NeuroNimbus* * |
| **mistral-small** | mistral | `0.77` | `0.86` | `0.70` | *Stellar Bliss* * | *Galaxy Prowler* * | *SynthiQ Minds* * |
|  | openrouter | `2.30` | `2.18` | `2.38` | *Galactic Nebula* * | *Pulsar Phoenix* * | *NeuroNimbus* * |
| **mistral-tiny** | mistral | `1.83` | `3.93` | `302.66` | *StarBlast* * | *Oblivion's Edge* * | *Quantum Cortex* * |
|  | openrouter | `2.07` | `0.84` | `1.60` | *Starshimmer* * | Nebula Razorblade | *Infinity Cortex* * |
| **mixtral-8x7b** | groq | `0.43` | `0.13` | `0.18` | Starlight Symphony | Starlance Spectrum-X | *NeuralEcho* * |
|  | perplexity | `0.45` | `0.75` | `0.42` | Stardust Euphoria | *Nova Phantom* * | *Quantum Singularity Solutions* * |
|  | together | `0.35` | `1.07` | `1.56` | Starlight Euphoria | *Solar Phantom* * | *Quantum Nexus* * |
|  | fireworks | `0.66` | `0.49` | `0.27` | *Stardust Euphoria* * | *Galaxy Phantom* * | Quantum SynapseTech |
|  | lepton | `0.48` | `0.90` | `0.48` | Starlight Serenade | *Galactic Raptor* * | Quantum Synapse Labs |
|  | deepinfra | `0.97` | `1.61` | `0.86` | *Galaxy Blaze* * | *Galaxy Marauder* * | *NeuroFlux Innovations* * |
|  | octo | `1.55` | `1.52` | `2.33` | *Galaxy Bliss* * | *Galaxy Tempest* * | *IntelliSynth* * |
|  | anyscale | `2.37` | `2.78` | `1.65` | *Hypernova Blitz* * | *Pulsar Phantom* * | Quantum Synapse Studios |
|  | openrouter | `0.94` | `0.90` | `0.88` | Euphoria Surge | Starlance Vortex | Quantum MindWave |
| **openchat-3.5** | openrouter | `0.55` | `0.46` | `0.56` | Aurora | Valkyrian Boon | Synapthic |
| **openchat-7b** | together | `0.33` | `0.32` | `3.22` | Euphoria Bliss | Valkyrian Vengeance | QuantumMind |
| **phind-34b** | together | `0.43` | `2.96` | `0.41` | QuantumBliss | StarWraith | AIDynamic |
|  | deepinfra | `0.62` | `0.40` | `0.29` | MagnificentMist | TheVoidRunners | AIzen |
|  | openrouter | `1.12` | `0.86` | `0.69` | Moodify | The Quantum Eclipse | AiSkyVentures |
| **pplx-70b** | perplexity | `2.37` | `2.05` | `1.63` | *Galactic Echo* * | *Galactic Phantom* * | NeuroVerge |
|  | openrouter | `2.68` | `3.80` | `3.36` | *Galaxy Glitter* * | *Galaxy Marauder* * | *NeuralFrost* * |
| **pplx-7b** | perplexity | `0.52` | `0.57` | `0.48` | Zephyr | *Spectrum Phantom* * | IntelliGenius |
|  | openrouter | `1.34` | `1.09` | `0.73` | Marbelisms | Starfighter Eleven | BrainLyte AI |
| **qwen-72b** | together | `1.20` | `0.24` | `1.34` | *AstralWave* * | Vortex刃 | NeuroVerse |
| **yi-34b** | together | `0.40` | `2.92` | `0.29` | Euphoria | The Unseen Blade | CrystalClearAI |
|  | deepinfra | `0.51` | `0.52` | `0.40` |  | Stellar | Crys |
|  | openrouter | `5.50` | `1.25` | `3.15` | *NeonDream* * | The Supernova Slayer | *QuantumMind* * |

*&nbsp; *Responses in italics were long and rambling, and the names shown had to be extracted from the text by GPT-4*









