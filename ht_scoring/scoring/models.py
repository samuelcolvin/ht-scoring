from django.db import models

unknown = 9999

def float2time(f):
	if f is None:
		return ''
	elif f == unknown:
		return ''
	elif f >= 3600:
		h = int(f / 3600)
		return '%2d:%s' % (h, float2time(f % 3600))
	elif f >= 60:
		m = int(f / 60)
		return '%02d:%s' % (m, float2time(f % 60))
	else:
		fmt = '%05.02f'
		if round(f) == f:
			fmt = '%02.0f'
		return fmt % f

class Group(models.Model):
	name = models.CharField(max_length=200)
	name.help_text = 'Eg. Pony Club'
	def no_members(self):
		return len(self.members.all())
	
	def __unicode__(self):
		s = ''
		if self.no_members() > 1:
			s = 's'
		return '%s, member%s: %d' % (self.name, s, self.no_members())
	
def create_competition_number():
	n = 1
	for comp in Competition.objects.all():
		if comp.number >= n:
			n = comp.number + 1
	return n
	
class Competition(models.Model):
	name = models.CharField(max_length=200)
	optimum_time = models.FloatField()
	optimum_time.help_text = 'Total Time in seconds, eg. 1m30s should be 90'
	fences = models.IntegerField()
	fences.help_text = 'Total Number of fences in the competition.'
	def entries(self):
		return len(self.rounds.all())
	
	def optimum_time_str(self):		
		return float2time(self.optimum_time)
	
	def rounds_count(self):
		return self.rounds.count()
	
	def complete_percent_str(self):
		fences = Fence.objects.filter(round__competition=self).count()
		rounds_with_times = Round.objects\
			.filter(competition=self).filter(time_finish__isnull=False).count()
		complete = float(fences + rounds_with_times)\
			/float(self.rounds.count() * (self.fences+1))*100
		return '%0.2f%%' % complete
		
	def __unicode__(self):
		return self.name
		
	class Meta:
		ordering = ['id']
	
def create_competitor_number():
	n = 1
	for comp in Competitor.objects.all():
		if comp.number >= n:
			n = comp.number + 1
	return n
		
class Competitor(models.Model):
	number = models.IntegerField(default=create_competitor_number)
	first_name = models.CharField(max_length=200)
	last_name = models.CharField(max_length=200)
	horse = models.CharField(max_length=200)
	group = models.ForeignKey(Group, blank=True, null=True, related_name='members')
	group.help_text = 'Eg. Pony Club'
	comment = models.TextField(max_length=1000, blank=True, null=True)
	
	def name(self):
		return self.first_name + ' ' + self.last_name
	
	def total_rounds(self):
		return len(self.rounds.all())
	
	def get_group(self):
		if self.group:
			return self.group.name
		else:
			return '-'
		
	def __unicode__(self):
		return '%d %s' % (self.number, self.name())
	
	def num_name(self):
		return 'no. ' + str(self.number) + ': ' + self.name()
	
	class Meta:
		ordering = ['number']

class Round(models.Model):
	competition = models.ForeignKey(Competition, related_name='rounds')
	competitor = models.ForeignKey(Competitor, related_name='rounds')
	not_competative = models.BooleanField()
	time_start = models.FloatField(default = 0)
	time_finish = models.FloatField(null=True, blank=True)
	time_diff = models.FloatField(null=True, blank=True)
	time_diff.short_description = 'Time Difference from Optimum'
	place = models.IntegerField(null=True, blank=True)
	
	def save(self, *args, **kw):
		if not None in [self.time_finish, self.time_start, self.competition.optimum_time]:
			self.time_diff = self.time_finish - self.time_start - self.competition.optimum_time
		super(Round, self).save(*args, **kw)
	
	class Meta:
		ordering = ['competitor']
		
	def time(self):
		if self.time_start != None and self.time_finish != None:
			return self.time_finish - self.time_start
		else:
			return None
	
	def get_faults(self):
		faults = self.fences.aggregate(total_faults = models.Sum('faults'))['total_faults']
		if faults is None:
			return 0
		else:
			return faults
		
	def eliminated(self):
		for f in self.fences.all():
			if f.eliminated:
				return True
		return False
	
	def faults_string(self):
		if self.not_competative:
			return 'HC'
		if self.eliminated():
			return 'E'
		else:
			return '%d' % self.get_faults()
	
	def time_start_str(self):
		return float2time(self.time_start)
	time_start_str.short_description = 'Starting Time'
		
	def time_finish_str(self):
		return float2time(self.time_finish)
	time_finish_str.short_description = 'Finishing Time'
			
	def time_str(self):
		return float2time(self.time())
			
	def time_diff_str(self):
		return float2time(self.time_diff)
	time_diff_str.short_description = 'Time Difference from Optimum'
	
	def __unicode__(self):
		return '%s in %s' % (self.competitor, self.competition.name)
	
		
class Fence(models.Model):
	number = models.IntegerField()
	faults = models.IntegerField(default=0)
	eliminated = models.BooleanField(default = False)
	auto_completed = models.BooleanField(default = False)
	round = models.ForeignKey(Round, related_name='fences')
	
	def full_name(self):
		return 'Fence %d' % self.number
	full_name.short_description = 'Fence Number'
	
	def faults_string(self):
		if self.eliminated:
			return 'E'
		if self.faults == 0 and self.auto_completed:
			return ''
		else:
			return '%d' % self.faults
	
	def competition(self):
		return self.round.competition.name
	
	def __unicode__(self):
		return 'fence %d, class %s, competitor no. %d' % (self.number, self.competition(), self.round.competitor.number)
