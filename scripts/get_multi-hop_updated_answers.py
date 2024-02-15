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


def buildQuerymulti_nonlast_succeed(sub,pred):
    q = """
    SELECT ?item ?itemLabel (YEAR(?starttime) AS ?yearstarttime) ?endtime WHERE {
      wd:"""+sub+" p:"+ pred+ """ ?s  .
            ?s  ps:"""+ pred+ """ ?item .
            OPTIONAL{?s  pq:P580 ?starttime  .}
            FILTER NOT EXISTS{ ?s pq:P582 ?endtime .}.
             SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    } order by desc(?starttime)
    """
    return q

def buildQuerymulti_nonlast_succeed_special(sub,pred):
    q= """
    SELECT ?item ?itemLabel (YEAR(?starttime) AS ?yearstarttime) ?endtime WHERE {
        wd:"""+sub+" p:"+ pred+ """ ?s  .
                ?s  ps:"""+ pred+ """ ?item .
                OPTIONAL{?s  pq:P580 ?starttime  .}
                OPTIONAL{ ?s pq:P582 ?endtime .}.
                FILTER(?endtime>NOW()).
                SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    } order by desc(?starttime)
    """
    return q

def buildQuery_multi_last_P39(sub,pred):
    q = """
    SELECT ?position ?positionLabel ?item ?itemLabel
    WHERE {
    wd:"""+sub+" p:"+ pred+ """ ?s  .
    ?s  ps:"""+ pred+ """ ?position.
    ?s  pq:P580 ?start  .
    OPTIONAL {
        ?s pq:P1365 ?item.
        }
    SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
    }order by desc(?start)

    """
    return q


def buildQuery_multi_succeed_P6_P35(sub,pred):
    q = """
  SELECT ?item ?itemLabel (YEAR(?starttime) AS ?yearstarttime) (YEAR(?endtime) AS ?yearendtime) WHERE {
      wd:"""+sub+" p:"+ pred+ """ ?s  .
      ?s  ps:"""+ pred+ """ ?item .
            ?s  pq:P580 ?starttime  .
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],en". }
  } order by desc(?starttime)
  """
    return q


def process_all_succeed_P6_P35(v, intermediate_entities):
    answers = []
    sub = v['subject']['subject']
    pred = v['relations'][0]

    q = buildQuery_multi_succeed_P6_P35(sub,pred)
    results = wikidata_rest_query(q)['results']['bindings']

    #got a list, then pick the first entity found after the midsubject entity
    for mid in intermediate_entities: #v['answer']["2023"]:
        midSub = mid['ID']
        for i in range(len(results)-1):
            resID = results[i]['item']['value'].split('/')[-1]
            if resID == midSub:
                id = results[i+1]['item']['value'].split('/')[-1]
                label = results[i+1]['itemLabel']['value']
                
                answers = [{"ID": id, "Label": label}]
                break

    return answers


def process_all_last_P39(v, intermediate_entities):
    answers = []
    sub = v['subject']['subject']
    pred = v['relations'][0]

    q = buildQuery_multi_last_P39(sub,pred)
    results = wikidata_rest_query(q)['results']['bindings']

    ##if positionLabel == midSubLabel: ans itemLabel
    #got a list, then pick the first entity found after the midsubject entity
    for mid in intermediate_entities:
        if 'member of' in mid['Label'].lower():
            continue
        midSub = mid['ID']
        for res in results:
            position = res['position']['value'].split('/')[-1]
            if position == midSub:
                if 'item' in res:
                    id = res['item']['value'].split('/')[-1]
                    label = res['itemLabel']['value']
                    answers = [{"ID": id, "Label": label}]
                    break
    return answers

def process_non_last_succeed_2023(midSub,midPred):
    answers = []

    q = buildQuerymulti_nonlast_succeed(midSub,midPred)
    result_cur = wikidata_rest_query(q)['results']['bindings']
    # print(q)
    # print(result_cur)
    if len(result_cur) <1:
        q = buildQuerymulti_nonlast_succeed_special(midSub,midPred)
        # print(q)
        result_cur = wikidata_rest_query(q)['results']['bindings']
        # print(result_cur)
    if len(result_cur) <1:
      return answers

    for res in result_cur:
        id = res['item']['value'].split('/')[-1]
        label = res['itemLabel']['value']
        answers.append({"ID": id, "Label": label})
    
    return answers


def process_all_non_last_non_succeed(midPred, midSubjects):
    answers = []

    for mid in midSubjects:
        midSub = mid['ID']
        mid_answers = process_non_last_succeed_2023(midSub,midPred)
        # print(f'mid answers: {mid_answers}')
        if len(mid_answers) < 1:
            continue
        answers.extend(mid_answers)

    return answers


def collect_answers_one_hop(k,v):
    sub = v['subject']['subject']
    pred = v['relations'][0]
    intermediate_entities = []

    if 'previous' not in k and 'before' not in k:
        q=buildQuerysingle(sub, pred)
        result_cur = wikidata_rest_query(q)['results']['bindings']
        if len(result_cur) <1:
            q = buildQuerysingle_special(sub, pred)
            result_cur = wikidata_rest_query(q)['results']['bindings']
            if len(result_cur) <1:
                return intermediate_entities

        for res in result_cur:
            id = res['item']['value'].split('/')[-1]
            label = res['itemLabel']['value']
            intermediate_entities.append({"ID": id, "Label": label})
        
        return intermediate_entities

    else:
        q = buildQueryPrevious(sub, pred)
        result_prev = wikidata_rest_query(q)['results']['bindings']

        if len(result_prev) <1:
            return intermediate_entities

        id_prev_2023 = result_prev[0]['item']['value'].split('/')[-1]
        label_prev_2023 = result_prev[0]['itemLabel']['value']
        intermediate_entities.append({"ID": id_prev_2023, "Label": label_prev_2023})

        utc_time1 = datetime.fromisoformat(result_prev[0]['endtime']['value'].rstrip("Z"))
        for i in range(1,len(result_prev)):   
            utc_time2 = datetime.fromisoformat(result_prev[i]['endtime']['value'].rstrip("Z"))
            if utc_time2 >= utc_time1:
                id_prev = result_prev[i]['item']['value'].split('/')[-1]
                label_prev = result_prev[i]['itemLabel']['value']
                intermediate_entities.append({"ID": id_prev, "Label": label_prev})
                break

        return intermediate_entities



def collect_two_hop_answers(data):
    updated_data = dict()
    for k,v in tqdm(data.items()):
        # print(f'k: {k}')
        intermediate_entities = collect_answers_one_hop(k,v)
        if len(intermediate_entities) == 0:
            print('hs')
            continue

        if 'last' not in k and 'succeed' not in k:
            answers = process_all_non_last_non_succeed(v['relations'][1], intermediate_entities)
        elif 'succeed' in k:
            answers =process_all_succeed_P6_P35(v, intermediate_entities)
        elif 'last' in k:
            answers =process_all_last_P39(v, intermediate_entities)

        if len(answers) < 1:
            continue

        nItem = v.copy()
        nItem["intermediate entities"] = intermediate_entities
        nItem['text answers'] = []
        for ans in answers:
            nItem['text answers'].append(ans['Label'])

        nItem['answer annotations'] = answers
        updated_data[k] = nItem
        
    return updated_data


def main():
    if len(sys.argv) == 2:
        timestamp = sys.argv[1]
        print(f"Received argument: {timestamp}")
    else:
        print("This script requires exactly one argument.")
        return
    
    dataPath = os.path.join('../PAT-data',timestamp) + '/PAT-multihop.json'
    if not os.path.exists(dataPath):
        print('Data Path does not exist')
        return

    with open(dataPath,'r') as f:
        data = json.load(f)
    # updated_data = collect_two_hop_answers(data)

    from datetime import datetime

    # Get the current date and time
    now = datetime.now()

    # Extract the current month and year
    current_month = now.strftime("%B")
    current_year = now.year

    out_path = '../PAT-data/' + current_month + str(current_year)

    if not os.path.exists(out_path):
        os.makedirs(out_path)
    
    with open(os.path.join(out_path, 'PAT-multihop.json'),'w') as f:
        json.dump({},f,indent =6)

main()