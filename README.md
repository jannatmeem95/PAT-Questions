This is the repo containing PAT-Questions.

The data is stored in `data` folder. Currently two snapshots of data is provided under two different subfolders in the `data` folder.  `Dec2023` contains the gold annotated data on Dec 30, 2023 Wikidata and  `Dec2021` contains the gold annotated data on Dec 30, 2021 Wikidata.

To get the updated answers/annotations to the PAT-Questions based on the present Wikidata at any point in time, run the following command:

`./scripts/update_answers.sh $MONTHYEAR`

Here, `$MONTHYEAR` is a command line input representing the subfolder containing the existing data. Currently the only valid options are: `Dec2023` and `Dec2021`. 
The updated answers will be stored in a new folder named the present `MONTHYEAR` i.e. `February2024`.
