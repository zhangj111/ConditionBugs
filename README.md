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


## Qualitative Analysis
In order to gain a further understanding of our approach, we randomly select 100 samples from the bugs it finds in testset and manually analyze and categorize them.
Through the analysis, we summarize that the top-3 common condition-related bugs are as follows:
1. Wrong Elements in Single Condition(48%). It means that there are wrong code elements used in a single condition.  For example, an API call is wrongly invoked or the bound of a variable  is incorrect.
```
List readOptions(Element e) {
        List result = new ArrayList();
        
        Node n = e.getFirstChild();
        while (n != null) {
-            if (n.getNodeType() == Node.ELEMENT_NODE && n.getNodeName().equals("option")) {
+            if (n.getNodeType() == Node.ELEMENT_NODE && n.getNodeName().equalsIgnoreCase("option")) {
                Element optionElem = (Element)n;
                
                String label = collectText(optionElem);
                Attr valueAttr = optionElem.getAttributeNode("value");
                String value;
                if (valueAttr == null) {
                    value = label;
                } else {
                    value = valueAttr.getValue();
                }
                
                if (label != null) {
                    Option option =  new Option();
                    option.setLabel(label);
                    option.setValue(value);
                    if (isSelected(optionElem)) {
                        option.setSelected(true);
                    }
                    result.add(option);
                }
            }
            
            n = n.getNextSibling();
        }
        
        return result;
    }
```
2. Insufficient Condition(17%). It means that additional conditions should be combined to ensure the right output. For example, a special case should be considered to avoid NullPointerException.
```
void updateCount(String s) {
-	if (!DashDownloadMapsFragment.this.isAdded()){
+	if (!DashDownloadMapsFragment.this.isAdded() ||
+				getMyApplication() == null){
		return;
	}
	File ms = getMyApplication().getAppPath(s);
	if (ms.exists()) {
		File[] lf = ms.listFiles();
		if (lf != null) {
			for (File f : ms.listFiles()) {
				if (f.getName().endsWith(IndexConstants.BINARY_MAP_INDEX_EXT)) {
					size += f.length();
					countMaps++;
				}
			}
		}
	}
}
```
3. Wrong Target of Condition Construction(17%). It means that the condition is basically  incorrect and should be replaced with a very different condition. For example, replacing the boolean condition with an object. 
```
void onPublish(Datum datum, RaftPeer source) throws Exception {
        RaftPeer local = peers.local();
        if (StringUtils.isBlank(datum.value)) {
            Loggers.RAFT.warn("received empty datum");
            throw new IllegalStateException("received empty datum");
        }

        if (!peers.isLeader(source.ip)) {
            Loggers.RAFT.warn("peer(" + JSON.toJSONString(source) + ") tried to publish " +
                    "data but wasn't leader, leader: " + JSON.toJSONString(getLeader()));
            throw new IllegalStateException("peer(" + source.ip + ") tried to publish " +
                    "data but wasn't leader");
        }

        if (source.term.get() < local.term.get()) {
            Loggers.RAFT.warn("out of date publish, pub-term: "
                    + JSON.toJSONString(source) + ", cur-term: " + JSON.toJSONString(local));
            throw new IllegalStateException("out of date publish, pub-term:"
                    + source.term.get() + ", cur-term: " + local.term.get());
        }

        local.resetLeaderDue();

        Datum datumOrigin = RaftCore.getDatum(datum.key);

        if (datumOrigin != null && datumOrigin.timestamp.get() > datum.timestamp.get()) {
            // refuse operation:
            Loggers.RAFT.warn("out of date publish, pub-timestamp:"
                    + datumOrigin.timestamp.get() + ", cur-timestamp: " + datum.timestamp.get());
            return;
        }

        // do apply
        if (datum.key.startsWith(UtilsAndCommons.DOMAINS_DATA_ID) || UtilsAndCommons.INSTANCE_LIST_PERSISTED) {
            RaftStore.write(datum);
        }

        RaftCore.datums.put(datum.key, datum);

-        if (datum.key.startsWith(UtilsAndCommons.DOMAINS_DATA_ID)) {
+        if (increaseTerm) {
            if (isLeader()) {
                local.term.addAndGet(PUBLISH_TERM_INCREASE_COUNT);
            } else {
                if (local.term.get() + PUBLISH_TERM_INCREASE_COUNT > source.term.get()) {
                    //set leader term:
                    getLeader().term.set(source.term.get());
                    local.term.set(getLeader().term.get());
                } else {
                    local.term.addAndGet(PUBLISH_TERM_INCREASE_COUNT);
                }
            }
            RaftStore.updateTerm(local.term.get());
        }

        notifier.addTask(datum, Notifier.ApplyAction.CHANGE);

        Loggers.RAFT.info("data added/updated, key=" + datum.key + ", term: " + local.term);
    }
```


## Catching bugs in the wild
|  Project   | Path    | Location (Line Number)| Issue|
|  ----  | ----  |----|  ----  | 
|Dlink  | [dlink-metadata/dlink-metadata-mysql/src/main/java/com/dlink/metadata/convert/MySqlTypeConvert.java](https://github.com/DataLinkDC/dinky/blob/9d09d2a8efbe40d4cb84e1774890925aefe66207/dlink-metadata/dlink-metadata-mysql/src/main/java/com/dlink/metadata/convert/MySqlTypeConvert.java#L62) | (62, 62)  | Fixed |
|Dlink  | [dlink-admin/src/main/java/com/dlink/service/impl/TaskServiceImpl.java](https://github.com/DataLinkDC/dlink/blob/9d09d2a8efbe40d4cb84e1774890925aefe66207/dlink-admin/src/main/java/com/dlink/service/impl/TaskServiceImpl.java#L794) | (794, 794)  | Fixed |
|Dlink  | [dlink-admin/src/main/java/com/dlink/<br>service/impl/CatalogueServiceImpl.java](https://github.com/DataLinkDC/dlink/blob/9d09d2a8efbe40d4cb84e1774890925aefe66207/dlink-admin/src/main/java/com/dlink/service/impl/CatalogueServiceImpl.java#L206) | (206, 206)  | The stop condition should be i <= catalogueNames.length - 1  |
|Dlink  | [dlink-core/src/main/java/com/dlink/<br>explainer/trans/OperatorTrans.java](https://github.com/DataLinkDC/dlink/blob/9d09d2a8efbe40d4cb84e1774890925aefe66207/dlink-core/src/main/java/com/dlink/explainer/trans/OperatorTrans.java#L112)| (112, 112) | If fieldStr equals to "AS" or FIELD_AS, then fieldNames = ["AS"], which is an invalid fieldName |
|Log4j  | [log4j-api-test/src/test/java/org/apache/logging/log4j/message/MapMessageTest.java](https://github.com/apache/logging-log4j2/blob/7fde2599121113b93ba3331e05740ac691f1ef74/log4j-api/src/main/java/org/apache/logging/log4j/message/ParameterFormatter.java#L488) | (488, 488)  | Fixed | 
|Log4j  | [log4j-core/src/main/java/org/apache/logging/<br>log4j/core/appender/routing/RoutingAppender.java](https://github.com/apache/logging-log4j2/blob/7fde2599121113b93ba3331e05740ac691f1ef74/log4j-core/src/main/java/org/apache/logging/log4j/core/appender/routing/RoutingAppender.java#L308)| (308, 308)  |  node.getType() could be null  | 
|Log4j  | [log4j-core/src/test/java/org/apache/logging/<br>log4j/core/appender/rolling/RollingAppenderCountTest.java](https://github.com/apache/logging-log4j2/blob/7fde2599121113b93ba3331e05740ac691f1ef74/log4j-core/src/test/java/org/apache/logging/log4j/core/appender/rolling/RollingAppenderCountTest.java#L67)| (67, 67)  |  Should check the accessibility of the path  | 
|Log4j  | [log4j-flume-ng/src/main/java/org/apache/logging/<br>log4j/flume/appender/FlumePersistentManager.java](https://github.com/apache/logging-log4j2/blob/7fde2599121113b93ba3331e05740ac691f1ef74/log4j-flume-ng/src/main/java/org/apache/logging/log4j/flume/appender/FlumePersistentManager.java#L511)| (511, 511)	 |  Variable "shutdown" might not have been initialized  | 
|Log4j  | [log4j-flume-ng/src/main/java/org/apache/logging/<br>log4j/flume/appender/FlumePersistentManager.java](https://github.com/apache/logging-log4j2/blob/7fde2599121113b93ba3331e05740ac691f1ef74/log4j-flume-ng/src/main/java/org/apache/logging/log4j/flume/appender/FlumePersistentManager.java#L637)| (637, 637)	 |  batchSize == 1 should also be considered  | 
|Gephi  | [modules/ImportPlugin/src/main/java/org/gephi/io/processor/plugin/DefaultProcessor.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/ImportPlugin/src/main/java/org/gephi/io/processor/plugin/DefaultProcessor.java#L102)| (102, 102)	 |  Fixed  | 
|Gephi  | [modules/DesktopProject/src/main/java/org/gephi/desktop/project/ProjectControllerUIImpl.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/DesktopProject/src/main/java/org/gephi/desktop/project/ProjectControllerUIImpl.java#L269)| (269, 269)	 |  Fixed  | 
|Gephi  | [modules/DesktopWindow/src/main/java/org/gephi/desktop/progress/ProgressTicketImpl.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/DesktopWindow/src/main/java/org/gephi/desktop/progress/ProgressTicketImpl.java#L196)| (196, 196)	 |  Fixed  | 
|Gephi  | [modules/ImportPlugin/src/main/java/org/gephi/io/importer/plugin/file/ImporterDOT.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/ImportPlugin/src/main/java/org/gephi/io/importer/plugin/file/ImporterDOT.java#L166)| (166, 168)	 |  Fixed  |
|Gephi  | [modules/ProjectAPI/src/main/java/org/<br>gephi/project/io/LoadTask.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/ProjectAPI/src/main/java/org/gephi/project/io/LoadTask.java#L113)| (113, 113)	 |  It can match an invalid file name "Workspace__xml"  | 
|Gephi  | [modules/VisualizationImpl/src/main/java/org/gephi/<br>visualization/bridge/DataBridge.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/VisualizationImpl/src/main/java/org/gephi/visualization/bridge/DataBridge.java#L166)| (166, 166)	 |  This used to cause a workspace change [issue](https://github.com/gephi/gephi/commit/32ecb18e20e95adfaaeea4b45d62084f72370a93) | 
|Gephi  | [modules/DataLaboratoryAPI/src/main/java/org/gephi/<br>datalab/impl/GraphElementsControllerImpl.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/DataLaboratoryAPI/src/main/java/org/gephi/datalab/impl/GraphElementsControllerImpl.java#L273)| (273, 273)	 |  Should also check another edge direction | 
|Gephi  | [modules/ImportPlugin/src/main/java/org/gephi/<br>io/importer/plugin/file/ImporterGEXF.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/ImportPlugin/src/main/java/org/gephi/io/importer/plugin/file/ImporterGEXF.java#L1004)| (1004, 1004)	 | classAtt could be null | 
|Gephi  | [modules/ImportAPI/src/test/java/org/gephi/io/<br>importer/impl/ElementDraftTest.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/ImportAPI/src/test/java/org/gephi/io/importer/impl/ElementDraftTest.java#L77)| (77, 77)	 | message can be miss-matched when using API "String.contains()" | 
|Gephi  | [modules/AppearanceAPI/src/main/java/org/gephi/<br>appearance/RankingImpl.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/AppearanceAPI/src/main/java/org/gephi/appearance/RankingImpl.java#L75)| (75, 75) | Should check if value in the range(minValue, maxValue) first | 
|Gephi  | [modules/UIComponents/src/main/java/org/gephi/<br>ui/components/splineeditor/SplineDisplay.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/UIComponents/src/main/java/org/gephi/ui/components/splineeditor/SplineDisplay.java#L280)| (280, 280) | yPos is always a negative value | 
|Gephi  | [modules/LayoutPlugin/src/main/java/org/gephi/<br>layout/plugin/forceAtlas2/ForceAtlas2.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/LayoutPlugin/src/main/java/org/gephi/layout/plugin/forceAtlas2/ForceAtlas2.java#L215)| (215, 215) | If the edge weight is 0, this could be illegal | 
|Gephi  | [modules/LayoutPlugin/src/main/java/org/gephi/<br>layout/plugin/forceAtlas2/ForceAtlas2.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/LayoutPlugin/src/main/java/org/gephi/layout/plugin/forceAtlas2/ForceAtlas2.java#L300)| (300, 300) | May cause divide-by-zero error | 
|Gephi  | [modules/LayoutPlugin/src/main/java/org/gephi/<br>layout/plugin/forceAtlas2/ForceAtlas2.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/LayoutPlugin/src/main/java/org/gephi/layout/plugin/forceAtlas2/ForceAtlas2.java#L301)| (301, 301) | speedEfficiency could less than minSpeedEfficiency if speedEfficiency *= 0.5 | 
|Gephi  | [modules/DesktopBranding/src/main/java/org/gephi/<br>branding/desktop/MemoryStarvationManager.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/DesktopBranding/src/main/java/org/gephi/branding/desktop/MemoryStarvationManager.java#L185)| (185, 185) | homepath could be null if System.getProperty returns null |
|Gephi  | [modules/FiltersPlugin/src/main/java/org/gephi/<br>filters/plugin/graph/EgoBuilder.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/FiltersPlugin/src/main/java/org/gephi/filters/plugin/graph/EgoBuilder.java#L121)| (121, 121) | Should also check n.getId() as the following statement does|
|Gephi  | [modules/FiltersPlugin/src/main/java/org/gephi/<br>filters/plugin/operator/INTERSECTIONBuilder.java](https://github.com/gephi/gephi/blob/6bd9b5ddf316db85ff92864f2748ecbd13817369/modules/FiltersPlugin/src/main/java/org/gephi/filters/plugin/operator/INTERSECTIONBuilder.java#L154)| (154, 154) | Should not break when just encountering one non-evaluated node|


 
