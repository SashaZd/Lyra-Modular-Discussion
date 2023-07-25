import itertools
from . import ViewManager, OODManager, AgentManager
from ..models import View, ObjectOfDiscussion, Topic, Agent
from rest_framework import status
from copy import deepcopy
from statistics import mean, median, mode, StatisticsError
import jenkspy
import numpy as np

from collections import defaultdict

def startDiscussion(request, data={}, run_id=None): 
	response_data = []
	participant_ids = data.get('participants', [])
	time_duration = data.get('time_duration', None)
	ood_id = data.get('ood', None)
	topic_id = data.get('topic', 0)

	if not participant_ids or not time_duration or not (ood_id or topic_id):
		return {"errors":"Need at least one participant, time_duration > 1, and either an ObjectOfDiscussion ID or Topic ID.", "status":status.HTTP_400_BAD_REQUEST}

	initial_views = ViewManager.get_initial_discussion_views(participants=participant_ids, ood_id=ood_id, topic_id=topic_id)
	

	
	discussion = LyraDiscussion(initial_views)
	final_views = discussion.initiate_group_discussion(1)

	response_data = [view.getResponseData() for view in final_views]

	return response_data


class LyraDiscussion(object): 
	"""docstring for LyraDiscussion"""

	g_id = itertools.count().__next__

	def __init__(self, views=[], contemplation=False):
		"""Init for the discussions
		Arguments:
		views: View[]
		"""
		super(LyraDiscussion, self).__init__()
		self.id = LyraDiscussion.g_id()
		self.contemplation = contemplation

		# How many groups of opinions are formed by the clustering process based on the similarity of the opinions
		# If number of groups formed < NSI then the public opinion on the topic has been formed. 
		self.NSI_THR = 2  # Normative social influence threshold
		self.UNC_THR = 0.8
		self.ood = views[0].ood

		# Add the article view to the discussion to convince people
		ood_view = ViewManager.make_ood_view(self.ood.id)
		views.append(ood_view)

		self.original_views = deepcopy(views)
		self.views = deepcopy(views)
		
		self.topic = views[0].topic
		self.journal = []

	def add_to_journal(self, message): 
		# self.journal.append(message)
		print(message)


	def initiate_group_discussion(self, duration:int=5):
		# participants = [person for person in self.group]

		# self.discussion = Discussion(self.old_views, participants)
		# self.discussion.article = self.article
		self.duration = duration
		self.add_to_journal("------- Discussion #%s Details --------" % (self.id))
		self.add_to_journal("%d debate participants: #%s" % (len(self.views), ', '.join([str(view.agent) for view in self.original_views])))
		self.add_to_journal("Discussion on %s" % (self.topic))
		self.add_to_journal("Debating merits of article, %s"%(self.ood.title))
		self.add_to_journal("""The %s participants were given the article to read, and %s rounds to discuss the same."""
			 % (len(self.views), self.duration))

		self.get_current_group_knowledge()
		
		for minute in range(self.duration):
			self.add_to_journal("\n----- Round %s -----" % (minute+1))
			self.discuss()

		return self.views

	def get_current_group_knowledge(self):
		self.add_to_journal("\n----- FAMILIARITY WITH THE ISSUE -------")
		
		for view in self.views: 
			self.add_to_journal("\nAgent:%s" % (view.agent.id))
			self.add_to_journal(AgentManager.get_knowledge_on_topic(view.agent, self.topic))
		self.add_to_journal("------------------------------------\n")

	def discuss(self):
		self.view_grouping = self.find_best_grouping_of_opinions()
		
		if not self.contemplation:
			self.add_to_journal("\nINSTRUCTION: Participants were asked to make a short argument to persuade the other debaters to adopt their position.")
			self.add_to_journal("\nINSTRUCTION: Participants were asked to select all debaters whose arguments resonated with them.")
			self.add_to_journal("\n%s groups of like minded individuals formed:" % (self.get_actual_cluster_count()))


	def get_actual_cluster_count(self):
		""" Don't want to include the article as a view group at the moment """ 
		num_clusters = len(self.view_grouping.keys())

		for mean, group in self.view_grouping.items():
			if len(group) == 1 and ViewManager.is_ood_view(group[0]):
				num_clusters -= 1
		return num_clusters


	def find_best_grouping_of_opinions(self):
		def small_grouping_opinions():
			# if(len(opinions) < 2):
			# 	return 0    
			self.views.sort(key=lambda x: x.opinion)
			# opinions.sort()
			maximumGap = 0
			split = 0

			for i in range(len(opinions) - 1):
				if(maximumGap < (self.views[i + 1].opinion - self.views[i].opinion)):
					maximumGap = self.views[i + 1].opinion - self.views[i].opinion
					split = self.views[i].opinion
			groups = [[view for view in self.views if view.opinion <= split], [view for view in self.views if view.opinion > split]]
			view_grouping = defaultdict(list)
			# participant_grouping = defaultdict(list)
			for group in groups:
				if len(group) > 0: 
					mean_group = round(mean([view.opinion for view in group]), 2) 
					view_grouping[mean_group] = group
					# for index, op in enumerate(opinions): 
					# 	if op in group: 
					# 		participant_grouping[mean_group].append(self.views[index])

			# print(opinion_grouping, participant_grouping)
			return view_grouping #, participant_grouping


		def get_classified_ops(zone_indices, participants=False):
			if not participants: 
				array_sort = [np.array([self.views[index] for index in zone]) for zone in zone_indices if zone]
				return array_sort

			else:
				# array_sort = [[opinions[index] for index in zone] for zone in zone_indices if zone]
				views_sort = [[self.views[index] for index in zone] for zone in zone_indices if zone]
				# sorted polygon stats --- sorted array
				opinion_grouping = defaultdict(list)
				# participant_grouping = defaultdict(list)
				for zone in views_sort: 
					mean_op = round(mean([view.opinion for view in zone]), 2)
					opinion_grouping[mean_op] = zone
					# participant_grouping[mean_op] = views_sort[index]

				# print(opinion_grouping)
				return opinion_grouping #, participant_grouping


		def goodness_of_variance_fit(nclasses):

			# Breaks will include the min/max of the data 
			# 3 is the min num_classes that is taken into the breaks --> i.e. produces 2 classes 
			classes = jenkspy.jenks_breaks(opinions, n_classes=nclasses)

			# Do actual classification
			classified = np.array([classify(i, classes) for i in opinions])

			# max values of zones
			maxz = max(classified)

			# nested list of zone indices
			zone_indices = [[idx for idx, val in enumerate(classified) if zone + 1 == val] for zone in range(maxz)]

			array_sort = get_classified_ops(zone_indices)

			# sum of squared deviations from array mean
			sdam = np.sum((opinions - np.mean(opinions)) ** 2)

			# sum of squared deviations of class means
			opinion_grouping = [np.array([view.opinion for view in view_group]) for view_group in array_sort]	
			sdcm = sum([np.sum((classified - classified.mean()) ** 2) for classified in opinion_grouping])

			# goodness of variance fit
			gvf = (sdam - sdcm) / sdam

			return gvf, zone_indices

		def classify(value, breaks):
			for i in range(1, len(breaks)):
				if value <= breaks[i]:
					return i
			return len(breaks) - 1


		gvf = 0.0
		nclasses = 2
		opinions = [view.opinion for view in self.views]

		if len(opinions) <= 3:
			return small_grouping_opinions()
			

		# Goodness of fit set to 0.9
		best_gvf = 0.0
		best_zone_indices = None
		while nclasses < len(opinions) and gvf < 0.9:
			gvf, zone_indices = goodness_of_variance_fit(nclasses)
			if gvf > best_gvf: 
				best_gvf = gvf
				best_zone_indices = zone_indices

			nclasses += 1

		# print("GVF for clustering: ", best_gvf)
		return get_classified_ops(best_zone_indices, participants=True)




