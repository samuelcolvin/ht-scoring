# from ht_scoring.scoring.models import Competition, Round, float2time

# class AddFaults:
# 	def __init__(self, mark_complete):
# 		self.mark_complete = mark_complete
# 		
# 	def process(self, comp_id, fence_number, new_fences, errors, comments):
# 		rounds = all_rounds()
# 		for number in new_fences:
# 			key = (number, comp_id)
# 			if new_fences[number] == 'E':
# 				faults = 60
# 				eliminated = True
# 			else:
# 				faults = new_fences[number]
# 				eliminated = False
# 			if rounds.has_key(key):
# 				s = 'Fence: competitor number ' + str(number) + ', fault ' + str(new_fences[number]) + ', fence ' + str(fence_number) + ': '
# 				if Fence.objects.filter(number=fence_number, round=rounds[key]):
# 					s += '***Fence already exists***, updating faults'
# 					fence = Fence.objects.get(number=fence_number, round=rounds[key])
# 					fence.faults = faults
# 					fence.auto_completed = False
# 					fence.eliminated = eliminated
# 					fence.save()
# 				else:
# 					s += 'creating new fence'
# 					fence = Fence(number=fence_number, round=rounds[key])
# 					fence.faults = faults
# 					fence.eliminated = eliminated
# 					fence.save()
# 				comments.append(s)
# 			else:
# 				errors.append('No entry found for number ' + str(number) + ' in this class, ignoring row.')
# 				
# 		if self.mark_complete:
# 			comments.append('Marking Fence Complete')
# 			comp = Competition.objects.get(id=comp_id)
# 			rounds = Round.objects.filter(competition = comp)
# 			for r in rounds:
# 				if not Fence.objects.filter(number=fence_number, round=r):
# 					fence = Fence(number=fence_number, round=r)
# 					fence.faults = 0
# 					fence.eliminated = False
# 					fence.auto_completed = True
# 					fence.save()
# 		
# 	def parser(self, f):
# 		if f.lower() == 'e':
# 			return 'E'
# 		else:
# 			return int(f)

			
# class AddTimes:
# 	def __init__(self, stage):
# 		self.stage = stage
# 		
# 	def process(self, comp_id, fence_number, times, errors, comments):
# 		rounds = all_rounds()
# 		for number in times:
# 			key = (number, comp_id)
# 			if rounds.has_key(key):
# 				if self.stage == 'start':
# 					rounds[key].time_start = times[number]
# 				else:
# 					rounds[key].time_finish = times[number]
# 				rounds[key].save()
# 				comments.append('Setting %s time = %s to number %d.' % (self.stage, float2time(times[number]), number))
# 			else:
# 				errors.append('No entry found for number ' + str(number) + ', ignoring row.')
# 	
# 	def parser(self, t):
# 		delims = [':', ' ', '+']
# 		delim = None
# 		for i in t:
# 			if i in delims:
# 				delim = i
# 				continue
# 		if delim is not None:
# 			ts = t.split(delim)
# 			secs = 0
# 			if t.count(delim) > 1:
# 				h = int(ts.pop(0))
# 				secs = h * 3600
# 			secs += int(ts.pop(0)) * 60
# 			secs += float(ts.pop(0))
# 			return secs
# 		else:
# 			secs = float(t)
# 			return secs
# 		
# def calc_results(comp_id):
# 	comp = Competition.objects.get(id=comp_id)
# 	rounds = Round.objects.filter(competition=comp)
# 	rounds = list(rounds)
# 	rounds.sort(cmp=sort_func_place)
# 	for i in range(0, len(rounds)):
# 		rounds[i].place = i + 1
# 		rounds[i].save()
# 	return rounds
# 		
# def sort_func_place(a, b):
# 	if a.time_start != b.time_start:
# 		if a.time_start:
# 			return -1
# 		else:
# 			return 1
# 	if a.not_competative != b.not_competative:
# 		if a.not_competative:
# 			return 1
# 		else:
# 			return -1
# 	if a.eliminated() != b.eliminated():
# 		if a.eliminated():
# 			return 1
# 		else:
# 			return -1
# 	if a.faults() > b.faults():
# 		return 1
# 	if a.faults() < b.faults():
# 		return -1
# 	if abs(a.time_diff()) > abs(b.time_diff()):
# 		return 1
# 	if abs(a.time_diff()) < abs(b.time_diff()):
# 		return -1
# 	else:
# 		return 0
# 		
# def status_list(comp):
# 	rounds = Round.objects.filter(competition=comp)
# 	rounds = list(rounds)
# 	rounds.sort(cmp=sort_func_status)
# 	return rounds
# 		
# def sort_func_status(a, b):
# 	if a.time_start != b.time_start:
# 		if a.time_start:
# 			return -1
# 		else:
# 			return 1
# 	if a.competitor.number == b.competitor.number:
# 		return 0
# 	if a.competitor.number > b.competitor.number:
# 		return 1
# 	else:
# 		return -1
# 	
# 		
# def all_rounds():
# 	rounds = Round.objects.all()
# 	round_dict = {}
# 	for r in rounds:
# 		round_dict[(r.competitor.number, r.competition.id)] = r
# 	return round_dict
# 	
# def parse_time(t):
# 	delims = [':', ' ']
# 	delim = None
# 	for i in t:
# 		if i in delims:
# 			delim = i
# 			continue
# 	if delim is not None:
# 		ts = t.split(delim)
# 		secs = 0
# 		if t.count(delim) > 1:
# 			h = int(ts.pop(0))
# 			secs = h * 3600
# 		secs += int(ts.pop(0)) * 60
# 		secs += float(ts.pop(0))
# 		return secs
# 	else:
# 		secs = float(t)
# 		return secs