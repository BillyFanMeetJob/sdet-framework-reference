# toolkit/funlib.py

def normalize(text:str|None)->str:
    """
    防止text是None時噴錯
    """
    return str(text or "").strip()
