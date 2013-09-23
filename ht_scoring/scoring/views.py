import ht_scoring.scoring.models as m
from django.core.urlresolvers import reverse
import SkeletalDisplay.views as views
import django.views.generic as generic
from django import forms
from django.forms.formsets import formset_factory
from django.db import models
import settings, traceback
import HotDjango

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
					{'url': reverse('faults', kwargs={'comp': self._comp_id}), 'name': 'Enter Faults'},
					{'url': reverse('times', kwargs={'comp': self._comp_id}), 'name': 'Enter Times'},
					{'url': reverse('completeness', kwargs={'comp': self._comp_id}), 'name': 'Completeness'},
					{'url': reverse('results', kwargs={'comp': self._comp_id}), 'name': 'Results'}]
			self._context['page_menu'] = buttons
			
	def page_loader(self, **kw):
		self._context = super(ScoringBase, self).get_context_data(**kw)
		self._context['info'] = []
		self._context['errors'] = []
		self._comp_id = int(kw['comp'])
		self._comp = m.Competition.objects.get(id=self._comp_id)
		self._context['fences'] = str(self._comp.fences)
		self._context['entries'] = str(self._comp.entries())
		self._context['optimum_time'] = self._comp.optimum_time_str()
		self._context['percent_complete'] = self._comp.complete_percent_str()
	
	def _calc_results(self):
		rounds = m.Round.objects.filter(competition=self._comp).filter(not_competative=False).filter(time_finish__isnull=False)
		rounds = rounds.annotate(faults=models.Sum('fences__faults'))
		rounds = rounds.annotate(eliminated_all=models.Sum('fences__eliminated'))
		rounds = rounds.extra(select={'abs_time_diff':'ABS(time_diff)'})
		rounds = rounds.extra(order_by = ['eliminated_all', 'faults', 'abs_time_diff'])
		place = 1
		for r in rounds:
			r.place=place
			r.save()
			place += 1
		return rounds

class Index(ScoringBase):
	template_name = 'index.html'
	
	def get_context_data(self, **kw):
		self._context = super(Index, self).get_context_data(**kw)
		self._context = super(Index, self).get_context_data(**kw)
		self._context['title'] = settings.SITE_TITLE
		table = HotDjango.get_all_apps()['ht_scoring__scoring']['Competition'].Table2
		self._context['table'] = table(m.Competition.objects.all())
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
		self._context['fence_list'] = range(1, self._comp.fences + 1)
		self._calc_results()
		rounds = []
		for r in m.Round.objects.filter(competition=self._comp):
			the_round = {'competitor': r.competitor.number}
			the_round['fences'] = {}
			for fn in self._context['fence_list']:
				the_round['fences'][fn] = {'state': 'empty', 'faults': ''}
				fences = m.Fence.objects.filter(number=fn, round=r)
				if fences.exists():
					the_fence = fences[0]
					the_round['fences'][fn]['faults'] = the_fence.faults_string()
					if the_fence.auto_completed:
						the_round['fences'][fn]['state'] = 'auto'
					else:
						if the_fence.faults == 0:
							the_round['fences'][fn]['state'] = 'clear'
						else:
							the_round['fences'][fn]['state'] = 'faults'
			the_round['time_start'] = r.time_start_str()
			the_round['time_finish'] = r.time_finish_str()
			the_round['time'] = r.time_str()
			the_round['time_diff'] = r.time_diff_str()
			the_round['status'] = r.faults_string();
			the_round['place'] = (r.place, '')[r.place is None];
			rounds.append(the_round)
		self._context['rounds'] = rounds
		self._context['title'] = self._comp.name
		self.scoring_base(generate_side_menu=False)
		return self._context
	

rows_per_page = 15

class FormsetForm(forms.Form):
	competitor = forms.IntegerField()
	input_value = forms.CharField(max_length=10)
	input_value.initial = 0

class FillInForm(ScoringBase):
	template_name = 'faults_times.html'
	
	def get(self, request, *args, **kw):
		self.page_loader(**kw)
		self.empty_form()
		context = self.get_context_data(**kw)
		return self.render_to_response(context)
	
	def post(self, request, *args, **kw):
		self.page_loader(**kw)
		self.full_form(request)
		context = self.get_context_data(**kw)
		return self.render_to_response(context)
	
	def full_form(self, request):
		self._header_form = self.header_form_cls(request.POST, fences = self._comp.fences)
		self._formset = formset_factory(self.formset_cls)(request.POST)
		if self._header_form.is_valid() and self._formset.is_valid():
			if self.process_forms():
				self.empty_form()
		else:
			self._context['errors'].append('Problem Submitting form')
		
	def empty_form(self):
		self._header_form = self.header_form_cls(fences = self._comp.fences)
		self._formset = formset_factory(self.formset_cls, extra=rows_per_page, max_num=rows_per_page)()
		
	def process_forms(self):
		clear = True
		try:
			if not self.process_header():
				clear = False
			else:
				for row in self._formset.cleaned_data:
					if 'competitor' in row:
						competitor_number = row['competitor']
						try:
							c_round = m.Round.objects.get(competition=self._comp, competitor__number=competitor_number)
						except m.Round.DoesNotExist:
							competitors = m.Competitor.objects.filter(number=competitor_number)
							if competitors.exists():
								self._context['errors'].append('%s not entered in %s, faults not recorded'\
															 % (competitors[0], self._comp.name))
							else:
								self._context['errors'].append('No competitor with number: %d' % competitor_number)
							clear = False
							continue
						if not self.process_row(row, c_round):
							clear = False
		except Exception, e:
			self._context['errors'].append('Problem Processing form:')
			self._context['errors'].append(str(e))
			if hasattr(e, 'detail'):
				self._context['errors'].append(e.detail)
			print e
			traceback.print_exc()
			clear = False
		else:
			self._context['info'].append('Data updated Successfully')
			if hasattr(self, '_fence_number'):
				self._context['info'].append('Fence %d' % self._fence_number)
		return clear
	
class FaultsFormHeader(forms.Form):
	mark_complete = forms.BooleanField(required=False, label = 'Mark Fence Complete')
	fence = forms.ChoiceField(label = 'Fence')
	
	def __init__(self, *args, **kwargs):
		fences = kwargs.pop('fences', 0)
		super(FaultsFormHeader, self).__init__(*args, **kwargs)
		c = [(i, 'Fence %d' % i) for i in range(1, fences + 1)]
		self.fields['fence'].choices = c
	
class FaultsFormsetForm(FormsetForm):
	def __init__(self, *args, **kwargs):
		super(FaultsFormsetForm, self).__init__(*args, **kwargs)
		self.fields['input_value'].label = 'Faults'

class Faults(FillInForm):
	def __init__(self, *args, **kw):
		self.header_form_cls = FaultsFormHeader
		self.formset_cls = FaultsFormsetForm
		super(Faults, self).__init__(*args, **kw)
		
	def get_context_data(self, **kw):
		self._context['form_header'] = self._header_form
		self._context['formset'] = self._formset
		self._context['help_text'] = 'Enter faults below, if eliminated enter E.'
		self._context['title'] = self._comp.name + ': Enter Faults'
		self.scoring_base()
		return self._context
	
	def process_header(self):
		self._fence_number = int(self._header_form.cleaned_data['fence'])
		if self._header_form.cleaned_data['mark_complete']:
			all_rounds = m.Round.objects.filter(competition=self._comp).exclude(fences__number=self._fence_number)
			fences = [m.Fence(number=self._fence_number, round=r, auto_completed=True) for r in all_rounds]
			m.Fence.objects.bulk_create(fences)
		return True
	
	def process_row(self, row, c_round):
		if row['input_value'].lower() == 'e':
			eliminated = True
			faults = 60
		else:
			try:
				faults = int(row['input_value'])
			except ValueError:
				self._context['errors'].append('%s could not be understood' % row['input_value'])
				return False
			eliminated = False
		fences = m.Fence.objects.filter(number=self._fence_number, round=c_round)
		if fences.exists():
			fence=fences[0]
			if not fence.auto_completed:
				self._context['info'].append('Fence already exists for %s: Fence %d, updating faults' % (c_round, self._fence_number))
			fence.auto_completed = False
		else:
			fence = m.Fence(number=self._fence_number, round=c_round)
		fence.faults = faults
		fence.eliminated = eliminated
		fence.save()
		return True

	
class TimesFormHeader(forms.Form):
	choices=[('time_start', 'Start Times'), ('time_finish', 'Finish Times')]
	time_choice = forms.ChoiceField(label = 'Start or End Time', choices = choices)
	
	def __init__(self, *args, **kwargs):
		kwargs.pop('fences', 0)
		super(TimesFormHeader, self).__init__(*args, **kwargs)
	
class TimesFormsetForm(FormsetForm):
	def __init__(self, *args, **kwargs):
		super(TimesFormsetForm, self).__init__(*args, **kwargs)
		self.fields['input_value'].label = 'Times'
		
class Times(FillInForm):
	def __init__(self, *args, **kw):
		self.header_form_cls = TimesFormHeader
		self.formset_cls = TimesFormsetForm
		super(Times, self).__init__(*args, **kw)
		
	def get_context_data(self, **kw):
		self._context['form_header'] = self._header_form
		self._context['formset'] = self._formset
		self._context['help_text'] = 'time format: [hours][+][mins][+][seconds] (delimiter space, + or :)  eg. 1+45+17.4, or 105+17.4, or just 6317.4.'
		self._context['title'] = self._comp.name + ': Enter Times'
		self.scoring_base()
		return self._context
	
	def process_header(self):
		self._time_choice = self._header_form.cleaned_data['time_choice']
		return True
	
	def process_row(self, row, c_round):
		try:
			time = self._parser(row['input_value'].lower())
		except Exception:
			self._context['errors'].append('error processing time: %s' % row['input_value'])
			return False
		setattr(c_round, self._time_choice, time)
		c_round.save()
		return True
	
	def _parser(self, t):
		delims = [':', ' ', '+']
		delim = None
		for i in t:
			if i in delims:
				delim = i
				continue
		if delim is not None:
			ts = t.split(delim)
			secs = 0
			if t.count(delim) > 1:
				h = int(ts.pop(0))
				secs = h * 3600
			secs += int(ts.pop(0)) * 60
			secs += float(ts.pop(0))
			return secs
		else:
			secs = float(t)
			return secs

class Results(ScoringBase):
	template_name = 'results.html'
	
	def get_context_data(self, **kw):
		self.page_loader(**kw)
		round_models = self._calc_results()
		rounds = []
		for r in round_models:
			the_round = {}
			the_round['place'] = str(r.place)
			the_round['number'] = str(r.competitor.number)
			the_round['name'] = r.competitor.name()
			the_round['horse'] = r.competitor.horse
			the_round['group'] = r.competitor.get_group()
			the_round['faults'] = r.faults_string()
			the_round['time_diff'] = r.time_diff_str()
			the_round['time'] = r.time_str()
			rounds.append(the_round)
		self._context['rounds'] = rounds
		self._context['title'] = self._comp.name + ' Results'
		self.scoring_base()
		return self._context
