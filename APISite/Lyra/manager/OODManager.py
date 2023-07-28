from rest_framework import status

from ..models import ObjectOfDiscussion
from ..serializers import ObjectOfDiscussionSerializer


def oods_list(request, data, sim_id=None):
	oods = ObjectOfDiscussion.objects.filter(topic__simulation=sim_id)
	topic_id = data.get("topic", "")
	if topic_id: 
		oods = ObjectOfDiscussion.objects.filter(topic=topic_id)

	ood_serializer = ObjectOfDiscussionSerializer(oods, many=True)
	return {"output": ood_serializer.data, "status":status.HTTP_200_OK}


def oods_add(request, data, sim_id=None):
	oods = data.get("oods", [])
	outputs = []

	for ood in oods: 
		_serializer = ObjectOfDiscussionSerializer(data=ood)

		if _serializer.is_valid():
			_serializer.save()
			outputs.append({"title":ood["title"], "output":_serializer.data, "status":status.HTTP_201_CREATED})
		else:
			outputs.append({"title":ood["title"], "output":_serializer.errors, "status":status.HTTP_400_BAD_REQUEST})

	return outputs

def oods_delete(request, data, sim_id=None):
	ood_id = data.get("ood_id")
	ood = ObjectOfDiscussion.objects.filter(topic__simulation=sim_id, id=ood_id)
	if ood: 
		ood.delete() 
		return {'output': 'Ood was deleted successfully!', "status":status.HTTP_204_NO_CONTENT}

	return {'output': 'Ood does not exist!', "status":status.HTTP_400_BAD_REQUEST}


##############

def get_ood_by_id(ood_id=None): 
	ood = None
	try: 
		ood = ObjectOfDiscussion.objects.get(id=ood_id)
	except ObjectOfDiscussion.DoesNotExist:
		print("Could not find OOD:%s"%(ood_id))
	return ood



