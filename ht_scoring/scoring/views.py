from django.template import RequestContext, Context, loader
from ht_scoring.scoring.models import Competition, Round, Fence
from django.http import HttpResponse
import ht_scoring.scoring.add_results as add_results

competition_pages = [
	{'page': 'faults', 'name': 'Enter Faults'},
	{'page': 'times_start', 'name': 'Enter Starting Times'},
	{'page': 'times_finish', 'name': 'Enter Finishing Times'},
	{'page': 'status', 'name': 'Show Status'},
	{'page': 'results', 'name': 'Show Results'},
]

rows_per_page = 20

def index(request):
	t = loader.get_template('index.html')
	title = 'Hunter Trial'
	c = Context({'competitions': Competition.objects.all(), 'pages': competition_pages})
	return base(request, title, t.render(c))
	
def faults(request):
	t = loader.get_template('faults_times.html')
	comp_id = int(request.GET[u'competition'])
	comp = Competition.objects.get(id=comp_id)
	fences = range(1, comp.fences + 1)
	rows = range(1, rows_per_page + 1)
	cont_d = {'competition': str(comp_id)}
	cont_d['competition_name'] = comp.name
	cont_d['value'] = 'Faults'
	cont_d['help_text'] = 'Enter faults below, if eliminated enter E.'
	cont_d['include_fences'] = True
	cont_d['question'] = 'Mark Fence Complete'
	cont_d['default'] = '0'
	cont_d['fences'] = fences
	cont_d['rounds'] = rows
	c = Context(cont_d)
	title = 'Enter Faults'
	return base(request, title, t.render(c))
	
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
	cont_d['competition_name'] = comp.name
	cont_d['value'] = ''
	cont_d['include_fences'] = False
	cont_d['help_text'] = 'time format: [hours][+][mins][+][seconds] (delimiter space, + or :)  eg. 1+45+17.4, or 105+17.4, or just 6317.4.'
	cont_d['default'] = ''
	cont_d['fences'] = fences
	cont_d['rounds'] = rows
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
	cont_d['fences'] = str(comp.fences)
	cont_d['entries'] = str(comp.entries())
	cont_d['optimum_time'] = comp.optimum_time_str()
	cont_d['fence_list'] = range(1, comp.fences + 1)
	rounds_raw = add_results.status_list(comp)
	rounds = []
	for rr in rounds_raw:
		the_round = {'competitor': rr.competitor.number}
		the_round['fences'] = {}
		for fn in cont_d['fence_list']:
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
	cont_d['rounds'] = rounds
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
	cont_d['fences'] = str(comp.fences)
	cont_d['entries'] = str(comp.entries())
	cont_d['optimum_time'] = comp.optimum_time_str()
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
	cont_d['rounds'] = rounds
	title = 'Results'
	c = Context(cont_d)
	return base(request, title, t.render(c))
	
	
def results_submit(request):
	pass

def base(request, title, content, wide=False):
	t = loader.get_template('base.html')
	cont_d = {'title': title, 'content': content, 'width': 'narrow'}
	if wide:
		cont_d['width'] = 'wide'
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
