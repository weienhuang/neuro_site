from django.db import models
from djangotoolbox.fields import EmbeddedModelField
from django_mongodb_engine.contrib import MongoDBManager
from djangotoolbox.fields import ListField
from djangotoolbox.fields import DictField
from bson import ObjectId
# Create your models here.

class NeuroToxin(models.Model):
	sourceid = models.CharField(max_length=30)
	text = models.TextField()
	sourcedb = models.CharField(max_length=200)
	denotations = ListField()
	objtype = ListField()
	
	objects = MongoDBManager()

class MedLine(models.Model):
	Title = models.CharField(max_length=200)
	URL = models.CharField(max_length=50)
	Description = models.CharField(max_length=200)
	ShortDetails = models.CharField(max_length=200)
	EntrezUID = models.CharField(max_length=30)
	objtype = ListField()

	objects = MongoDBManager()

class Relation(models.Model):
	pmid = models.CharField(max_length=30)
	entity_front = DictField()
	entity_back = DictField()
	relation_type = models.CharField(max_length=200)
