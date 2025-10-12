import json, os
from openai import OpenAI
client = OpenAI(base_url=os.environ["NIM_API_BASE"], api_key=os.environ["NIM_API_KEY"])
VLM_MODEL = os.environ.get("NIM_VLM_PARSER_MODEL","nvidia/nemoretriever-parse")

def parse_page_markdown_bbox(image_b64: str):
    r = client.chat.completions.create(
        model=VLM_MODEL,
        tools=[{"type":"function","function":{"name":"markdown_bbox"}}],
        messages=[{"role":"user","content":[{"type":"image_url","image_url":{"url": image_b64}}]}],
        max_tokens=4096
    )
    tool_call = r.choices[0].message.tool_calls[0]
    return json.loads(tool_call.function.arguments)  # blocks with text/type/bbox
