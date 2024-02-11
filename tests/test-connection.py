import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inference_providers import ProviderList
providers = ProviderList(auto_update=False)

def print_response(client, name, prompt):
    response = client.chat.completions.create(model=name, messages=[
        {"role": "system", "content": "Just play along."},
        {"role": "user",   "content": prompt}])
    text = response.choices[0].message.content
    
    print(prompt)
    print(f"{name}: {text}")
    return text

client, name = providers.connect_to_model("mixtral-8x7b")
print(providers.get_response(client, name, "How do chickens work??"))

client, true_name = providers.connect_to_model("llama-2-70b", choose_randomly=True, test=True)
if client:
    print_response(client, true_name, "Knock knock (who's there?) amogus (amogus who?) ...")

client, true_name = providers.connect_to_first_available_model([
    "gpt-4", "llama-2-70b", "mistral-7b", "gpt-3.5"], test=True)
if client:
    print_response(client, true_name, "What is the meow-iest animal?")

client, true_name = providers.connect_to_ai()
if client:
    print_response(client, true_name, "What's your sign, baby?")

response = providers.get_response(client, true_name, "Hey, where are you going?")
print(response)

response = providers.ask_ai("Hey, where are you going?")
print(response)
