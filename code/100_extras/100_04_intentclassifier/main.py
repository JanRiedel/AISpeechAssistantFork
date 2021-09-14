import spacy
from spacy.util import minibatch, compounding
import time
import random
from sklearn.metrics import classification_report
import os
import string

# Todo remove puctuation, try other models
#https://github.com/rsreetech/TextClassificationWithSpacy/blob/master/TweetTextClassificationWithSpacy.ipynb
TRAINING_DATA = {
	'sentences': [
		'Wie spät ist es?',
		'Wie spät ist es in Berlin?',
		'Wie viel Uhr ist es in Tokyo?',
		'Wie spät ist es in New York?',
		'Wie spät ist es jetzt in London?',
		'Wie viel Uhr ist es jetzt?',
		'Wie spät haben wir es?',
		'Uhrzeit?',
		'Sag mir wie spät es ist.',
		'Wie spät?',
		'Sagst du mir die Uhrzeit?',
		'Sag mir bitte die Uhrzeit.',
		'Ich wüsste gerne wie spät es ist.',
		'Wie spät haben wir es in Köln?',
		
		'Spiele Musik von Peter Maffay.',
		'Spiele die Ärzte.',
		'Bitte spiele Jazz.',
		'Spiele Radio Regenbogen.',
		'Mache Musik an.',
		'Spiele Musik von Pink.',
		'Musik aus den Charts.',
		'Spiele klassische Musik.',
		'Bitte spiele Kinderlieder.',
		'Spiele Punkrock.'		
	],
	'intents': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
}

TEST_DATA = {
	'sentences': [
		'Wie spät ist es in San Francisco?',
		'Wie viel Uhr haben wir es?',
		'Spiele Musik von der Kelly Family.',
		'Sag mal wie spät es ist!',
		'Spiele bitte schöne Musik',
		'Spiele meine Playlist',
		'Wie viel Uhr haben wir es in München?'
	],
	'intents': ['time','time','music', 'time', 'music', 'music', 'time']
}

def Sort(sub_li): 
  
	# reverse = True (Soresulting_list = list(first_list)rts in Descending  order) 
	# key is set to sort using second element of  
	# sublist lambda has been used 
	return(sorted(sub_li, key = lambda x: x[1],reverse=True))  

# run the predictions on each sentence in the evaluation  dataset, and return the metrics
def evaluate(tokenizer, textcat, test_texts, test_cats ):
	docs = (tokenizer(text) for text in test_texts)
	preds = []
	for i, doc in enumerate(textcat.pipe(docs)):
		#print(doc.cats.items())
		scores = Sort(doc.cats.items())
		#print(scores)
		catList=[]
		for score in scores:
			catList.append(score[0])
		preds.append(catList[0])
		
	labels = ['time', 'music']
	
	print(classification_report(test_cats,preds,labels=labels))

def train(train_data, iterations, test_texts,test_cats, model_arch, dropout = 0.3, model=None,init_tok2vec=None):
	nlp = spacy.load("de_core_news_sm")
	
	# add the text classifier to the pipeline if it doesn't exist
	# nlp.create_pipe works for built-ins that are registered with spaCy
	if "textcat" not in nlp.pipe_names:
		textcat = nlp.create_pipe(
			"textcat", config={"exclusive_classes": True, "architecture": model_arch}
		)
		nlp.add_pipe(textcat, last=True)
		
	# otherwise, get it, so we can add labels to it
	else:
		textcat = nlp.get_pipe("textcat")

	# add label to text classifier
	textcat.add_label("time")
	textcat.add_label("music")

	# get names of other pipes to disable them during training
	pipe_exceptions = ["textcat", "trf_wordpiecer", "trf_tok2vec"]
	other_pipes = [pipe for pipe in nlp.pipe_names if pipe not in pipe_exceptions]
	with nlp.disable_pipes(*other_pipes):  # only train textcat
		optimizer = nlp.begin_training()
		if init_tok2vec is not None:
			with init_tok2vec.open("rb") as file_:
				textcat.model.tok2vec.from_bytes(file_.read())
		print("Training the model...")
		print("{:^5}\t{:^5}\t{:^5}\t{:^5}".format("LOSS", "P", "R", "F"))
		batch_sizes = compounding(16.0, 64.0, 1.5)
		for i in range(iterations):
			print('Iteration: '+str(i))
			start_time = time.perf_counter()
			losses = {}
			# batch up the examples using spaCy's minibatch
			random.shuffle(train_data)
			batches = minibatch(train_data, size=batch_sizes)
			for batch in batches:
				texts, annotations = zip(*batch)
				nlp.update(texts, annotations, sgd=optimizer, drop=dropout, losses=losses)
			with textcat.model.use_params(optimizer.averages):
				# evaluate on the test data 
				evaluate(nlp.tokenizer, textcat, test_texts, test_cats)
			print ('Elapsed time '+str(time.perf_counter() - start_time)+  " seconds")
		with nlp.use_params(optimizer.averages):
			modelName = model_arch+"_model"
			filepath = os.path.join(os.getcwd(), modelName)
			nlp.to_disk(filepath)
	return nlp
	
if __name__ == '__main__':

	train_texts = [d.lower() for d in TRAINING_DATA['sentences']]
	train_cats = TRAINING_DATA['intents']
	final_train_cats=[]
	for cat in train_cats:
		cat_list = {'time': 1 if cat == 1 else 0, 'music': 1 if cat == 0 else 1}
		#if cat == 1:
		#	cat_list['time'] =  1
		#	cat_list['calendar'] =  0
		#else:
		#	cat_list['time'] =  0
		#	cat_list['calendar'] =  1
		final_train_cats.append(cat_list)
		
	training_data = list(zip(train_texts, [{"cats": cats} for cats in final_train_cats]))
	
	test_texts = [d.lower() for d in TEST_DATA['sentences']]
	test_cats = TEST_DATA['intents']
	
	print(test_texts)
	print(test_cats)
	
	nlp = train(training_data, 10, test_texts, test_cats, "ensemble")
	
	test1 = "Wie spät ist es?"
	test2 = "Spiele Musik von Blink 182."
	nlp2 = spacy.load(os.path.join(os.getcwd(), "ensemble_model"))
	doc2 = nlp2(test1)
	print("Text: "+ test1)
	print(doc2.cats)
	
	doc3 = nlp2(test2)
	print("Text: "+ test2)
	print(doc3.cats)