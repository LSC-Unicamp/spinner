import urllib.request, json

key = 'e97767e5bdb0489cb79f3dceba66dc5c.MlV3W2bIKG4yWcLzM9RWau_f'
models = ['gemma4:31b', 'gpt-oss:20b', 'deepseek-v4-flash:0731', 'deepseek-v4-flash:preview', 'minimax-m2.7']

for model in models:
    payload = json.dumps({
        'model': model,
        'stream': False,
        'messages': [{'role': 'user', 'content': 'Say OK'}]
    }).encode()
    req = urllib.request.Request(
        'https://ollama.com/api/chat',
        data=payload,
        headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'},
        method='POST',
    )
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
            print(f'OK  {model}: {data["message"]["content"][:40]}')
    except urllib.error.HTTPError as e:
        print(f'ERR {model}: HTTP {e.code}')
    except Exception as e:
        print(f'ERR {model}: {str(e)[:60]}')
