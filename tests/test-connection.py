import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from inference_providers import ProviderList
providers = ProviderList(verbose=True, auto_update=False)

def print_response(client, name, prompt):
    response = client.chat.completions.create(model=name, messages=[
        {"role": "system", "content": "Just play along."},
        {"role": "user",   "content": prompt}])
    text = response.choices[0].message.content
    
    print(prompt)
    print(f"{name}: {text}")
    return text

print(providers.get_canonical_model_names())

client, name = providers.connect_to_model("llama-2-7be", test=True)
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



['mistral-7b', 'mistral-medium', 'gpt-4', 'wizard-python-34b', 'mixtral-8x7b', 'codellama-34b', 'codellama-70b', 'gpt-4-turbo', 'gpt-3.5', 'llama-2-7b', 'chatgpt', 'codellama-python-34b', 'mistral-small', 'gpt-4-32k', 'codellama-python-70b', 'gemini', 'gemini-nano', 'phind-34b', 'gemini-pro', 'yi-34b', 'falcon-40b', 'llama-2-70b', 'palm', 'mistral-tiny', 'mistral']
