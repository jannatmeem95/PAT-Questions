This is the repo containing PAT-Questions.

The data is stored in `data` folder. Currently two snapshots of data is provided under two different subfolders in the `data` folder.  `Dec2023` contains the gold annotated data on Dec 30, 2023 Wikidata and  `Dec2021` contains the gold annotated data on Dec 30, 2021 Wikidata.

To get the updated answers/annotations to the PAT-Questions based on the present Wikidata at any point in time, run the following command:

`./scripts/update_answers.sh $MONTHYEAR`

Here, `$MONTHYEAR` is a command line input representing the subfolder containing the existing data. Currently the only valid options are: `Dec2023` and `Dec2021`. 
The updated answers will be stored in a new folder named the present `MONTHYEAR` i.e. `February2024`.


## Dataset Description

`data/Dec2023` and `data/Dec2021` folder each contains two files `PAT-singlehop.json` and `PAT-multihop.json` comprising the single and multi-hop questions respectively annotated for that timestamp.

`PAT-singlehop.json` and `PAT-multihop.json` contains PAT-questions indexed by the unique `question`.
Each item in the `json` files contain seven common fields associated:

`question`: The natural language question, 

`subject`: A dictionary containing the Wikidata ID and natural language label of the subject, [{`subject`: WikiID, `subLabel`: Label}],

`text answers`: Contains the natural language answers to the question, 

`answer annotations`: Contains a list of dictionaries each representing the Wikidata ID and natural language label of a candidate answer, {`ID`: WikiID, `Label`: Label},

`relations`: Contains the Wikidata property/properties needed to build SPARQL queries,

`template`: source PAT-Questions template, and 

`uniq_id`: A unique ID of the question
 
 Multi-hop questions have an extra field,
 
 `intermediate entities`: Contains a list of dictionaries each representing the Wikidata ID and natural language label of an intermediate entity/ answer to the one-hop question, [{`subject`: WikiID, `subLabel`: Label}]
