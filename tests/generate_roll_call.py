import sys
import os
import time

repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, os.path.join(repo_root, 'src'))

from inference_providers.inference_providers import ProviderList
providers = ProviderList(verbose=True, auto_update=False)

sample_query = "## What's the coolest name you can think of for..." 
sample_subjects = ["a new drug", "a space station", "an AI tech startup"]

gpt4_client, gpt4_name = providers.connect_to_model("gpt-4", verify=True)

samples = "|".join([f"...{item}?" for item in sample_subjects])

table = []
table.append(sample_query)
table.append(f"||||||{samples}|")
table.append(f"|----" * (len(sample_subjects) + 5) + "|")

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
                    if not response:
                        response = "**FAIL**"
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
            line += timings + answers
            table.append(line)
            print(line)

table_text  = "\n".join(table) + "\n"
table_text += "\n*&nbsp; *Responses in italics were long and rambling, and the names shown above had to be extracted from the text by GPT-4*" + "\n"
datestr = time.strftime("%Y-%m-%d %H:%M:%S")
table_text += f"\n`Table generated {datestr}`" + "\n"
table_utf8 = table_text.encode("utf-8", errors="ignore")

with open(os.path.join(repo_root, "docs/roll-call.md"), "wb") as f:
    f.write(table_utf8)
  

