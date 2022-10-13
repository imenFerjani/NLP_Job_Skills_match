# -*- coding: utf-8 -*-
"""final_research.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1n8vmwJn7CQeCbUjORBptmePn_h-bqcgz

### Mounting Google drive
"""

#from google.colab import drive
#drive.mount('/content/drive')

# Commented out IPython magic to ensure Python compatibility.
# %cd '/content/drive/My Drive/five_class_entitydata'

"""### Imports"""

import os
import spacy 
import re
import json
import random
import logging
from sklearn.metrics import classification_report
from sklearn.metrics import precision_recall_fscore_support
from spacy.gold import GoldParse
from spacy.scorer import Scorer
from sklearn.metrics import accuracy_score

"""### Converting dataturks to spacy format"""

#converting dataturks annotated data to spacy format to be 
#used as training data

def convert_dataturks_to_spacy(dataturks_JSON_FilePath):
    try:
        training_data = []
        lines=[]
        with open(dataturks_JSON_FilePath, 'r') as f:
            lines = f.readlines()

        for line in lines:
            data = json.loads(line)
            text = data['content']
            entities = []
            for annotation in data['annotation']:
                #only a single point in text annotation.
                point = annotation['points'][0]
                labels = annotation['label']
                # handle both list of labels or a single label.
                if not isinstance(labels, list):
                    labels = [labels]

                for label in labels:
                    #dataturks indices are both inclusive [start, end] but spacy is not [start, end)
                    entities.append((point['start'], point['end'] + 1 ,label))


            training_data.append((text, {"entities" : entities}))

        return training_data
    except Exception as e:
        logging.exception("Unable to process " + dataturks_JSON_FilePath + "\n" + "error = " + str(e))
        return None

"""### Cleaning data"""

############################Removes leading and trailing white spaces from entity spans.############################
# https://github.com/explosion/spaCy/issues/3558
def trim_entity_spans(data: list) -> list:
    """Removes leading and trailing white spaces from entity spans.

    Args:
        data (list): The data to be cleaned in spaCy JSON format.

    Returns:
        list: The cleaned data.
    """
    invalid_span_tokens = re.compile(r'\s')

    cleaned_data = []
    for text, annotations in data:
        entities = annotations['entities']
        valid_entities = []
        for start, end, label in entities:
            valid_start = start
            valid_end = end
            while valid_start < len(text) and invalid_span_tokens.match(
                    text[valid_start]):
                valid_start += 1
            while valid_end > 1 and invalid_span_tokens.match(
                    text[valid_end - 1]):
                valid_end -= 1
            valid_entities.append([valid_start, valid_end, label])
        cleaned_data.append([text, {'entities': valid_entities}])

    return cleaned_data

"""### Training the model"""

################### Train Spacy NER.###########
def train_spacy():
    TRAIN_DATA = convert_dataturks_to_spacy("/content/drive/My Drive/five_class,\
    _entitydata/traindata_3withmyannotation.json")
    TRAIN_DATA=trim_entity_spans(TRAIN_DATA)
    nlp = spacy.blank('en')  # create blank Language class
    # create the built-in pipeline components and add them to the pipeline
    # nlp.create_pipe works for built-ins that are registered with spaCy
    # if 'tagger' not in nlp.pipe_names:
    #      nlp.add_pipe(nlp.create_pipe('tagger'))
    if 'ner' not in nlp.pipe_names:
        ner = nlp.create_pipe('ner')
        nlp.add_pipe(ner, last=True)

       
       
    # add labels
    for _, annotations in TRAIN_DATA:
         for ent in annotations.get('entities'):
            ner.add_label(ent[2])

    # get names of other pipes to disable them during training
    other_pipes = [pipe for pipe in nlp.pipe_names if pipe != 'ner']
    with nlp.disable_pipes(*other_pipes):  # only train NER
        optimizer = nlp.begin_training()
        for itn in range(25):
            print("Statring iteration " + str(itn))
            random.shuffle(TRAIN_DATA)
            losses = {}
            for text, annotations in TRAIN_DATA:
                nlp.update(
                    [text],  # batch of texts
                    [annotations],  # batch of annotations
                    drop=0.1,  # dropout - make it harder to memorise data
                    sgd=optimizer,  # callable to update weights
                    losses=losses)
            print(losses)
    return nlp

nlp_=train_spacy()

"""### Saving the Trained model"""

# save model to output directory (with parcial cleaned data)
def save_model(output_dir):
      nlp_.to_disk(output_dir)
      print("Saved model to", output_dir)

output_dir='./model2'
save_model(output_dir)

"""### Loading the trained model instance"""

###################loading the saved model################################
 output_dir='./model2'
 nlp2 = spacy.load(output_dir)

"""### Testing"""

##############################preparing the testdata########################
examples = convert_dataturks_to_spacy("3class_test_data.json")
examples=trim_entity_spans(examples)
tp = 0
tr = 0
tf = 0

ta = 0
c = 0

#################testing the model######################
nlp_=nlp2
for text, annot in examples:

    f = open("resume"+str(c)+".txt", "w")
    doc_to_test = nlp_(text)
    d = {}
    for ent in doc_to_test.ents:
        d[ent.label_] = []
    for ent in doc_to_test.ents:
        d[ent.label_].append(ent.text)
        
    if 'Skills' in d:
      skills_=d['Skills']    
      print(f'resume {str(c)} skills {skills_}')
    # print(d.keys())

    #---------------------------      
    for i in set(d.keys()):

        f.write("\n\n")
        f.write(i + ":"+"\n")
        for j in set(d[i]):
            f.write(j.replace('\n', '')+"\n")
    #-----------------------------
    d = {}
    for ent in doc_to_test.ents:
        d[ent.label_] = [0, 0, 0, 0, 0, 0]
    for ent in doc_to_test.ents:
        doc_gold_text = nlp_.make_doc(text)
        gold = GoldParse(doc_gold_text, entities=annot.get("entities"))
        y_true = [ent.label_ if ent.label_ in x else 'Not ' +
                  ent.label_ for x in gold.ner]
        y_pred = [x.ent_type_ if x.ent_type_ ==
                  ent.label_ else 'Not '+ent.label_ for x in doc_to_test]
        if(d[ent.label_][0] == 0):
            # f.write("For Entity "+ent.label_+"\n")
            # f.write(classification_report(y_true, y_pred)+"\n")
            (p, r, f, s) = precision_recall_fscore_support(
                y_true, y_pred, average='weighted')
            a = accuracy_score(y_true, y_pred)
            d[ent.label_][0] = 1
            d[ent.label_][1] += p
            d[ent.label_][2] += r
            d[ent.label_][3] += f
            d[ent.label_][4] += a
            d[ent.label_][5] += 1
    c += 1

"""### Validating the pridiction"""

###########################validating the model##########################
for i in d:
    print("\n For Entity "+i+"\n")
    print("Accuracy : "+str((d[i][4]/d[i][5])*100)+"%")
    print("Precision : "+str(d[i][1]/d[i][5]))
    print("Recall : "+str(d[i][2]/d[i][5]))
    print("F-score : "+str(d[i][3]/d[i][5]))

"""### matcher"""

import pandas as pd
from pathlib import Path

nlp_=nlp2

def find_skills(text):
  d = {}
  docx=nlp_(text)
  for ent in docx.ents:
    d[ent.label_] = []
  for ent in docx.ents:
    d[ent.label_].append(ent.text)
  if 'Skills' in d:
    skills_=d['Skills']    
    return skills_
  else:
    return None

"""### Creating job list"""

# create jobs list
jobs=[]
job_dir='/content/drive/My Drive/five_class_entitydata/jobs'
pathlist = Path(job_dir).glob('**/*.txt')
for path in pathlist:
    with open (path, "r") as fileHandler:
      job={
          'name':path.name,
           'skills':find_skills(''.join(fileHandler.readlines()))
      }
      jobs.append(job)

print(jobs[1]['name'])
print(jobs[1]['skills'])
print(jobs[2]['name'])
print(jobs[2]['skills'])
print(jobs[3]['name'])
print(jobs[3]['skills'])
print(jobs[4]['name'])
print(jobs[4]['skills'])

"""### Creating cv list"""

# create cvs list
cvs=[]
cv_dir='/content/drive/My Drive/five_class_entitydata/cv'
pathlist = Path(cv_dir).glob('**/*.txt')
for path in pathlist:
    with open (path, "r") as files:
      cv={
          'name':path.name,
           'skills':find_skills(''.join(files.readlines()))
      }
      cvs.append(cv)

print(cvs[1]['name'])
print(cvs[1]['skills'])
print(cvs[2]['name'])
print(cvs[2]['skills'])
print(cvs[3]['name'])
print(cvs[3]['skills'])
print(cvs[4]['name'])
print(cvs[4]['skills'])
print(cvs[5]['name'])
print(cvs[5]['skills'])

"""### Matching both list cv and jobs"""

def job_match(text,cv=True):
  skills=find_skills(text)
  matched=[]
  if cv:
    for job in jobs:
      nskill_job=len(job['skills'])
      count=0
      for skill in skills:
        if skill in job['skills']:
          count+=1
      matched.append({
          'name':job['name'],
          'pct':count/nskill_job*100,
          'job_skill':job['skills'],
          'cv_skill':skills

      })
  else:
    for cv in cvs:
      nskill_cv=len(cv['skills'])
      count=0
      for skill in skills:
        if skill in cv['skills']:
          count+=1
      matched.append({
          'name':cv['name'],
          'pct':count/nskill_cv*100,
          'job_skill':cv['skills'],
          'cv_skill':skills

      })
  return matched

"""### Finding Most Matching Job"""

# find most matching jobs
#######################reading the file from folder######################
f = open('/content/drive/My Drive/five_class_entitydata/cv/r1.txt', 'r')
text = f.read()
match_jobs=job_match(text)
match_jobs = sorted(match_jobs, key=lambda k: k['pct'],reverse=True)

for i in range(3):
  print(f"cv matching with {match_jobs[i]['name']}")
  print(f"{match_jobs[i]['pct']}")

"""### Finding Most Matching Resumes"""

# find most matching cv
#######################reading the file from folder######################
f = open('/content/drive/My Drive/five_class_entitydata/jobs/dataengineer.txt', 'r')
text = f.read()
match_cvs=job_match(text,cv=False)
match_cvs = sorted(match_cvs, key=lambda k: k['pct'],reverse=True)

for i in range(10):
  print(f"job matching with cv {match_cvs[i]['name']}")
  print(f"{match_cvs[i]['pct']}")

"""### Cleanups"""

##################################### delete produced resume files
i=10
while i < 30:
  print ("resume"+str(i)+".txt")
  if os.path.isfile("resume"+str(i)+".txt"):
    print ("found")
    path = "resume"+str(i)+".txt" 
    os.remove(path)
    print ("deleted")
    print ("..........")
  else:
    print ("not found")
  i+=1

###################deleting the saved model#################################
#  !rm -rf model2

"""### xxxxx"""

###################loading the saved model################################
 output_dir='./model2'
 nlp2 = spacy.load(output_dir)

#######################reading the file from folder######################
f = open('/content/drive/My Drive/five_class_entitydata/feed1.txt', 'r')
text = f.read()
# text="im competent in java,c# and python"
# text=cleandata(text)

docx=nlp2(text)
d = {}
for ent in docx.ents:
  d[ent.label_] = []
for ent in docx.ents:
  d[ent.label_].append(ent.text)
if 'Skills' in d:
  skills_=d['Skills']    
  print(f'Dedected skills {skills_}')

#########################viewving the results####################
from spacy import displacy
displacy.render(nlp_, style='ent',jupyter=True)