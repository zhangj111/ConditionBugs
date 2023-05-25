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


def annotate_api(row):
    print(row.name)
    nodes = eval(row['nodes'])

    ants = []
    for node in nodes:
        text = node
        annotation = re.findall(r'\.\s\w+\s\(', text)
        annotation = 1 if annotation else 0
        ants.append(annotation)

    return nodes, row['forward'], row['backward'], ants, row['label']


if __name__ == '__main__':
    for choice in sys.argv[1:]:
        annotation_type = 'api'
        df_chunk = pd.read_csv('data/%s.csv' % choice, chunksize=1000, encoding='utf-8')
        result = pd.DataFrame(columns=['nodes', 'forward', 'backward', 'types', 'label'])
        result.to_csv('data/%s_%s.csv' % (choice, annotation_type), index=False)
        for raw_data in df_chunk:
            raw_data.columns = ['nodes', 'forward', 'backward', 'target', 'label']
            items = raw_data.apply(annotate_api, axis=1)
            result = pd.DataFrame(data=list(items), columns=['nodes', 'forward', 'backward', 'types', 'label'])
            # result = result.sample(frac=1)
            result.to_csv('data/%s_%s.csv' % (choice, annotation_type), index=False, mode='a', header=False)


