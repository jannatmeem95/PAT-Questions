from unidecode import unidecode
from tqdm import tqdm

from urllib.request import urlopen, quote
import json
from datetime import datetime
from datetime import timezone
import sys
import os

def wikidata_rest_query(query):
    url = "https://query.wikidata.org/sparql?query=%s&format=json" % quote(query)
    with urlopen(url) as f:
        response = f.read().decode("utf-8")
    return json.loads(response)


def buildQuerysingle(sub, pred):
    q = """
    SELECT ?item ?itemLabel (YEAR(?starttime) AS ?yearstarttime) ?endtime WHERE {
        wd:"""+sub +" p:" + pred +""" ?s  .
                ?s  ps:""" + pred +""" ?item .
                ?s  pq:P580 ?starttime  .
                FILTER NOT EXISTS{ ?s pq:P582 ?endtime .}.
    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    } order by desc(?starttime)
    """
    return q

def buildQuerysingle_special(sub, pred):
    q = """
  SELECT ?item ?itemLabel (YEAR(?starttime) AS ?yearstarttime) (YEAR(?endtime) AS ?yearendtime) WHERE {
      wd:"""+sub +" p:" + pred +""" ?s  .
            ?s  ps:""" + pred +""" ?item .
            ?s  pq:P580 ?starttime  .
            ?s  pq:P582 ?endtime  .
            FILTER(?endtime>NOW()).
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
  } order by desc(?starttime)
  """
    return q

def buildQueryPrevious(sub, pred):
    q = """
    SELECT ?item ?itemLabel ?starttime ?endtime WHERE {
      wd:"""+sub +" p:" + pred +""" ?s  .
            ?s  ps:""" + pred +""" ?item .
            ?s  pq:P580 ?starttime  .
            ?s pq:P582 ?endtime .
            FILTER(?endtime <=NOW()).
    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    } order by desc(?endtime)
    """
    return q


def collect_answers_one_hop(data):
    updated_data = dict()
    extra_special=dict()

    for k,v in tqdm(data.items()):
        answers = []
        answers_special = []
        sub = v['subject']['subject']
        pred = v['relations'][0]

        if 'previous' not in k and 'before' not in k:
            q=buildQuerysingle(sub, pred)
            result_cur = wikidata_rest_query(q)['results']['bindings']
            if len(result_cur) <1:
                q = buildQuerysingle_special(sub, pred)
                result_cur = wikidata_rest_query(q)['results']['bindings']
                if len(result_cur) <1:
                    nItem = v.copy()
                    nItem['answer'] = []
                    updated_data[k] = nItem
                    continue
            text = []
            extra_special_text = []
            for res in result_cur:
                id = res['item']['value'].split('/')[-1]
                label = res['itemLabel']['value']
                answers.append({"ID": id, "Label": label})
                text.append(label)
                if 2023 - int(res['yearstarttime']['value'] ) >7:
                    extra_special_text.append(label)
                    answers_special.append({"ID": id, "Label": label})


            nItem = v.copy()
            nItem['text answers'] = text
            nItem['answer annotations'] = answers
            updated_data[k] = nItem

            specialItem = v.copy()
            specialItem['text answers'] = extra_special_text
            specialItem['answer annotations'] = answers_special
            extra_special[k] = specialItem

        else:
            q = buildQueryPrevious(sub, pred)
            result_prev = wikidata_rest_query(q)['results']['bindings']

            if len(result_prev) <1:
                nItem = v.copy()
                nItem['answer'] = []
                updated_data[k] = nItem
                continue

            text = []
            id_prev = result_prev[0]['item']['value'].split('/')[-1]
            label_prev = result_prev[0]['itemLabel']['value']
            answers.append({"ID": id_prev, "Label": label_prev})
            text.append(label_prev)

            utc_time1 = datetime.fromisoformat(result_prev[0]['endtime']['value'].rstrip("Z"))
            for i in range(1,len(result_prev)):
                utc_time2 = datetime.fromisoformat(result_prev[i]['endtime']['value'].rstrip("Z"))
                if utc_time2 >= utc_time1:
                    id_prev = result_prev[i]['item']['value'].split('/')[-1]
                    label_prev = result_prev[i]['itemLabel']['value']
                    answers.append({"ID": id_prev, "Label": label_prev})
                    text.append(label_prev)
                    break

            nItem = v.copy()
            nItem['text answers'] = text
            nItem['answer annotations'] = answers
            updated_data[k] = nItem

    print(len(updated_data))
    return updated_data, extra_special


def main():
    if len(sys.argv) == 2:
        timestamp = sys.argv[1]
        print(f"Received argument: {timestamp}")
    else:
        print("This script requires exactly one argument.")
        return
    
    dataPath = os.path.join('../PAT-data',timestamp) + '/PAT-singlehop.json'
    if not os.path.exists(dataPath):
        print('Data Path does not exist')
        return

    with open(dataPath,'r') as f:
        data = json.load(f)
    updated_data, extra_special = collect_answers_one_hop(data)
    print(f'updated data length: {len(updated_data)}')
    print(f'extra special data length: {len(extra_special)}')
    
    from datetime import datetime

    # Get the current date and time
    now = datetime.now()

    # Extract the current month and year
    current_month = now.strftime("%B")
    current_year = now.year

    out_path = '../PAT-data/' + current_month + str(current_year)

    if not os.path.exists(out_path):
        os.makedirs(out_path)
    
    with open(os.path.join(out_path, 'PAT-singlehop.json'),'w') as f:
        json.dump(updated_data,f,indent =6)

    with open(os.path.join(out_path, 'PAT-singlehop-special-attention.json'),'w') as f:
        json.dump(extra_special,f,indent =6)

main()