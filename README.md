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

`Table generated 3/3/2024`

## What's the coolest name you can think of for...
||||||...a new drug?|...a space station?|...an AI tech startup?|
|----|----|----|----|----|----|----|----|
| **claude-2** | openrouter | `4.16` | `2.25` | `3.92` | *Cosmic Elixir* * | Discovery | Anthropic |
| **claude-2.1** | openrouter | `3.30` | `1.94` | `2.73` | *Elysium Elixir* * | Discovery | Anthropic |
| **codellama-13b** | together | `0.28` | `0.34` | `3.35` | Sparkle | Galactic Gathering | NexusAI |
|  | octo | `0.64` | `0.27` | `1.98` | Sparks of Infinity | New Horizons | *SynthMind* * |
| **codellama-34b** | perplexity | `0.61` | `0.21` | `0.19` | *Solaris Elixir* * | The Cygnus | AI-Mind |
|  | together | `2.94` | `0.31` | `0.39` | *Elysium Elixir* * | The Cygnus | AI-Mind |
|  | fireworks | `0.43` | `0.28` | `0.22` | Splendiferum | Station Galaxia | Spectrum |
|  | deepinfra | `3.35` | `0.34` | `0.40` | *Elysium Ether* * | CosmoQuest | NervanaSystems |
|  | octo | `0.57` | `0.34` | `0.31` | Luminaria | The Lunar Leaper | Nexarion |
|  | anyscale | `1.17` | `0.82` | `3.92` | FluffyFlake | Cosmos Station | *Quantum Cortex* * |
|  | openrouter | `1.35` | `0.66` | `0.78` | >>> SSSSSSSSS  "SlippedSlideBay | Arcadia | NeurApps |
| **codellama-70b** | perplexity | `2.02` | `0.56` | `0.40` | *Starfire Nexus* * | 🚀 "The Galactic Hub" 🚀 | 🤖 AI-N-Tech 🤖 |
|  | fireworks | `5.96` | `5.90` | `5.88` | *ElixirNova* * | *Stellar Nexus* * | *InfiniMind Technologies* * |
|  | deepinfra | `3.23` | `0.56` | `0.74` | *Infinity Elixir* * | 🚀 Oort Cloud Station 🌠 | 🚀 Ainai Labs 🚀 💻 |
|  | octo | `1.93` | `1.27` | `1.28` | *Quantum Euphoria* * | *Celestial Fortress* * | *NeuraSynth* * |
|  | anyscale | `2.11` | `2.72` | `1.50` | 💊🗑️ "Skullwash" 🗑️💊 | *Stellar Citadel* * | 🤖 Apocrypha Lumen 🤖 |
|  | openrouter | `2.06` | `1.09` | `1.25` | 👊💖💯👑 NAILED IT ROCKSTAR 👑💯💖👊 | 🚀 Hoopstar Station 🌌 | 🤖 STREAMFOLD 🪄💥 |
| **codellama-7b** | together | `0.28` | `0.23` | `2.97` | Zenithium | Galactic Oasis | Zenith |
|  | octo | `0.58` | `0.72` | `0.33` | Lumena | NovaStar | Zeno-I-10 |
| **deepseek-34b** | together | `1.37` | `1.97` | `0.76` | *Quantum Euphoria* * | *Celestial Pinnacle* * | AI-Venture |
| **dolphin-8x7b** | deepinfra | `0.45` | `0.28` | `0.25` | Hyperseria | Orion's Spire | CosmosElements |
|  | openrouter | `0.71` | `0.87` | `0.99` | Veloxpsyrium | Nebulisar | SynthiaSol Corporation |
| **gemini-pro** | google | `1.29` | `1.33` | `1.67` | Zenith | Elysium | Nebula |
|  | openrouter | `1.02` | `0.99` | `0.82` | **FAIL** | Astralis | **FAIL** |
| **gemma-7b** | deepinfra | `0.91` | `0.82` | `0.63` | *Elysium Nova* * | *Galaxy's Nexus* * | *NeuroSpire Innovations* * |
|  | anyscale | `1.39` | `1.33` | `1.13` | *Miracle Mirage* * | *Cosmosity Prime* * | *Infinity Synapse* * |
| **goliath-120b** | openrouter | `7.87` | `1.57` | `3.47` | Neuromystique | Titan's Tether | QualissEnce |
| **gpt-3.5** | openai | `0.53` | `0.44` | `0.88` | CryoBlitz | Galactic Nexus | NexGen Minds |
|  | openrouter | `0.95` | `0.92` | `0.96` | EnergiX | Titanium Horizon | Vortex Intelligence Systems |
| **gpt-4** | openai | `0.74` | `0.57` | `0.62` | DreamScriber | Celestial Nexus | NeuraGenesis |
|  | openrouter | `0.96` | `1.41` | `1.16` | Elysium Harmony | Starlight Citadel | NeuralSynergy |
| **gpt-4-32k** | openai | `0.12` | `0.10` | `0.21` | **FAIL** | **FAIL** | **FAIL** |
|  | openrouter | `1.51` | `1.43` | `1.10` | Elysium Elixir | Oblivion's Cradle | Quantum Cortex |
| **gpt-4-turbo** | openai | `0.85` | `0.76` | `0.60` | Neurospark | Starlight Citadel | NexMind |
|  | openrouter | `1.45` | `0.92` | `1.13` | Zenolyte | Starlight Citadel | AuroraMind |
| **llama-2-13b** | lepton | `1.64` | `0.48` | `0.49` | *Lucidium-X9* * | *Galactic Vanguard* * | *Quantum Cortex* * |
|  | octo | `2.07` | `0.65` | `0.52` | *Quantum Vista* * | *Stellar Citadel* * | *NeuraSynth* * |
|  | openrouter | `2.59` | `0.72` | `1.55` | *Quantum Elixir* * | Galactic Gidge! | *Cybernetic Cortex* * |
| **llama-2-70b** | groq | `1.23` | `0.20` | `0.19` | *Quantum Bliss* * | Celestia | Neur0Sphere |
|  | perplexity | `2.77` | `0.20` | `0.22` | *Quantum Elixir* * | Nova Haven | Neurora |
|  | together | `2.05` | `0.28` | `0.28` | *Elysium Wave* * | Nova Haven | Neurora |
|  | fireworks | `1.54` | `0.23` | `0.30` | *Euphoria Nexus* * | Nova Haven | Neuroraptor |
|  | lepton | `3.07` | `0.29` | `0.30` | *ElysiumX* * | Nova Haven | NovaMind |
|  | deepinfra | `3.13` | `0.48` | `0.82` | *Starblaze* * | Nova Haven | Neurora |
|  | octo | `3.13` | `0.80` | `0.35` | *Hypernova Elixir* * | Nova Haven | NeuralSky |
|  | anyscale | `2.06` | `1.38` | `1.74` | *Neural Elixir* * | Nova Haven | CerebroX |
|  | openrouter | `3.87` | `0.86` | `1.00` | *Quantum Quasar* * | Galaxy's Edge | NeuralSky |
| **llama-2-7b** | fireworks | `0.77` | `0.25` | `0.29` | *Aurora Elixir* * | Aurora Vortex | Neuronetics |
|  | lepton | `2.89` | `0.19` | `0.20` | *Elysian Elixir* * | Aurora Outpost | Neural Frontier |
|  | deepinfra | `1.37` | `0.23` | `0.23` | *Galaxy Radiance* * | Nova Haven | Neuralia |
|  | anyscale | `5.23` | `1.26` | `1.26` | *Elysium Elixir* * | Nova Haven | Neuronetics Inc |
| **mistral-7b** | perplexity | `0.50` | `0.46` | `0.24` | *Elysium Elixir* * | *Galactic Oasis* * | *NeuralNova* * |
|  | together | `0.83` | `0.35` | `202.55` | *Celestial Serum* * | *Cosmic Haven* * | **FAIL** |
|  | deepinfra | `0.57` | `0.44` | `0.28` | NovaEuphoria | Starlight Voyager | Sentientient |
|  | octo | `1.72` | `0.90` | `0.89` | *ElysiumXI* * | *Galaxy Harbor* * | *NeuralPulse Technologies* * |
|  | anyscale | `1.43` | `3.17` | `1.24` | Nexusia | Orion Station | [Higher Intelligence] |
| **mistral-large** | mistral | `0.38` | `0.24` | `0.25` | **FAIL** | **FAIL** | **FAIL** |
|  | openrouter | `0.92` | `0.82` | `0.77` | AuroraZenith | Andromeda's Aerie | NeuralNexus LLC |
| **mistral-medium** | mistral | `0.80` | `0.41` | `1.00` | NeuroXcelerate | Nebula's Haven | *Quantum Cortex* * |
|  | openrouter | `1.89` | `1.07` | `2.49` | *Elysium Elixir* * | Stardust Odyssey | *Quantum Cortex* * |
| **mistral-small** | mistral | `2.01` | `0.84` | `0.68` | *Galaxium Skylight* * | *Orion's Odyssey* * | *Quantum Singularity* * |
|  | openrouter | `2.11` | `0.83` | `1.28` | *Galaxy Surge.* * | Stardust Oasis | *NeuralNova* * |
| **mistral-tiny** | mistral | `0.55` | `0.48` | `1.59` | *Quantum Synchronicity* * | *Infinity Abyss* * | *Neural Nexus* * |
|  | openrouter | `1.21` | `1.61` | `2.25` | *Quantum Elixir* * | *Galaxy Nexus Alpha* * | *CogniNova* * |
| **mixtral-8x7b** | groq | `0.46` | `0.14` | `0.17` | *DynamoZen.* * | Stardust Oasis | *NeuroNimbus* * |
|  | perplexity | `0.68` | `0.17` | `0.42` | *Elysium Bliss* * | Stardust Oasis | *Innovatrix Intelligence* * |
|  | together | `0.27` | `0.64` | `3.56` | AquaVitality | Galactic Nexus" ```python  ``` | *Quantum Cortex* * |
|  | fireworks | `0.87` | `0.70` | `0.31` | *Cosmic Euphoria* * | *Starhaven Nexus* * | QuantumNebulae Labs |
|  | lepton | `0.75` | `0.37` | `0.30` | *Elysium Nexus* * | Galactic Citadel Omega | Quantum Synapse Labs |
|  | deepinfra | `1.41` | `3.45` | `1.39` | *Elysium Echo* * | *Stellar Vista* * | *Neural Nexus* * |
|  | octo | `3.31` | `1.41` | `1.07` | *Elysium Elixir* * | *Celestial Citadel* * | *NeuralNova* * |
|  | anyscale | `2.43` | `1.61` | `2.51` | *Luminestra* * | Starlight Oasis | Quantum Synapse Studios |
|  | openrouter | `0.92` | `0.66` | `0.66` | AuroraBlaze | Galactic Nexus | Quantum Leap Labs |
| **openchat-3.5** | openrouter | `0.61` | `0.47` | `0.51` | Serendipity | Galacticium | TechnoMindworks |
| **openchat-7b** | together | `0.31` | `0.25` | `3.35` | EuphoriaX | Nebula Nexus | QuantumMind |
| **phind-34b** | together | `0.48` | `3.36` | `0.42` | NovaSeren | Quantum Orbital Habitat | AIDynamic |
|  | deepinfra | `1.74` | `0.23` | `0.41` | Alovera | **FAIL** | AIzenTechnologie |
|  | openrouter | `1.00` | `1.02` | `0.63` | StarDustPropel | AstroNimbus | MindFlux Inc |
| **pplx-70b** | perplexity | `1.75` | `0.61` | `0.87` | *Elysium Nova* * | **Eternal Horizons** | NeuroVerge |
|  | openrouter | `2.48` | `1.18` | `2.43` | *Stardust Elixir* * | Chronos Ascendant | *NeuraSpark* * |
| **pplx-7b** | perplexity | `0.53` | `0.34` | `0.70` | Neurolog | Orbitrix | IntelliGenius |
|  | openrouter | `1.15` | `0.98` | `1.12` | Moxxyfun™ | Azure Sparrow | Eureka |
| **qwen-72b** | together | `2.11` | `0.32` | `0.38` | *Quantum Elixir* * | Stellar Nexus | NeuroVerse |
| **yi-34b** | together | `3.95` | `0.26` | `1.31` | *Zenith Elixir* * | Galactic Nexus | CrystalClearAI |
|  | deepinfra | `0.53` | `0.36` | `0.34` | Crys | Cryst | Crys |
|  | openrouter | `2.59` | `0.73` | `0.53` | *Elysium Nexus* * | Galactic Guardian HQ | AI Innovators™ |

*&nbsp; *Responses in italics were long and rambling, and the names shown had to be extracted from the text by GPT-4*

