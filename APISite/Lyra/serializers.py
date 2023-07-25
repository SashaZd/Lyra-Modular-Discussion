from rest_framework import serializers 
from Lyra.models import Simulation, Run, Agent, View, Discussion, Topic, ObjectOfDiscussion, RunAction, SimAction



class SimulationSerializer(serializers.ModelSerializer):
	class Meta:
		model = Simulation
		fields = '__all__'


class RunSerializer(serializers.ModelSerializer):
	class Meta:
		model = Run
		fields = '__all__'



class TopicSerializer(serializers.ModelSerializer):
	class Meta:
		model = Topic
		fields = '__all__'


class ObjectOfDiscussionSerializer(serializers.ModelSerializer):
	class Meta:
		model = ObjectOfDiscussion
		fields = '__all__'
		
		

class ViewSerializer(serializers.ModelSerializer):
	class Meta:
		model = View
		fields = '__all__'

		
class AgentSerializer(serializers.ModelSerializer):
	class Meta:
		model = Agent
		fields = ('id', 'run', 'name')


class DiscussionSerializer(serializers.ModelSerializer):
	class Meta:
		model = Discussion
		fields = '__all__'
		

class RunActionSerializer(serializers.ModelSerializer):
	class Meta:
		model = RunAction
		fields = '__all__'


class SimActionSerializer(serializers.ModelSerializer):
	class Meta:
		model = SimAction
		fields = '__all__'
		
