import re

def extract_all_xml(xml_tag, raw_output):
    # Find all XML tags of the form <xml_tag>...</xml_tag> in the raw output
    # Capture the content between the tags, including multi-line content
    pattern = re.compile(f'<{re.escape(xml_tag)}>(.*?)</{re.escape(xml_tag)}>', re.DOTALL)
    matches = pattern.findall(raw_output)
    return matches
