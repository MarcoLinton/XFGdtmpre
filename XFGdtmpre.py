import createFunctions as cf
import os
## Check dependencies in 'createFunctions.py' before using

## User should define database details
config = {
		'user': 'root',
		'password': '',
		'host': 'localhost',
		'database': 'bitcoinsubboards',
		##'use_pure': False,
		'get_warnings': True,
		'raise_on_warnings': True,
		}
		
		
## Dates should be in this format:
## start = '2010-01-01 00:00:00'
## end = '2016-08-10 00:00:00'

## Granularity should be in this format:
## datetime.timedelta(days = 1) or relativedelta(months = 1)

## All files will be created in the same filePath
## Files created:
## 		metadata.dat 	- file containing metadata
##		-seq.dat	 	- file containing info on time slices for the dtm
##		dictionary.dict	- python object which contains id to word mappings
##		vocabulary.dat	- file containing words in the dictionary in human readable format, position maps to id
##		-mult.dat		- sparse matrix representation of documents

## Parameters
filePath 	= '//Bitcointalk'
start 		= '2009-11-21 00:00:00'
end 		= '2016-08-10 00:00:00'
granularity = cf.relativedelta(days = 14)
table 		= 'bitcointalk'

timeStamps 	= cf.getStamps(start, end, granularity)
meta = cf.createMeta(filePath, timeStamps, table, config)
seq = cf.createSeq(filePath, timeStamps)
dic = cf.createDictionary(filePath)

## Reduce or modify the dictionary as needed here, original and reduced are saved
dictionary 	= cf.corpora.Dictionary().load(os.path.join(filePath, 'dictionary.dict'))
dictionary.filter_extremes(no_below = 10, no_above = 0.1, keep_n = 10000)
dictionary.compactify()
dictionary.save(os.path.join(filePath, 'dictionaryReduced.dict'))

with open(os.path.join(filePath, 'vocabularyReduced.dat'), 'w') as voc_file :
	for word in dictionary.values():
		voc_file.write(word + '\n')

with open(os.path.join(filePath, 'dfs.dat'), 'w') as dfs :
	for freq in dictionary.dfs.values() :
		dfs.write(str(freq) + '\n')

mult = cf.createMult(filePath, 'dictionaryReduced.dict')

if meta and seq and dic and mult :
	print("Input for the dynamic topic model was created successfully, all appropriate files are in yuor specified filepath")
else :
	print("One or more files weren't created, check filepath")


#### Download code from https://github.com/blei-lab/dtm
#### Now all files are ready to apply dynamic topic model, example run from terminal:
## ./main --ntopics=200 --mode=fit --model=dtm --rng_seed=0 --initialize_lda=true  --corpus_prefix=data/ 
## --outname=data/output --top_chain_var=0.5 --alpha=4 --lda_sequence_min_iter=6 --lda_sequence_max_iter=20
## --lda_max_em_iter=20





