import mysql.connector
from gensim import corpora
from nltk.tokenize import RegexpTokenizer
from nltk.corpus import stopwords, wordnet
from nltk.tag.perceptron import PerceptronTagger
from nltk.stem.wordnet import WordNetLemmatizer
from timeit import default_timer as timer
from dateutil.relativedelta import relativedelta
import datetime
import time
import re
import os
import csv



## Helper function ##
## Takes a start date, an end date and a granularity and returns vector
## of dates
def getStamps(start, end, granularity) :
    vecDate = [start]
    
    start 	= datetime.datetime.strptime(start, '%Y-%m-%d %H:%M:%S')
    end 	= datetime.datetime.strptime(end, '%Y-%m-%d %H:%M:%S')
   
    nextTime = start + granularity
    while nextTime <= end :
        vecDate.append(nextTime.strftime('%Y-%m-%d %H:%M:%S'))
        nextTime = nextTime + granularity
    
    return vecDate


	
## Helper function ##
## Takes start and end timestamps, file connection and database config as inputs 
## and returns appropriate documents
def intervalPosts(start, end, dat_outfile, table, config) :

	startTime 	= timer()
	
	cnx 		= mysql.connector.connect(**config)
	cursor 		= cnx.cursor()
	
	## select post texts and metainfo between specified dates
	query 		= "SELECT * FROM " + table + " WHERE datetime < '" + end + "' AND datetime >= '" + start + "';"
	
	cursor.execute(query)
	
	tokenizer 	= RegexpTokenizer('[a-z][a-z-]+[a-z]')
	lemmatizer 	= WordNetLemmatizer()
	stoplist 	= set(stopwords.words('english'))
	stoplist 	|= {'http', 'https', 'com', 'www', 'org'}
	tagger = PerceptronTagger()
	
	print("Results between " + start + " and " + end + " starting")
	
	counter 	= 0
	
	for line in cursor:
	
		
		if line[4] == None :
			content = line[5]
		else :
			content = ' '.join([line[4], line[5]])
		
	
		##content = line[4]
		
		if content == None :
			continue
		if line[7] == None :
			quotes = str(None)
		else :
			quotes = line[7].encode('utf-8')
		if line[6] == None :
			links = str(None)
		else :
			links = line[6].encode('utf-8')
		
		## start preprocessing here
		
		content = tokenizer.tokenize(content.lower())
		
		tagged = tagger.tag(content)
		
		tagged = [word for word, tag in tagged if tag[0] == 'N' or tag[0] == 'F'] ## or word in specVocab]
		content = [lemmatizer.lemmatize(word) for word in tagged]
		
		content = ' '.join([word for word in content if word not in stoplist])
		
		if len(content) < 20:
			continue
		
		try :
			id 		 = str(line[0])
			postid 	 = str(line[1])
			datetime = line[2].encode('utf-8')
			username = line[3].encode('utf-8')
			content  = str(content)
		except :
			print 'Encoding error occured'
			continue
	
		dat_outfile.write(id + '\t' + postid +
						'\t' + datetime + '\t' + username
						+ '\t' + content + '\t' + links
						)
	
		dat_outfile.write('\n')
		
		counter += 1
		if counter % 20000 == 0 & counter :
			print(str(counter) + ' documents preprocessed')
			

	cursor.close()
	cnx.close()
	
	endTime = timer()
	timed 	= endTime - startTime
	print("Done. " + str(counter) + " posts processed in: ")
	print(str(timed) + " seconds" + '\n')
	return counter
	

## Takes a list of time stamps, a file path, a MySQL table name and
## a database config as input and creates the metadat file, metadata.dat
def createMeta(filePath, timeStamps, table, config) :

	with open(os.path.join(filePath, 'metadata.dat'),'w') as dat_outfile :

		dat_outfile.write('id' + '\t' + 'postid' + '\t' + 'datetime' + '\t'
			+ 'username' + '\t' + 'posttext' + '\t' + 'postquote' + '\t' + 
			'\n')
		
		print("Metadata start")
		
		for i in xrange(len(timeStamps) - 1) :
			intervalPosts(timeStamps[i], timeStamps[i + 1], dat_outfile, table, config)
			
		print("Metadata finished" + '\n')
		
	return True
	
	
## Takes a file path, a relativedelta time granularity, a start and 
## end date in the following format: 2009-11-21 00:00:00 and creates
## the time slice file, -seq.dat
def createSeq(filePath, timeStamps) :

	print("Seq creation start")
	
	first = datetime.datetime.strptime(timeStamps[0], '%Y-%m-%d %H:%M:%S')
	last   = datetime.datetime.strptime(timeStamps[len(timeStamps) - 1], '%Y-%m-%d %H:%M:%S')
	
	with open(os.path.join(filePath, 'metadata.dat'), 'r') as open_file :
		count 		= 0
		reader 		= csv.reader(open_file, delimiter = '\t')
		
		countList 	= []

		reader.next()
		
		a = 0
		currentDown = datetime.datetime.strptime(timeStamps[a], '%Y-%m-%d %H:%M:%S')
		currentUp = datetime.datetime.strptime(timeStamps[a + 1], '%Y-%m-%d %H:%M:%S')

		for line in reader :
			
			if len(line[2]) < 19 :
				time = datetime.datetime.strptime(line[2], '%Y-%m-%d')
			else :
				time = datetime.datetime.strptime(line[2], '%Y-%m-%d %H:%M:%S')
			
			if time < first :
				raise ValueError('Metadata starts before the specified date')
			elif time > last :
				raise ValueError('Metadata goes beyond the specified date')
			
			
			if currentDown <= time < currentUp :
				count += 1
			else :
				countList.append(count)
				count = 1
				a += 1
				currentDown = datetime.datetime.strptime(timeStamps[a], '%Y-%m-%d %H:%M:%S')
				currentUp = datetime.datetime.strptime(timeStamps[a + 1], '%Y-%m-%d %H:%M:%S')
				while time >= currentUp :
					a += 1
					currentDown = datetime.datetime.strptime(timeStamps[a], '%Y-%m-%d %H:%M:%S')
					currentUp = datetime.datetime.strptime(timeStamps[a + 1], '%Y-%m-%d %H:%M:%S')
					countList.append(0)
				
	
	if count != 1 :
		countList.append(count)

	with open(os.path.join(filePath, '-seq.dat'), 'w') as seq_file :
		seq_file.write(str(len(countList)) + '\n')
		for c in countList :
			seq_file.write(str(c) + '\n')
			
	print("Seq file created")
	return True
	
	
## Takes a file path as input and creates a dictionary and vocabulary
## file from the metadata file
def createDictionary(filePath) :
	print 'Dictionary and Vocabulary start'
	with open(os.path.join(filePath, 'metadata.dat'), 'r') as corpus_file :
		reader		= csv.reader(corpus_file, delimiter = '\t')
		reader.next()
		dictionary = corpora.Dictionary(line[4].split() for line in reader)
	
	## store the dictionary
	dictionary.save(os.path.join(filePath, 'dictionary.dict'))

	## save vocabulary
	with open(os.path.join(filePath, 'vocabulary.dat'), 'w') as voc_file :
		for word in dictionary.values():
			voc_file.write(word + '\n')

	print 'Dictionary and Vocabulary saved'
	return True
	
	
## Takes a file path and the dictionary file name as input and creates the mult
## file i.e. the sparse term document matrix, -mult.dat
def createMult(filePath, dictionaryFileName) :	
	dictionary 	= corpora.Dictionary().load(os.path.join(filePath, dictionaryFileName))
	docLengths = []
	
	with open(os.path.join(filePath, 'metadata.dat'), 'r') as corpus_file :
		reader 		= csv.reader(corpus_file, delimiter = '\t')
		reader.next()

		class MyCorpus(object):
			def __iter__(self):
				for line in reader:
					yield dictionary.doc2bow(line[4].split(), allow_update = False)


		print('Multfile start' + '\n')
		
		## only loads a line at a time			
		corpus_memory_friendly = MyCorpus()

		with open(os.path.join(filePath, '-mult.dat'),'w') as multFile :
			count = 1

			for vector in corpus_memory_friendly : 
				multFile.write(str(len(vector)) + ' ')
				docLengths.append(len(vector))
				for (wordID, weight) in vector : 
					multFile.write(str(wordID) + ':' + str(weight) + ' ')
				multFile.write('\n')
				if count % 20000 == 0 :
					print(str(count) + ' documents written')
				count += 1

	with open(os.path.join(filePath, 'docLengths.dat'), 'w') as lengths_file :
		for length in docLengths :
			lengths_file.write(str(length) + '\n')
	
	print('Multfile saved')
	return True
	
	