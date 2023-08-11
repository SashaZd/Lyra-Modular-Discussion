import itertools
import random
from collections import defaultdict
from copy import deepcopy
from math import exp, fabs
from statistics import mean

import jenkspy  # noqa: E401
import numpy as np
from rest_framework import status

from ..models import ObjectOfDiscussion, Topic, View
from . import AgentManager, ViewManager


def startDiscussion(request, data={}, run_id:int=None): 
	"""
	Function: startDiscussion
	Summary: Starts Discussion Amongst Participants. Discussions can only occur on ObjectOfDiscussions not Topics
	Examples: InsertHere
	Attributes: 
		@param (request):Request Object
		@param (data) default={}: {participants:[1,2], time_duration:5, ood:2}
		@param (run_id) int=None: Run ID
	Returns: InsertHere
	"""
	response_data = []
	participant_ids = data.get('participants', [])
	time_duration = data.get('time_duration', None)
	ood_id = data.get('ood', None)

	if not participant_ids or not time_duration or not ood_id:
		return {"errors":"Need at least one participant, time_duration >= 1, and an ObjectOfDiscussion ID.", "status":status.HTTP_400_BAD_REQUEST}
  
	try: 
		ood = ObjectOfDiscussion.objects.get(id=ood_id)
		topic = ood.topic
	except ObjectOfDiscussion.DoesNotExist: 
		return {"errors":"Need valid ObjectOfDiscussion.", "status":status.HTTP_400_BAD_REQUEST}
	
	
	initial_views = ViewManager.get_initial_discussion_views(participants=participant_ids, ood=ood, topic=topic)
	
	_initial_views = []
	for eachView in initial_views: 
		_data = eachView.getResponseData()
		_initial_views.append(_data)

	discussion = LyraDiscussion(_initial_views, ood, topic)
	final_views, journal = discussion.initiate_group_discussion(time_duration)

	response_data = {
		"views": [view.getResponseData() for view in final_views if view],
		"journal": journal
	}
	
	return response_data


class LyraDiscussion(object): 
	"""docstring for LyraDiscussion"""

	g_id = itertools.count().__next__

	def __init__(self, views=[], ood:ObjectOfDiscussion=None, topic:Topic=None, contemplation=False):
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

		# Weight of the opinion of the group increases if it's a large number of people 
		# PUB_OP_NUM_AGENTS gives a max number of people in the opinion group to count it towards a strong opinion
		self.PUB_OP_NUM_AGENTS = 10
		self.ood = ood
		self.topic = topic

		# Add the article view to the discussion to convince people
		ood_view = ViewManager.make_ood_view(self.ood).getResponseData()
		ood_view["agent"] = None 
		views.append(ood_view)

		self.original_views = deepcopy(views)
		self.newer_views = deepcopy(views)
		
		self.journal = []

	def add_to_journal(self, message): 
		self.journal.append(message)


	def initiate_group_discussion(self, duration:int=5):
		self.duration = duration
		self.add_to_journal("------- Discussion #%s Details --------" % (self.id))
		self.add_to_journal("%d debate participants: # %s" % (len(self.newer_views), ', '.join(["%s"%view["agent"] for view in self.original_views if view["agent"] != None])))
		self.add_to_journal("Discussion on %s" % (self.topic))
		self.add_to_journal("Debating merits of article, %s"%(self.ood.title))
		self.add_to_journal("""The %s participants were given the article to read, and %s rounds to discuss the same."""% (len(self.newer_views), self.duration))

		self.get_current_group_knowledge()
		
		for minute in range(self.duration):
			self.add_to_journal("\n----- Round %s -----" % (minute+1))
			self.discuss()

		final_views = []
		for view in self.newer_views: 
			if view["agent"]: 
				view.pop("id")
				view["ood"] = self.ood.id
				view["topic"] = self.topic.id
				_new_view = ViewManager.add_view_data(view)

				final_views.append(_new_view)

		self.newer_views = final_views

		return self.newer_views, self.journal

	def get_current_group_knowledge(self):
		self.add_to_journal("\n----- FAMILIARITY WITH THE ISSUE -------")
		
		for view in self.newer_views: 
			if view["agent"]: 
				self.add_to_journal("\nAgent:%s" % (view["agent"]))
				self.add_to_journal(AgentManager.get_knowledge_on_topic(view["agent"], self.topic))
		self.add_to_journal("------------------------------------\n")

	
	def discuss(self):
		self.view_grouping = self.find_best_grouping_of_opinions()
		num_clusters = self.get_actual_cluster_count()
		
		if not self.contemplation:
			self.add_to_journal("\nINSTRUCTION: Participants were asked to make a short argument to persuade the other debaters to adopt their position.")
			self.add_to_journal("\nINSTRUCTION: Participants were asked to select all debaters whose arguments resonated with them.")
			self.add_to_journal("\n%s groups of like minded individuals formed:" % (num_clusters))

		newer_views = []

		if num_clusters <= self.NSI_THR:
			if not self.contemplation: 
				self.add_to_journal("Since there were only %s distinct clusters of opinions, it seemed as though Public Opinion had formed." % (num_clusters))
			
			largest_group = max(self.view_grouping.values(), key=len) 

			for view in self.newer_views: 
				if not view["agent"]: 
					newer_views.append(view)
					continue
				_new_view = self.public_opinion_formed(view, largest_group=largest_group)
				
				newer_views.append(_new_view)
				if self.contemplation: 
					break
		
		else:
			if not self.contemplation: 
				self.add_to_journal("Too many differing opinion groups present. Public Opinion not formed on the matter.")
			
			for view in self.newer_views: 
				if not view["agent"]: 
					newer_views.append(view)
					continue
				newer_views.append(self.no_public_opinion(view))
				if self.contemplation: 
					break

		self.newer_views = newer_views


	def no_public_opinion(self, view):
		"""If there are many groups, then public opinion has not formed."""

		# if not isinstance(agent_name, Person):
		# 	return view

		temp_view = deepcopy(view)
		view_data = deepcopy(view)
		# view_data.pop("id")

		mean_closest_group, closest_group = self.closest_group_to_view(view)
		_mean_closest = sum([view["opinion"] for view in closest_group]) / len(closest_group)

		view_data["opinion"] = (_mean_closest + view["attitude"]) / 2
		# max_group, min_group = max(closest_group), min(closest_group)
		# view.unc = max([fabs(op - view.opinion) for op in closest_group])
		# view = ViewManager.add_view_data(view_data, save=False)
		
		if ViewManager.is_there_change_view_data(temp_view, view_data): 
			self.template_nopubop_closer_journal(view["agent"], mean_closest_group, True)
		else:
			self.template_nopubop_closer_journal(view["agent"], mean_closest_group, False)

		return view_data


	def public_opinion_formed(self, view:dict={}, largest_group:[]=None):
		"""Public opinion is formed
			Since pub_op is formed, any agents that retain their ideas risk rejection. 
		"""
		

		# Agents with high levels of uncertainty will follow the largest groups opinions
		# temp_view = view.getResponseData()
		new_view_data = deepcopy(view)
		# new_view_data.pop("id")

		if view["uncertainty"] > self.UNC_THR:
			if not self.contemplation: 
				self.add_to_journal("Agent: #%s looked for the group with the largest majority." % (view["agent"]))
			
			self.template_highunc_journal(view["agent"])
			new_view_data["opinion"] = round(mean([eachView["opinion"] for eachView in largest_group]), 2)
			new_view_data["attitude"] = round(mean([eachView["opinion"] for eachView in largest_group]), 2)
			
			# Uncertainty changes to the max difference between this agent's opinion, and any other person in this group 
			# max_group, min_group = max([eachView["opinion"] for eachView in largest_group]), min([eachView["opinion"] for eachView largest_group])
			if len(largest_group) >= 2: 
				new_view_data["uncertainty"] = max([fabs(eachView["opinion"] - new_view_data["opinion"]) for eachView in largest_group])

		else:
			# Agent recognizes that there is a difference in it's own attitude and opinion
			# Find the group that is closest to the opinion of this agent.
			self.template_pubop_nsi_journal(view["agent"])
			mean_closest_group, closest_group  = self.closest_group_to_view(view)

			if not self.contemplation:
				self.add_to_journal("The closest group was the one with %s" % (self.template_name_group_members([eachView["agent"] for eachView in closest_group if eachView["agent"]], excludePerson=view["agent"])))


			new_view_data = self.check_normative_social_influence(view=view, opinion_group=closest_group)
			# Sasha continue here
		
		# new_view = ViewManager.add_view_data(new_view_data, save=False)
		return new_view_data


	def check_normative_social_influence(self, view:dict={}, opinion_group=[]):
		f_a = self.calculate_fa(opinion_group)
		f_b = self.calculate_fb(opinion_group)
		f_c = self.calculate_fc(opinion_group, view)

		if not self.contemplation:
			self.add_to_journal("Agent: #%s thought about whether the group opinion was strong enough." % (view["agent"]))

		# Public Opinion Strength (op_str)
		# Pressure to conform to a group's opinion increases as op_str approaches 1
		# After calculating the op_str agents decide whether or not to conform to the public opinion of the group
		op_str = (f_a + f_b + f_c) / 3

		# if not self.contemplation:
		# 	print("CSI: ", agent_name.name, f_a, op_str)
		# print(view.agent.name, op_str, f_a, f_b, f_c)
		view_data = deepcopy(self.internal_debate(view, opinion_group, op_str))
		return view_data

	# Sasha continue here....
	def internal_debate(self, view:dict={}, opinion_group:list=[], op_str:float=None):
		"""Internal Debate
			Decides whether the public opinion strength of this group is strong enough for the agent
			to change either it's attitude or its opinion
		""" 
		# Default public threshold
		view_data = deepcopy(view)
		# view_data.pop("id")

		def_val_pub_thr = 0.6

		# Using a public opinion spectrum we divide the public opinion spectrum into 3 categories: 
		# using 2 thresholds: th1, th2
		th1 = fabs(0.7 - view["uncertainty"])
		th2 = def_val_pub_thr if th1 < def_val_pub_thr else th1	  		# 0.6
		public_opinion_expressed = round(mean([eachView["opinion"] for eachView in opinion_group]), 2)

		
		if op_str < th1: 
			# op_str is too weak for this agent to follow in terms of either attitude or opinion
			# No change in agent attitude or opinion
			self.template_pubop_nsi_nochange_journal(view["agent"])
			pass

		elif op_str >= th1 and op_str < th2: 
			"""Private acceptance
				1. Agents with small uncertainty value find the op_str is strong enough to follow
					and change their expressed opinions to match. 
					Since there is now an inconsistency in the expressed opinions and the internal attitudes, 
					the agents will change their internal attitudes to match the external opinions they now express
				2. Agents with large uncertainty values find the op_str is strong enough for them to follow the
					mean opinion. However, the op_str is not strong enough for them to realize they're bending to public pressure
					Thus, they think they follow the pub_op based on their internal attitudes, and change the same to match
				3. ie. any agent in this category will change their internal attitudes and expressed op. to match the 
					mean opinion of the group
			""" 

			# if not self.contemplation: 
			# 	print(agent_name.name, "CSI: ", op_str, th1, th2, view.unc)

			if th1 < th2: 
				self.template_pubop_nsi_change_highunc_journal(view["agent"])
			else:
				self.template_pubop_nsi_change_lowunc_journal(view["agent"])

			view_data["opinion"] = public_opinion_expressed
			view_data["attitude"] = public_opinion_expressed

			# Check Wang paper for this circs.
			if len(opinion_group) >= 2: 
				view_data["uncertainty"] = max([fabs(eachView["opinion"] - view_data["opinion"]) for eachView in opinion_group])
						

		elif op_str >= th2: 
			"""Public conformity
				Public opinion strength is too large. 
				Agents conform to the public opinion with their expressed opinions for group inclusion
				However, they are aware that this doesn't change their inner attitudes
				ie. opinion of the agent changes, but attitude does not
			""" 
			self.template_pubop_nsi_conform_forced_journal(view["agent"])
			view_data["opinion"] = public_opinion_expressed
			# max_group, min_group = max(opinion_group), min(opinion_group)
			# view.unc = max([fabs(op - view.opinion) for op in opinion_group])

		view_data["opinion"] = round(view_data["opinion"], 2)
		view_data["attitude"] = round(view_data["attitude"], 2)

		return view_data


	def calculate_fa(self, opinion_group):
			"""Opinion Strength based on: Number of individuals in the opinion group"""
			x = len(opinion_group)
			if(x <= 1):
				return 0
			elif(x >= self.PUB_OP_NUM_AGENTS):
				return 1
			else: 
				size_proportion = (x / (len(self.original_views) - 1))
				return size_proportion


	def calculate_fb(self, opinion_group:list=[]):
		"""Opinion Strength based on: Group Opinion Homogenity"""
		x = 1 - np.var([view["opinion"] for view in opinion_group])
		
		# Homogenity of opinins / More variance -> less homogenity
		f_b = 1 / (1 + exp(24 * x - 6))
		return f_b


	def calculate_fc(self, opinion_group:list=[], view:dict={}):
		"""Opinion Strength based on: Discrepancy between the agent's 
		internal attitude and the mean public opinion in the group
		"""
		x = round(fabs(view["attitude"] - mean([eachView["opinion"] for eachView in opinion_group])), 2)
		return (1 / (1 + exp(-12 * x + 6)))


	def closest_group_to_view(self, view:dict={}):
		""" Returns the group with the opinion closest to this one
		""" 

		mean_closest, diff, closest_group = float("Inf"), float("Inf"), None
		for _mean, group in self.view_grouping.items():
			new_diff = abs(view["opinion"] - _mean)
			if new_diff < diff: 
				mean_closest, diff, closest_group = _mean, new_diff, group

		return mean_closest, closest_group


	def get_actual_cluster_count(self):
		""" Don't want to include the article as a view group at the moment """ 
		num_clusters = len(self.view_grouping.keys())

		for _mean, group in self.view_grouping.items():
			if len(group) == 1 and not group[0]["agent"]:
				num_clusters -= 1
		return num_clusters


	def find_best_grouping_of_opinions(self):
		def small_grouping_opinions():

			self.newer_views.sort(key=lambda x: x["opinion"])

			maximumGap = 0
			split = 0

			for i in range(len(opinions) - 1):
				if(maximumGap < (self.newer_views[i + 1]["opinion"] - self.newer_views[i]["opinion"])):
					maximumGap = self.newer_views[i + 1]["opinion"] - self.newer_views[i]["opinion"]
					split = self.newer_views[i]["opinion"]

			groups = [[view for view in self.newer_views if view["opinion"] <= split], [view for view in self.newer_views if view["opinion"] > split]]
			
			view_grouping = defaultdict(list)
			for group in groups:
				mean_group = round(mean([view["opinion"] for view in group]), 2) 
				view_grouping[mean_group] = group
					
			return view_grouping

		def get_classified_ops(zone_indices, participants=False):
			if not participants: 
				array_sort = [np.array([self.newer_views[index] for index in zone]) for zone in zone_indices if zone]
				return array_sort

			else:
				
				views_sort = [[self.newer_views[index] for index in zone] for zone in zone_indices if zone]
				
				opinion_grouping = defaultdict(list)
				
				for zone in views_sort: 
					mean_op = round(mean([view["opinion"] for view in zone]), 2)
					opinion_grouping[mean_op] = zone
					
				return opinion_grouping 

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
			opinion_grouping = [np.array([view["opinion"] for view in view_group]) for view_group in array_sort]	
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
		opinions = [view["opinion"] for view in self.newer_views]

		if len(opinions) <= 3 or len(np.unique(opinions))<2:
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

		return get_classified_ops(best_zone_indices, participants=True)


	# Templates from Lyra
	def template_name_group_members(self, group:[str], excludePerson:str=None):
		if self.contemplation: 
			return

		_group = [name for name in group if name != excludePerson]
		if len(_group) > 1:
			return "%s and %s" % (', '.join(["%s"%(name) for name in _group[:-1]]), _group[-1])
		elif len(_group) == 1:
			return _group[0]
		else:
			return "the other view(s)"

	def template_highunc_journal(self, agent_name:str=None):
		if self.contemplation: 
			return
		self.add_to_journal(random.choice(LyraDiscussion.template_pubop_highUnc) % agent_name)

	def template_pubop_nsi_journal(self, agent_name:str=None):
		if self.contemplation: 
			return
		self.add_to_journal(random.choice(LyraDiscussion.template_pubop_nsi) % (agent_name))

	def template_pubop_nsi_nochange_journal(self, agent_name):
		if self.contemplation: 
			return
		self.add_to_journal(random.choice(LyraDiscussion.template_pubop_nsi_nochange) % (agent_name))

	def template_pubop_nsi_change_highunc_journal(self, agent_name):
		if self.contemplation: 
			return
		self.add_to_journal("%s accepted that their views were outdated. Retaining their views meant risking rejection." % (agent_name))
		self.add_to_journal(random.choice(LyraDiscussion.template_pubop_nsi_change_highunc) % (agent_name))

	def template_pubop_nsi_change_lowunc_journal(self, agent_name):
		if self.contemplation: 
			return
		self.add_to_journal("%s accepted that their views were outdated. Retaining their views meant risking rejection." % (agent_name))
		self.add_to_journal(random.choice(LyraDiscussion.template_pubop_nsi_change_lowunc) % (agent_name))


	def template_pubop_nsi_conform_forced_journal(self, agent_name):
		if self.contemplation: 
			return
		self.add_to_journal(random.choice(LyraDiscussion.template_pubop_nsi_conform_forced) % (agent_name))


	def template_nopubop_closer_journal(self, agent_name, mean_closest_group, change=True):
		if self.contemplation: 
			return
		if change: 
			views = self.view_grouping[mean_closest_group]
			if len(views) == 1:
				# then the agent tries to reconcile the difference between their internal attitudes and opinions
				self.add_to_journal(random.choice(LyraDiscussion.template_nopubop_closer_group_alone) % (agent_name))
			else:
				self.add_to_journal(random.choice(LyraDiscussion.template_nopubop_closer_group) % (agent_name, self.template_name_group_members([view["agent"] for view in views], agent_name)))
		else:
			self.add_to_journal(random.choice(LyraDiscussion.template_nopubop_closer_noChange) % (agent_name))

	template_grouping_choices_article_agree = [
		"--> %s agreed with the article's position "
	]

	template_grouping_choices = [
		# Template string + name of other group participants
		"--> %s agreed with each other's views ", 
		"--> %s were in accordance", 
		"--> %s found their views aligned with one another", 
		"--> %s agreed the most with each other", 
		"--> %s sided with one another"
	]

	template_no_group_small = [
		# "No one took sides.", 
		# "There were too few participants to form coalitions.",
		"There weren't enough conversationalists for distinct coalitions to emerge."
	]

	template_consensus = [
		"The participants found they reached a consensus.",
		# "The group realized they were preaching to the choir.",
		# "Everyone realized they were all saying the same thing.",
		# "Everyone agreed upon the basics"
	]

	template_alone_group = [
		"--> %s (%s:%s) disagreed with the rest.",
		# "%s could see groups forming with like minded individuals. But they stood their ground.",
		# "%s refused to budge from their views.",
		# "%s disagreed with the other's views on the article."
	]

	template_pubop_formed = [
		"Public opinion seemed to have formed.",
		# "Public opinion has emerged."
	]

	template_pubop_highUnc = [
		"%s was very uncertain about their own views. \n\tThey decided their personal attitudes aligned with the majority opinion and changed their mind accordingly.",
		# "Uncertain as %s was, agreeing with the majority opinion seemed like the safest option. ",
		# "Uncertain and unable to make up their mind, %s decided the majority was right."
	]

	template_pubop_nsi = [
		# "%s realized they were experiencing cognitive dissonance between the opinions they were expressing and the point of view that they held.",
		# "%s realized that their opinions didn't really match what they believed",
		"""%s realized the opinion they expressed was inconsistent with their internal attitude on the article.\n\tThey looked for the group with views closest to their own expressed opinions."""
	]


	template_pubop_nsi_nochange = [
		"""After an internal debate %s realized that the strength of the group's convictions was too weak.\n\tThey maintained their opinions.""",
		# "However, the public opinion did not sway %s. They maintained their views."
	]

	# High uncertainty
	template_pubop_nsi_change_highunc = [
		# "%s felt this group's opinion best captured their own and changed their mind.",
		# "%s felt the majority opinion was a better representation of their own attitudes, and changed their mind.",
		"""%s felt that the group's views represented a natural evolution of their own attitudes.\n\t They modified their opinions and attitudes to match.""", 
		# "%s felt they agreed with the majority"
	]

	# Low uncertainty
	template_pubop_nsi_change_lowunc = [
		"""The group opinion was strong enough to sway %s.\n\tThey accepted the group's views and changed their opinions and attitudes to match.""",
		# "Convinced by the majority opinion, $s changed their views on the article.",
		# "%s was swayed by the public opinion. They changed their views to match.", 
		# "Convinced by the public opinion, %s changed their mind on the matter."
	]

	template_pubop_nsi_conform_forced = [
		"""%s grew aware of the peer pressure to conform to the group's views. \n\tHowever, they were aware the group's opinions did not agree with their internal attitudes on the matter.\n\tThey pretended to agree with the group to avoid exclusion from their midst."""
		# "Unable to convince the others, %s stayed silent.",
		# "%s decided it was best to pretend to agree with the others.",
		# "Not wanting to be ridiculed, %s decided to pretend they agreed with the public opinion.",
		# "%s remained unconvinced by the public opinion and stayed silent."
	]

	template_nopubop_closer_group_alone = [
		"%s did not agree with the other opinions. \n\tThey realized their expressed opinions did not truly match their internal attitudes.\n\tThey tried to reconcile the difference."
	]

	template_nopubop_closer_group = [
		# Agent tries to reconcile the difference between their attitude and the opinions of the others in the closest group
		"%s was swayed by %s's argument.\n\tThey decided to change their rating to indicate the same."
	]

	template_nopubop_closer_noChange = [
		"%s decided the group's views were insufficient to change their opinions."
	]


