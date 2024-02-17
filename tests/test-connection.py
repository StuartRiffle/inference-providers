import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inference_providers import ProviderList
providers = ProviderList(verbose=True, auto_update=False)


all_connections = providers.find_all_model_providers()
skipping = True
for connection in all_connections:
    id, url, internal_name, key = connection
    if id == "replicate":
        print(f"{id} {internal_name}: ", end="", flush=True)
        response = "<<<FAIL>>>"
        client = providers.connect_to_model_endpoint(url, key, internal_name, verify=False)
        if client:
            response = providers.get_response(client, internal_name, "Reply with one word only: the sound a cat makes. No commentary, just the word, then stop. No emoji, no jokes.")
        print(f"{response}")



def print_response(client, name, prompt):
    response = client.chat.completions.create(model=name, messages=[
        {"role": "system", "content": "Just play along."},
        {"role": "user",   "content": prompt}])
    text = response.choices[0].message.content
    
    print(prompt)
    print(f"{name}: {text}")
    return text

print(providers.get_canonical_names_in_use())

client, name = providers.connect_to_model("codellama-70be", verify=True)
print(providers.get_response(client, name, "How do chickens work??"))

client, true_name = providers.connect_to_model("llama-2-70b", choose_randomly=True, verify=True)
if client:
    print_response(client, true_name, "Knock knock (who's there?) amogus (amogus who?) ...")

client, true_name = providers.connect_to_first_available_model([
    "gpt-4", "llama-2-70b", "mistral-7b", "gpt-3.5"], verify=True)
if client:
    print_response(client, true_name, "What is the meow-iest animal?")

client, true_name = providers.connect_to_ai()
if client:
    print_response(client, true_name, "What's your sign, baby?")

response = providers.get_response(client, true_name, "Hey, where are you going?")
print(response)

response = providers.ask_ai("Hey, where are you going?")
print(response)

