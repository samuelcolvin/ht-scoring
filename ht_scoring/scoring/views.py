from django.template import RequestContext, Context, loader
import ht_scoring.scoring.models as m
from django.http import HttpResponse
import ht_scoring.scoring.add_results as add_results
from django.core.urlresolvers import reverse
import SkeletalDisplay.views as views
import django.views.generic as generic
import django.views.generic.edit as generic_edit
from django import forms
from django.forms.formsets import formset_factory
import settings

class ScoringBase(generic.TemplateView):
	def scoring_base(self, generate_side_menu=True):
		side_menu = None
		if generate_side_menu:
			side_menu = self.side_menu()
		self.page_buttons()
		self._context.update(views.base_context(self.request, side_menu))
	
	
	def side_menu(self):
		side_menu = []
		active=None
		if hasattr(self, '_comp_id'): active = self._comp_id
		for comp in m.Competition.objects.all():
			cls = ''
			if comp.id == active: cls = 'open'
			side_menu.append({'url': reverse('comp_display', kwargs={'comp': comp.id}), 
							'name': comp.name, 'class': cls, 'index': comp.id})
		side_menu = sorted(side_menu, key=lambda d: d['index'])
		return side_menu
	
	def page_buttons(self):
		if hasattr(self, '_comp_id'):
			buttons = [{'url': reverse('comp_display', kwargs={'comp': self._comp_id}), 'name': 'Summary'},
					{'url': reverse('completeness', kwargs={'comp': self._comp_id}), 'name': 'Completeness'},
					{'url': reverse('faults', kwargs={'comp': self._comp_id}), 'name': 'Enter Faults'}]
			self._context['page_menu'] = buttons
			
	def page_loader(self, **kw):
		self._context = super(ScoringBase, self).get_context_data(**kw)
		self._comp_id = int(kw['comp'])
		self._comp = m.Competition.objects.get(id=self._comp_id)

class Index(ScoringBase):
	template_name = 'index.html'
	
	def get_context_data(self, **kw):
		self._context = super(Index, self).get_context_data(**kw)
		self._context = super(Index, self).get_context_data(**kw)
		self._context['title'] = settings.SITE_TITLE
		self.scoring_base()
		return self._context
		

class CompetitionDisplay(ScoringBase):
	template_name = 'competition.html'
	
	def get_context_data(self, **kw):
		self.page_loader(**kw)
		self._context['title'] = self._comp.name
		self.scoring_base()
		return self._context

class CompletenessDisplay(ScoringBase):
	template_name = 'completeness.html'
	
	def get_context_data(self, **kw):
		self.page_loader(**kw)
		self._context['competition_name'] = self._comp.name
		self._context['fences'] = str(self._comp.fences)
		self._context['entries'] = str(self._comp.entries())
		self._context['optimum_time'] = self._comp.optimum_time_str()
		self._context['fence_list'] = range(1, self._comp.fences + 1)
		rounds_raw = add_results.status_list(self._comp)
		rounds = []
		for rr in rounds_raw:
			the_round = {'competitor': rr.competitor.number}
			the_round['fences'] = {}
			for fn in self._context['fence_list']:
				the_round['fences'][fn] = {'state': 'empty', 'faults': ''}
				if m.Fence.objects.filter(number=fn, round=rr) and rr.time_start:
					the_fence = m.Fence.objects.get(number=fn, round=rr)
					the_round['fences'][fn] = {'faults': the_fence.faults_string()}
					if the_fence.auto_completed:
						the_round['fences'][fn]['state'] = 'auto'
					else:
						if the_fence.faults == 0:
							the_round['fences'][fn]['state'] = 'clear'
						else:
							the_round['fences'][fn]['state'] = 'faults'
			the_round['time_start'] = rr.time_start_str()
			the_round['time_finish'] = rr.time_finish_str()
			the_round['time'] = rr.time_str()
			the_round['time_diff'] = rr.time_diff_str()
			the_round['status'] = rr.faults_string();
			the_round['place'] = (str(rr.place), '')[rr.place is None];
			rounds.append(the_round)
		self._context['rounds'] = rounds
		self._context['title'] = self._comp.name
		self.scoring_base(generate_side_menu=False)
		return self._context
	

rows_per_page = 20

class FaultsForm(forms.Form):
	competitor = forms.IntegerField()
	faults = forms.CharField(max_length=10)
	faults.initial = 0
	
class FaultsFormHeader(forms.Form):
	mark_complete = forms.BooleanField(required=False, label = 'Mark Fence Complete')
	fence = forms.ChoiceField(label = 'Fence')
	
	def __init__(self, *args, **kwargs):
		fences = kwargs.pop('fences', 0)
		super(FaultsFormHeader, self).__init__(*args, **kwargs)
		c = [(i, 'Fence %d' % i) for i in range(1, fences + 1)]
		self.fields['fence'].choices = c
			

class Faults(ScoringBase):
	template_name = 'faults_times.html'
	
	def get(self, request, *args, **kw):
		self.page_loader(**kw)
		self.empty_form()
		context = self.get_context_data(**kw)
		return self.render_to_response(context)
	
	def post(self, request, *args, **kw):
		self.page_loader(**kw)
		self.process_forms(request)
		context = self.get_context_data(**kw)
		return self.render_to_response(context)
		
	def get_context_data(self, **kw):
		self._context['form_header'] = self._header_form
		self._context['formset'] = self._formset
		self._context['help_text'] = 'Enter faults below, if eliminated enter E.'
		self._context['title'] = self._comp.name + ': Enter Faults'
		self.scoring_base()
		return self._context
	
	def process_forms(self, request):
		print request.POST
		self._header_form = FaultsFormHeader(request.POST, fences = self._comp.fences)
		self._formset = formset_factory(FaultsForm)(request.POST)
# 		import pdb; pdb.set_trace()
		if self._header_form.is_valid() and self._formset.is_valid():
			print 'ADD FAULTS'
			self.empty_form()
		else:
			print 'INVALID'
		
	def empty_form(self):
		self._header_form = FaultsFormHeader(fences = self._comp.fences)
		self._formset = formset_factory(FaultsForm, extra = 10)()
	
def faults_submit(request):
	mark_complete = False
	if request.POST.get('question', False):
		mark_complete = True
	add_faults = add_results.AddFaults(mark_complete)
	return process_table_form(request, add_faults, 'Faults Submitted')
	
def times(request):
	t = loader.get_template('faults_times.html')
	comp_id = int(request.GET[u'competition'])
	comp = Competition.objects.get(id=comp_id)
	fences = range(1, comp.fences + 1)
	rows = range(1, rows_per_page + 1)
	cont_d = {'competition': str(comp_id)}
	self._context['competition_name'] = comp.name
	self._context['value'] = ''
	self._context['include_fences'] = False
	self._context['help_text'] = 'time format: [hours][+][mins][+][seconds] (delimiter space, + or :)  eg. 1+45+17.4, or 105+17.4, or just 6317.4.'
	self._context['default'] = ''
	self._context['fences'] = fences
	self._context['rounds'] = rows
	c = Context(cont_d)
	return (c, t)
	
def times_start(request):
	(c, t) = times(request)
	title = 'Enter Starting Times'
	return base(request, title, t.render(c))
	
def times_start_submit(request):
	add_times = add_results.AddTimes('start')
	return process_table_form(request, add_times, 'Start Times Submitted')
	
def times_finish(request):
	(c, t) = times(request)
	title = 'Enter Finishing Times'
	return base(request, title, t.render(c))
	
def times_finish_submit(request):
	add_times = add_results.AddTimes('finish')
	return process_table_form(request, add_times, 'Finish Times Submitted')

def status(request):
	t = loader.get_template('completeness.html')
	comp_id = int(request.GET[u'competition'])
	comp = Competition.objects.get(id=comp_id)
	cont_d = {'competition_name': comp.name}
	self._context['fences'] = str(comp.fences)
	self._context['entries'] = str(comp.entries())
	self._context['optimum_time'] = comp.optimum_time_str()
	self._context['fence_list'] = range(1, comp.fences + 1)
	rounds_raw = add_results.status_list(comp)
	rounds = []
	for rr in rounds_raw:
		the_round = {'competitor': rr.competitor.number}
		the_round['fences'] = {}
		for fn in self._context['fence_list']:
			the_round['fences'][fn] = {'state': 'empty', 'faults': ''}
			if Fence.objects.filter(number=fn, round=rr) and rr.time_start:
				the_fence = Fence.objects.get(number=fn, round=rr)
				the_round['fences'][fn] = {'faults': the_fence.faults_string()}
				if the_fence.auto_completed:
					the_round['fences'][fn]['state'] = 'auto'
				else:
					if the_fence.faults == 0:
						the_round['fences'][fn]['state'] = 'clear'
					else:
						the_round['fences'][fn]['state'] = 'faults'
		the_round['time_start'] = rr.time_start_str()
		the_round['time_finish'] = rr.time_finish_str()
		the_round['time'] = rr.time_str()
		the_round['time_diff'] = rr.time_diff_str()
		the_round['status'] = rr.faults_string();
		the_round['place'] = (str(rr.place), '')[rr.place is None];
		rounds.append(the_round)
	self._context['rounds'] = rounds
	title = 'Status'
	c = Context(cont_d)
	return base(request, title, t.render(c), wide=True)
	
def status_submit(request):
	pass

show_results_to=6

def results(request):
	t = loader.get_template('results.html')
	comp_id = int(request.GET[u'competition'])
	comp = Competition.objects.get(id=comp_id)
	cont_d = {'competition_name': comp.name}
	self._context['fences'] = str(comp.fences)
	self._context['entries'] = str(comp.entries())
	self._context['optimum_time'] = comp.optimum_time_str()
	rounds_raw = add_results.calc_results(comp_id)
	rounds = []
	for r in rounds_raw:
#		if r.place > show_results_to:
#			break
		the_round = {}
		the_round['place'] = str(r.place)
		the_round['number'] = str(r.competitor.number)
		the_round['name'] = r.competitor.name()
		the_round['horse'] = r.competitor.horse
		the_round['pc'] = r.competitor.get_group()
		the_round['faults'] = r.faults_string()
		the_round['time_diff'] = r.time_diff_str()
		the_round['time'] = r.time_str()
		rounds.append(the_round)
	self._context['rounds'] = rounds
	title = 'Results'
	c = Context(cont_d)
	return base(request, title, t.render(c))
	
	
def results_submit(request):
	pass

def base(request, title, content, wide=False):
	t = loader.get_template('sbase.html')
	cont_d = {'title': title, 'content': content, 'width': 'narrow'}
	if wide:
		self._context['width'] = 'wide'
	c = RequestContext(request, cont_d)
	return HttpResponse(t.render(c))
	
def process_table_form(request, process, title):
	errors = []
	comments = []
	comments.append('processing table...')
	t = loader.get_template('submit.html')
	form = request.POST
	comp_id = int(form['competition'])
	fence_number = int(form['fence'])
	rows = range(1, rows_per_page + 1)
	table_data = {}
	for r in rows:
		number = form['round_number' + str(r)]
		if number != '':
			try:
				number = int(number)
			except ValueError:
				errors.append('Conversion error on number \'%s\', row ignored.' % number)
			else:
				value = form['round_value' + str(r)]
				table_data[number] = value
	competition = Competition.objects.get(id=comp_id)
	table2 = {}
	if len(table_data) > 0:
		for row in table_data:
			try:
				value = process.parser(table_data[row])
			except ValueError:
				errors.append('Conversion error on number %d value \'%s\', row ignored.' % (row, table_data[row]))
			else:
				table2[row] = value
		comments.append('%d rows being processed...' % len(table2))
		comments.append('fence %d, competition \'%s\'' % (fence_number, competition.name))
#	else:
#		comments.append('Nothing to do.')
	process.process(competition.id, fence_number, table2, errors, comments)
	c = Context({'errors': errors, 'comments' : comments})
	return base(request, title, t.render(c))
