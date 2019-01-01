
import numpy as np


def _read(path, args):
    with open(path, 'r') as fp:
        content = fp.read()

    for k, v in args.items():
        content = content.replace(f"%{k}", str(v))

    return content

def _flatten_array(data):
    data = np.multiply(data, 255.0)
    data = data.astype(np.uint8)
    data = data[:, ::-1]
    return data
