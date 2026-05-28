# HuggingFace Model Size Check (pre-download)

Before downloading a large model, check actual file sizes via HF API to estimate transfer time and disk usage.

## Basic file listing

```bash
curl -s "https://huggingface.co/api/models/USER/REPO" | python3 -c "
import json,sys
d=json.load(sys.stdin)
total=0
for f in d.get('siblings',[]):
    n=f['rfilename']
    sz=f.get('size',0)
    if sz>1024**3:
        print(f'{n}: {sz/(1024**3):.1f} GB')
        total+=sz
    elif sz>1024**2:
        print(f'{n}: {sz/(1024**2):.1f} MB')
        total+=sz
print(f'---\\nTotal: {total/(1024**3):.2f} GB')
```
