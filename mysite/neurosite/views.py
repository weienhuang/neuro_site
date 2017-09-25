# Create your views here.
from django.shortcuts import render
import requests
from pymongo import MongoClient
from bson import ObjectId
import pymongo
from .models import NeuroToxin, MedLine

def index(request, page = None):
	if page == None:
		page = 1
	else:
		page = int(page)

	# Get current page data
	medline_list = MedLine.objects.raw_query({'$and':[{'objtype':{'$all':['Chemical', 'Disease']}}, {'bestmatch':True}]}).order_by('id')[(page-1)*10:(page)*10]
	# uri = "mongodb://ehang:12345677@140.117.69.70:30241/Pattern"
	# client = MongoClient(uri)
	# db = client.Pattern
	# collection = db.neurosite_medline
	# medline_list = list(collection.find({'$and':[{'objtype':{'$all':['Chemical', 'Disease']}}, {'bestmatch':True}]}))[(page-1)*10:(page)*10]

	# Page setting
	startpage = page - 5
	if startpage < 1:
		startpage = 1
	page_range = range(startpage, startpage + 10)
	prepage = page - 1
	if prepage < 1:
		prepage = 1
	nextpage = page + 1

	# Build context
	context = {
		'page': page,
		'prepage': prepage,
		'nextpage': nextpage,
		'page_range': page_range,
		'medline_list': medline_list,
	}
	return render(request, 'neurosite/index.html', context)


def detail(request, page, pmid):
	getFromDB = NeuroToxin.objects.raw_query({'sourceid':pmid})
	neighbor = getNeighbor(pmid)
	if len(getFromDB) == 0:
		url = 'https://www.ncbi.nlm.nih.gov/CBBresearch/Lu/Demo/RESTful/tmTool.cgi/BioConcept/'+pmid+'/PubTator'
		result = requests.get(url)
		result = result.text
		# raw data format: 
		#=================================================
		# pmid|t|tile \n
		# pmid|a|abstract \n
		# pmid \t start \t end \t name \t type \t id \n...
		#=================================================
		# The 'start' recorded in NER list represents the entity is start from '''title''' to the index of this number
		
		# Remove \n
		result = result.replace('\n', '')
		# Strip first pmid
		result = result.strip(pmid)
		# Split by pmid
		result_list = result.split(pmid)
		# Divide into different data types
		title = result_list[0].strip('|t|')
		abstract = result_list[1].strip('|a|')
		entities = [entity.strip('\t').split('\t') for entity in result_list[2:]]

		# Combine abstract that will be displayed in template
		title_len = len(title)
		display_abst = ''
		for i in range(len(entities)):
			if int(entities[i][0]) > title_len:
				if len(display_abst) == 0 :
					display_abst += abstract[0: int(entities[i][0]) - title_len -1]
				else:
					display_abst += abstract[int(entities[i-1][1]) - title_len -1 : int(entities[i][0]) - title_len -1]

				if entities[i][3] == 'Disease':
					color = 'text-danger'
				elif entities[i][3] == 'Species':
					color = 'text-warning'
				elif entities[i][3] == 'Chemical':
					color = 'text-info'
				elif entities[i][3] == 'Gene':
					color = 'text-success'
				else:
					color = 'text-primary'

				display_abst += '<font class="'+color+'">'+entities[i][2]+'</font>'
		if len(display_abst) == 0:
			display_abst = abstract
		else:
			display_abst += abstract[int(entities[-1][1]) - title_len -1 : ]
	else:
		temp_title = MedLine.objects.get(EntrezUID = pmid).Title
		title_len = len(temp_title)
		title_start = 0
		title = ''

		temp_abst = getFromDB[0].text
		display_abst = ''
		abst_start = 0

		entities = list()
		test_entities = list()
		for entity in getFromDB[0].denotations:
			if entity['span']['begin'] < title_len:
				title += temp_title[title_start: entity['span']['begin']]
				objtype = entity['obj'].split(':')[0]

				if objtype == 'Disease':
					color = 'text-danger'
				elif objtype == 'Species':
					color = 'text-warning'
				elif objtype == 'Chemical':
					color = 'text-info'
				elif objtype == 'Gene':
					color = 'text-success'
				else:
					color = 'text-primary'

				title += '<font class="'+color+'">'+temp_title[entity['span']['begin']: entity['span']['end']]+'</font>'
				title_start = entity['span']['end']

				mention = temp_title[entity['span']['begin']: entity['span']['end']]
				entities.append([entity['span']['begin'], entity['span']['end'], temp_title[entity['span']['begin']: entity['span']['end']], entity['obj'].split(':')[0], entity['obj'].split(':')[1]])
			else:
				display_abst += temp_abst[abst_start: entity['span']['begin']]
				objtype = entity['obj'].split(':')[0]

				if objtype == 'Disease':
					color = 'text-danger'
				elif objtype == 'Species':
					color = 'text-warning'
				elif objtype == 'Chemical':
					color = 'text-info'
				elif objtype == 'Gene':
					color = 'text-success'
				else:
					color = 'text-primary'

				display_abst += '<font class="'+color+'">'+ temp_abst[entity['span']['begin']: entity['span']['end']]+'</font>'
				abst_start = entity['span']['end']

				mention = temp_abst[entity['span']['begin']: entity['span']['end']]
				entities.append([entity['span']['begin'], entity['span']['end'], temp_abst[entity['span']['begin']: entity['span']['end']], entity['obj'].split(':')[0], entity['obj'].split(':')[1]])

			check = 0
			for e in test_entities:
				if e['conceptid'] == entity['obj'].split(':')[1]:
					e['mention'] = list(set(e['mention']+[mention]))
					check = 1
					break
			if check == 0:
				new_entity = {'type':entity['obj'].split(':')[0], 'mention':[mention], 'conceptid':entity['obj'].split(':')[1]}
				test_entities.append(new_entity)
		title += temp_title[title_start:]
		display_abst += temp_abst[abst_start:]

	context = {
		'page': page,
		'title': title,
		'neighbor': neighbor,
		'display_abst': display_abst,
		'entities': entities,
		'test_entities': test_entities
	}
	return render(request, 'neurosite/detail.html', context)

def getNeighbor(pmid):
	uri = "mongodb://ehang:12345677@140.117.69.70:30241/Pattern"
	client = MongoClient(uri)
	db = client.Pattern
	collection = db.neurosite_medline
	objid = collection.find_one({"EntrezUID": pmid},{'_id': 1})
	next_count = MedLine.objects.raw_query({'$and':[{'objtype':{'$all':['Chemical', 'Disease']}}, {'bestmatch':True},{"_id": { "$gte": ObjectId(objid['_id'])}}]}).count()
	prev_count = MedLine.objects.raw_query({'$and':[{'objtype':{'$all':['Chemical', 'Disease']}}, {'bestmatch':True},{"_id": { "$lte": ObjectId(objid['_id'])}}]}).count()

	if next_count == 1:
		next_pmid = 0
		next_page = 0
	else:
		next_article = MedLine.objects.raw_query({'$and':[{'objtype':{'$all':['Chemical', 'Disease']}}, {'bestmatch':True},{"_id": { "$gt": ObjectId(objid['_id'])}}]})
		next_pmid = next_article[0].EntrezUID
		next_page = (prev_count-1+1)/10 + 1

	if prev_count == 1:
		prev_pmid = 0
		prev_page = 0
	else:
		prev_article = MedLine.objects.raw_query({'$and':[{'objtype':{'$all':['Chemical', 'Disease']}}, {'bestmatch':True},{"_id": { "$lt": ObjectId(objid['_id'])}}]}).order_by('-id')
		prev_pmid = prev_article[0].EntrezUID
		prev_page = (prev_count-1-1)/10 + 1

	neighbor = {'prev_page': prev_page, 'prev_pmid': prev_pmid, 'next_page':next_page, 'next_pmid': next_pmid}
	return neighbor