"""
digraph null {
node [fontsize = 8];
1 [shape=Mdiamond, label="BEGIN "];
2 [shape=rectangle, label="TRY "];
3 [shape=rectangle, label="final Accumulator<NamedAggregators> accum = AccumulatorSingleton.getInstance(jsc) "];
4 [shape=rectangle, label="Exception e "];
5 [shape=rectangle, label="final NamedAggregators initialValue = accum.value() "];
6 [shape=rectangle, label="e.print() "];
7 [shape=diamond, label="opts.getEnableSparkSinks() "];
8 [shape=rectangle, label="final MetricsSystem metricsSystem = MODULE_.get().metricsSystem() "];
9 [shape=rectangle, label="final AggregatorMetricSource aggregatorMetricSource = new AggregatorMetricSource(opts.getAppName(), initialValue) "];
10 [shape=rectangle, label="metricsSystem.removeSource(aggregatorMetricSource) "];
11 [shape=rectangle, label="metricsSystem.registerSource(aggregatorMetricSource) "];
12 [shape=doublecircle, label="EXIT "];
3 -> 4 ;
 3 -> 5 ;
 5 -> 4 ;
 8 -> 9 ;
 9 -> 10 ;
 10 -> 11 ;
 1 -> 2 ;
 2 -> 3 ;
 4 -> 6 ;
 7 -> 8 ;
 5 -> 7 ;
 6 -> 7 ;
 7 -> 12 ;
 11 -> 12 ;
 6 -> 4[style=dashed];
 }
"""

import re
import pandas as pd
import javalang
import sys


def parse_cfg(row):
    print(row.name)
    cfg, target = row['cfg'], row['node']
    node_list = []
    nodes = re.findall(r'(\d+)\s+\[shape=\w+,\s+label="([\s\S]+?)"];\n', cfg)

    for node in nodes:
        id_, text = eval(node[0]), node[1]
        try:
            tokens = [item.value for item in javalang.tokenizer.tokenize(text)]
        except Exception:
            print(text)
            exit(-1)
        statement = ' '.join(tokens) if id_ != target else '_BOS_ ' + ' '.join(tokens) + ' _EOS_'
        node_list.append(statement)
    fwd_edges = re.findall(r'(\d+) -> (\d+) ;\n', cfg)
    back_edges = re.findall(r'(\d+) -> (\d+)\[style=dashed\];\n', cfg)
    fwd_edges = [[eval(edge[0]), eval(edge[1])] for edge in fwd_edges]
    back_edges = [[eval(edge[0]), eval(edge[1])] for edge in back_edges]
    for i, edge in enumerate(fwd_edges):
        begin, end = edge
        if begin > end:
            fwd_edges[i] = [end, begin]
            node_list[begin - 1], node_list[end - 1] = node_list[end - 1], node_list[begin - 1]
            for j, link in enumerate(fwd_edges):
                if j == i:
                    continue
                begin_idx, end_idx = -1, -1
                if begin in link:
                    begin_idx = link.index(begin)
                if end in link:
                    end_idx = link.index(end)
                if begin_idx != -1:
                    link[begin_idx] = end
                if end_idx != -1:
                    link[end_idx] = begin
                fwd_edges[j] = link
            for k, back in enumerate(back_edges):
                begin_idx, end_idx = -1, -1
                if begin in back:
                    begin_idx = back.index(begin)
                if end in back:
                    end_idx = back.index(end)
                if begin_idx != -1:
                    back[begin_idx] = end
                if end_idx != -1:
                    back[end_idx] = begin
                back_edges[k] = back
    if not back_edges:
        back_edges = [[1, 1]]
    for idx, node in enumerate(node_list):
        if node.startswith('_BOS_') and node.endswith('_EOS_'):
            target = idx
    return node_list, fwd_edges, back_edges, target, row['label']


if __name__ == '__main__':
    for choice in sys.argv[1:]:
        df_chunk = pd.read_csv('../data/%s.csv' % choice, chunksize=1000, encoding='utf-8')
        result = pd.DataFrame(columns=['nodes', 'forward', 'backward', 'target', 'label'])
        result.to_csv('data/%s.csv' % choice, index=False)
        for raw_data in df_chunk:
            items = raw_data.apply(parse_cfg, axis=1)
            result = pd.DataFrame(data=list(items), columns=['nodes', 'forward', 'backward', 'target', 'label'])
            # result = result.sample(frac=1)
            result.to_csv('data/%s.csv' % choice, index=False, mode='a', header=False)

