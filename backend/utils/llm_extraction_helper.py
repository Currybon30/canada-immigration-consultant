def clean_generation(text: str) -> str:
    if "<|im_start|>assistant" in text:
        text = text.split("<|im_start|>assistant")[1]
    if "<|im_end|>" in text:
        text = text.split("<|im_end|>")[0]
    return text.strip()