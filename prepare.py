import pandas as pd
from itertools import chain
from tqdm import tqdm
import sys


def position(row):
    method, bugs, normals = row['method'], row['bugs'], row['normals']
    items = []
    # method = re.sub(r'(\s+)([<>])(\s+)([<>])(\s+)([<>])(\s+)', r'\1\2\4\6\3\5\7', code)
    for bug in eval(bugs):
        items.append({"id": row.name, "method": method, "target": bug, "label": 1})
    for normal in eval(normals):
        items.append({"id": row.name, "method": method, "target": normal, "label": 0})
    return items


def convert_data():
    all_data = pd.read_csv('data/dataset_all.csv')
    data = all_data.apply(lambda x: position(x), axis=1)
    data = list(chain.from_iterable(data))
    df = pd.DataFrame(data)
    df.to_csv('data/dataset.csv', index=False)


def remove():
    csv_data = pd.read_csv('data/dataset_final.csv', chunksize=1000)
    chunks = []
    for n, chunk in enumerate(csv_data):
        print(n)
        chunks.append(chunk)
        # break
    df = pd.DataFrame(pd.concat(chunks))

    df.drop_duplicates(subset=['method', 'cfg', 'target', 'node'], inplace=True)

    data = []
    groups = df.groupby(['method'], sort=False)
    for _, group in tqdm(groups):
        buggy = group[group['label'] == 1]
        non_buggy = group[group['label'] == 0]
        if len(buggy) > 0:
            data.append(buggy)
        if len(non_buggy) > 0:
            data.append(non_buggy.sample(n=1))
    data = pd.concat(data)

    data.to_csv('data/dataset_final.csv', index=False)


def split():
    csv_data = pd.read_csv('data/dataset_final.csv', chunksize=1000)
    chunks = []
    for n, chunk in enumerate(csv_data):
        print(n)
        chunks.append(chunk)
        # break
    df = pd.DataFrame(pd.concat(chunks))

    df = df.sample(frac=1, random_state=3)
    total = len(df)
    fraction = int(total*0.1)
    train, valid, test = df.iloc[:fraction*8, :], df.iloc[fraction*8: fraction*9, :], df.iloc[fraction*9:, :]

    train.to_csv('data/train.csv', index=False)
    valid.to_csv('data/valid.csv', index=False)
    test.to_csv('data/test.csv', index=False)


if __name__ == "__main__":
    option = eval(sys.argv[1])
    if option == 0:
        convert_data()
    elif option == 1:
        remove()
        split()
