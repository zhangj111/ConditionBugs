# Detecting Condition-related Bugs with Control Flow Graph Neural Network

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



 
