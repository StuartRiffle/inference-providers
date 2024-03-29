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

## What's the coolest name you can think of for...
||||||...a new drug?|...a space station?|...an AI tech startup?|
|----|----|----|----|----|----|----|----|
| **claude-2** | openrouter | `3.30` | `2.21` | `1.92` | *Aetherium Skyline* * | Destiny | Anthropic |
| **claude-2.1** | openrouter | `2.86` | `2.15` | `2.34` | *Elysium Essence* * | Destiny | Anthropic |
| **codellama-13b** | together | `0.44` | `0.65` | `3.18` | Sparkle | Galactic Gathering | NexusAI |
|  | octo | `1.56` | `0.23` | `0.21` | Glittermith | Aurora Station | Intelligence |
| **codellama-34b** | perplexity | `2.06` | `0.21` | `0.24` | *SuperNova Bliss* * | The Cygnus Station | AI-Mind |
|  | together | `2.00` | `0.46` | `0.28` | *Starlight Miracle* * | The Cygnus | AI-Mind |
|  | fireworks | `0.99` | `0.32` | `0.21` | *Starlight Serenity* * | The Crimson Comet | NovaTech |
|  | deepinfra | `3.20` | `0.32` | `0.32` | *Elysium Myst* * | Cosmopolis | NeuralPulse |
|  | octo | `0.76` | `0.39` | `0.75` | Torflerin | The Galactic Nexus | Cerebra |
|  | anyscale | `1.23` | `1.72` | `0.88` | Aurora | CosmoSphere | MatrixMind |
|  | openrouter | `0.78` | `0.35` | `0.74` | Blissure | 007-C | Quantum Minds |
| **codellama-70b** | perplexity | `2.35` | `0.46` | `0.43` | *Elysium Bliss* * | 🚀 "The Galactic Hub" 🚀 | 🤖 AI-N-Tech 🤖 |
|  | fireworks | `5.90` | `5.78` | `5.84` | *ElysiumX9* * | *Aeon Nebula Nexus* * | *IntelliQuantum* * |
|  | deepinfra | `3.60` | `0.74` | `0.64` | *Galaxy Elixir* * | *Galaxy's Crest* * | 🤔💻 Doodle Innate AI 💥 |
|  | octo | `2.25` | `5.45` | `1.44` | *Astranova* * | *Cosmic Sanctuary* * | *NeuralNova* * |
|  | anyscale | `1.50` | `1.61` | `1.68` | 💊 "Optimistic Synergy" 💊 | 🚀☀️👽 Towering Starship Station 🚀☀️👽 | *Neural Nova* * |
|  | openrouter | `9.47` | `3.14` | `4.48` | *Revelixium* * | *Celestial Vertex* * | *Neural Nexus* * |
| **codellama-7b** | together | `0.30` | `0.52` | `2.83` | Zenithium | Galactic Oasis | Zenith |
|  | octo | `0.49` | `0.55` | `0.20` | Veridium | Zara's Oasis | MindMeld |
| **deepseek-34b** | together | `1.66` | `1.99` | `0.43` | *Quantum Ascendancy* * | *Nebula Nexus* * | AI-Venture |
| **dolphin-8x7b** | deepinfra | `0.27` | `0.19` | `0.23` | Ultelligence | Nebula Haven | CyberSpectra |
|  | openrouter | `0.61` | `0.70` | `0.53` | Aqualuna | Celestial Mirage | SynerGear |
| **gemini-pro** | google | `15.12` | `14.77` | `14.61` | **FAIL** | **FAIL** | **FAIL** |
|  | openrouter | `0.95` | `0.68` | `0.58` | Lucid | Celestial Haven | CogniVerse |
| **gemma-7b** | deepinfra | `0.65` | `0.44` | `0.59` | *Euphoria Elixir* * | *Astra Celestialis* * | *NeuraLink* * |
|  | anyscale | `1.17` | `1.49` | `1.39` | *Quantum Elixir* * | *Nebula Nexus* * | *QuantumClarity* * |
| **goliath-120b** | openrouter | `1.47` | `1.43` | `1.36` | NeuroBliss | Dione's Starfall | Synaptic Skies |
| **gpt-3.5** | openai | `0.48` | `0.84` | `0.39` | Eternalix | Celestial Nexus | CyberNova |
|  | openrouter | `1.30` | `1.18` | `0.75` | EternalWave | Aurora 9 | MindMatrix |
| **gpt-4** | openai | `0.50` | `0.45` | `0.48` | Elysium Ascend | Celestial Serenity | Quantum Quasar |
|  | openrouter | `1.35` | `1.12` | `1.68` | Aurora Spectra | Cosmic Odyssey Haven | NeuralNova |
| **gpt-4-32k** | openai | `0.09` | `0.10` | `0.20` | **FAIL** | **FAIL** | **FAIL** |
|  | openrouter | `1.47` | `0.69` | `1.59` | Elysium Elixir | Infinity Horizon | QuantumSynapse |
| **gpt-4-turbo** | openai | `0.64` | `0.86` | `0.67` | Quantixara | Starhaven Observatory | NeuroNexa |
|  | openrouter | `1.20` | `1.68` | `1.59` | NexaVoid | Starhaven Orbital | AuroraMind |
| **llama-2-13b** | lepton | `1.36` | `0.44` | `0.33` | *Elixirion.* * | *StarForge Citadel* * | *NeuroNexus Innovations* * |
|  | octo | `2.68` | `0.66` | `0.64` | *Elysium Bliss* * | *Orion's Halo* * | *Neural Nimbus* * |
|  | openrouter | `2.24` | `0.36` | `0.98` | *Galaxy Elixir* * | Cosmic Oasis | *NeuroPulse* * |
| **llama-2-70b** | groq | `0.70` | `0.97` | `0.17` | *AstralVibe* * | Celestia | Neur0Sphere |
|  | perplexity | `3.64` | `0.21` | `0.23` | *Quantum Elixir* * | Nova Haven | Neurora |
|  | together | `5.85` | `1.08` | `1.03` | *Elysium Echo* * | Nova Haven | Neurora |
|  | fireworks | `1.10` | `0.27` | `0.33` | *Quantum Elysium* * | Galaxy's Edge | *NeuroFusion Labs* * |
|  | lepton | `2.82` | `0.37` | `0.30` | *Elysium Bliss* * | Nova Haven | Neuromorphix |
|  | deepinfra | `3.59` | `0.56` | `0.50` | *Quantum Euphoria* * | Nova Haven | Neuromorphix |
|  | octo | `5.83` | `0.31` | `0.36` | *Galaxy Nebula* * | Nova Haven | NeuralSky |
|  | anyscale | `3.56` | `1.62` | `1.78` | *Elysium Wave* * | Nova Spire | Neuromorphix |
|  | openrouter | `3.50` | `0.66` | `0.53` | *Elysium Elixir* * | Nebula's Edge | NeuralSky |
| **llama-2-7b** | fireworks | `0.95` | `0.25` | `0.25` | *Elysium Elixir* * | Orbital Oasis | *Neural Nexus Innovations* * |
|  | lepton | `1.92` | `0.33` | `0.30` | *Quantum Elixir* * | Orbital Oasis | NeuralSpark |
|  | deepinfra | `2.17` | `0.43` | `0.34` | *NebulaZenith* * | Galactic Haven | NovaMind |
|  | anyscale | `4.25` | `0.97` | `1.99` | *Mystic Elixir* * | Nebulon-9 | NeuralSphere |
| **mistral-7b** | perplexity | `0.37` | `0.31` | `0.30` | *Quantum Elixir* * | *Cosmic Nebula Nexus* * | *Quantum Cortex* * |
|  | together | `0.66` | `0.35` | `302.63` | *Hypernova* * | *Starlight Citadel* * | **FAIL** |
|  | deepinfra | `1.06` | `0.27` | `0.38` | Radiance | Seraphim One | Synthe Excellence |
|  | octo | `0.95` | `557.72` | `0.91` | *Elysium Elixir* * | *Starlight Citadel* * | *NeuroPulse Technologies* * |
|  | anyscale | `1.72` | `2.03` | `1.84` | Nano-Peak | 'Cosmos-A | Neural Boost |
| **mistral-large** | mistral | `0.42` | `0.97` | `0.23` | **FAIL** | **FAIL** | **FAIL** |
|  | openrouter | `2.94` | `0.79` | `1.04` | *ElysiumX* * | Stellar Sanctuary | NeuralNexus Solutions |
| **mistral-medium** | mistral | `0.44` | `0.48` | `3.00` | NeuroXcelerate | Nebula's Haven | *Quantum Synapse* * |
|  | openrouter | `0.92` | `3.59` | `0.94` | NeuroXcelerate | *Stellar Apex* * | NeuronFlare |
| **mistral-small** | mistral | `0.88` | `0.32` | `2.60` | *Elysium Nexus* * | Stardust Oasis | *Quantum Cortex* * |
|  | openrouter | `2.10` | `1.36` | `2.59` | *Elysium Prime* * | *Celestial Haven* * | *QuantumSynapse* * |
| **mistral-tiny** | mistral | `1.37` | `0.77` | `1.22` | *Xenon Bliss* * | *Galaxy Goliath* * | *Quantum Cortex* * |
|  | openrouter | `1.57` | `1.64` | `0.71` | *Elysium Starlight* * | *Galactic Pinnacle* * | *NeuralNova* * |
| **mixtral-8x7b** | groq | `4.16` | `0.84` | `0.25` | *Elysium Stardust* * | Stardust Oasis | *Neural Nova* * |
|  | perplexity | `1.06` | `0.22` | `0.55` | *Elysium Elixir* * | Stardust Oasis | *NeuralNimbus* * |
|  | together | `0.36` | `0.52` | `4.25` | AquaVitality | Galactic Nexus" | *NeuralNova* * |
|  | fireworks | `1.06` | `0.45` | `0.17` | *Quantum Bliss* * | *Galactic Titanium Sanctuary* * | QuantumSynapse |
|  | lepton | `0.62` | `0.28` | `0.24` | *Miracle Elixir* * | Starlight Citadel | Quantum Synapse Labs |
|  | deepinfra | `0.97` | `1.16` | `0.54` | *Galaxy Surge* * | *Celestial Haven* * | *Neural Synergy* * |
|  | octo | `1.08` | `1.24` | `2.05` | *AstraZenora* * | *Starlight Bastion* * | *NeuraByte* * |
|  | anyscale | `2.32` | `1.25` | `1.70` | *Quantum Elixir* * | Stardynamo Voidpulse | Quantum Synapse |
|  | openrouter | `1.55` | `0.73` | `0.84` | NebulaPulse | Galactic Harmony | EvolvAI |
| **openchat-3.5** | openrouter | `0.75` | `0.48` | `0.52` | Elysian Nexus | Celestial Odyssey | NeuroSynergy |
| **openchat-7b** | together | `0.72` | `0.59` | `1.67` | EuphoriaX | Nebula Nexus | QuantumMind |
| **phind-34b** | together | `0.48` | `2.97` | `0.42` | NovaSeren | Quantum Orbital Habitat | AIDynamic |
|  | deepinfra | `0.55` | `0.31` | `0.29` | Cerebrozon | **FAIL** | **FAIL** |
|  | openrouter | `0.84` | `0.84` | `0.82` | TempestTranquil | MeteorStellar | AIdeationInnovations |
| **pplx-70b** | perplexity | `2.05` | `1.05` | `2.10` | *ElysiumX* * | **Ascendant Horizon** | *NeuroNimbus* * |
|  | openrouter | `2.81` | `1.62` | `3.09` | *Elysium Elixir* * | Galactron Destinium | *Neural Nexus* * |
| **pplx-7b** | perplexity | `1.11` | `0.80` | `1.01` | Neurologine | Orbiton One | NeuralGenesis |
|  | openrouter | `3.72` | `1.10` | `1.45` | *Astral Elixir* * | Nexus One | ZenithIntel |
| **qwen-72b** | together | `1.73` | `0.41` | `0.28` | *Hypernova* * | Stellar Nexus | NeuroVerse |
| **yi-34b** | together | `3.56` | `0.25` | `1.33` | *ChronoSync* * | Galactic Nexus | CrystalClearAI |
|  | deepinfra | `0.50` | `0.34` | `0.38` | **FAIL** | S | AI Mastery |
|  | openrouter | `0.98` | `1.34` | `50.45` | *Elysium Glow* * | UltraBright StarCrystalSpaceStation | *Quantum Cortex* * |

*&nbsp; *Responses in italics were long and rambling, and the names shown above had to be extracted from the text by GPT-4*

`Table generated 3/8/2024`

