# Detecting Condition-related Bugs with Control Flow Graph Neural Network
This repo includes the code and dataset for the paper published at ISSTA 2023. Automated bug detection is essential for high-quality software development and has attracted much attention over the years. Among the various bugs, previous studies show that the condition expressions are quite error-prone and the condition-related bugs are commonly found in practice. Traditional approaches to automated bug detection are usually limited to compilable code and require tedious manual effort. Recent deep learning-based work tends to learn general syntactic features based on Abstract Syntax Tree (AST) or apply the existing Graph Neural Networks over program graphs. However, AST-based neural models may miss important control flow information of source code, and existing Graph Neural Networks for bug detection tend to learn local neighbourhood structure information. Generally, the condition-related bugs are highly influenced by control flow knowledge, therefore we propose a novel CFG-based Graph Neural Network (CFGNN) to automatically detect condition-related bugs, which includes a graph-structured LSTM unit to efficiently learn the control flow knowledge and long-distance context information. We also adopt the API-usage attention mechanism to leverage the API knowledge. To evaluate the proposed approach, we collect real-world bugs in popular GitHub repositories and build a large-scale condition-related bug dataset. The experimental results show that our proposed approach significantly outperforms the state-of-the-art methods for detecting condition-related bugs.
## Requirements
* Python 3.6
* pandas 0.20.3
* pytorch 1.3.1
* torchtext 0.4.0
* tqdm 4.30.0
* scikit-learn 0.19.1
* javalang 0.11.0
* Apache Maven 3.3.9
* Java 1.8.0_282

## Data
The data is stored in the file data/dataset_all.csv (extracted from data/dataset_all.zip), whose form is as follows:

|id                                             |method          |bugs  |normals |
| ------ | ------ | ------ | ------ | 
|1  |void saveDownloadInfo(BaseDownloadTask task) {... | [(617, 663)]  | [(264, 277), (362, 375), (462, 475)] | 

Here bugs and normals denote the positions of buggy and non-buggy condition expressions in the method.      


## How to run
1. `python prepare.py 0` 
2. `cd spoon/`
3. `mvn compile`
4. `mvn exec:java -Dexec.mainClass="fr.inria.controlflow.Main" -Dexec.args="../data/dataset_final.csv ../data/dataset_final.csv"`
5. `python prepare.py 1`
6. `cd CFGNNN/`
7. `python preprocess.py train valid test`
8. `python annotation.py train valid test`
9. `python main.py`



 
