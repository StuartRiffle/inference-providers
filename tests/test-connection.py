import sys
import os
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from inference_providers.inference_providers import ProviderList
providers = ProviderList(verbose=True, auto_update=False)


sample_subjects = ["a new party drug", "a starfighter", "an AI tech startup"]

gpt4_client, gpt4_name = providers.connect_to_model("gpt-4", verify=True)

samples = "|".join([f"...{item}?" for item in sample_subjects])
print("## What's the coolest name you can think of for...")
print(f"||Provider||||{samples}|")
print(f"|----" * (len(sample_subjects) + 5) + "|")

model_names = providers.get_canonical_names_in_use()
for model_name in model_names:
    sources = providers.find_model_providers(model_name)
    lastname = ""
    if sources:
        for connection in sources:
            id, url, canonical_name, internal_name, key = connection
            line = f"| {'**'+canonical_name+'**' if canonical_name != lastname else ''} | {id} |"
            lastname = canonical_name
            client = providers.connect_to_model_endpoint(url, key, internal_name, verify=False)
            timings = ""
            answers = ""
            for trial in sample_subjects:
                if client:
                    prompt =  f"What's the coolest name you can think of for {trial}? Reply with only the name, say nothing else."
                    start_time = time.time()
                    response = providers.get_response(client, internal_name, prompt)
                    time_desc = f"{time.time() - start_time:.2f}"
                    timings += f" `{time_desc}` |"
                    response_text = str(response).replace("\n", " ").strip()
                    response_words = response_text.split(" ")
                    response_text = " ".join(response_words[:5])
                    if len(response_words) > 5:
                        audit_prompt  = f"This prompt was given to an LLM: \"{prompt}\".\n"
                        audit_prompt += f"The response is verbatim below. It may not be well formed. Please just extract the name.\n"
                        audit_prompt += f"If there are multiple names in the output, just pick one.\n"
                        audit_prompt += f"It the LLM is barking mad and does not actually return a name, print \"FAIL\".\n"
                        audit_prompt += f"\n{response_text}"
                        response_text = "*" + str(providers.get_response(gpt4_client, gpt4_name, prompt)) + "* *"
                else:
                    response_text = ""
                    time_desc = ""
                response_text = response_text.strip('".')
                answers += f" {response_text} |"
            print(line + timings + answers)

all_connections = providers.find_all_model_providers()
skipping = True

for connection in all_connections:
    id, url, canonical_name, internal_name, key = connection
    if True:#canonical_name == "gemini-pro":
        print(f"[{id}]  {internal_name}:  ", end="", flush=True)
        response = "<<<FAIL>>>"
        start_time = time.time()
        client = providers.connect_to_model_endpoint(url, key, internal_name, verify=False)
        if client:
            response = providers.get_response(client, internal_name, "What's the coolest name possible for an AI tech startup?")
        print(f"{response} ({time.time() - start_time:.3f})")



def print_response(client, name, prompt):
    response = client.chat.completions.create(model=name, messages=[
        #{"role": "system", "content": "Just play along."},
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



