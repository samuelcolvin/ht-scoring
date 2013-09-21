import django_tables2 as tables
from django_tables2.utils import A
import SkeletalDisplay
import ht_scoring.scoring.models as m
import HotDjango

class Competitor(SkeletalDisplay.ModelDisplay):
    model = m.Competitor
    attached_tables = [{'name':'Round', 'populate':'rounds', 'title':'Rounds'}]
    index = 0
    hot_table_dft_field = 'first_name'
    
    class DjangoTable(tables.Table):
        number = tables.LinkColumn('display_item', args=['ht_scoring__scoring', 'Competitor', A('pk')])
        name = tables.Column()
        total_rounds = tables.Column(verbose_name='Rounds')
        comment = tables.Column(verbose_name='Comment')
        
        class Meta(SkeletalDisplay.ModelDisplayMeta):
            pass
    
    class HotTable(HotDjango.ModelSerialiser):
        group = HotDjango.IDNameSerialiser(m.Group)
        class Meta:
            fields = ('id', 'number', 'first_name', 'last_name', 'horse', 'comment', 'group')

class Competition(SkeletalDisplay.ModelDisplay):
    model = m.Competition
    attached_tables = [{'name':'Round', 'populate':'rounds', 'title':'Rounds'}]
    index = 1
    
    class DjangoTable(tables.Table):
        name = tables.LinkColumn('display_item', args=['ht_scoring__scoring', 'Competition', A('pk')])
        fences = tables.Column(verbose_name='Fences')
        rounds_count = tables.Column(verbose_name='Rounds')
        optimum_time_str = tables.Column(verbose_name='Optimum Time')
        complete_percent_str = tables.Column(verbose_name='Percentage Complete')
        
        class Meta(SkeletalDisplay.ModelDisplayMeta):
            pass
    
    class HotTable(HotDjango.ModelSerialiser):
        class Meta:
            fields = ('id', 'name', 'fences')

class Round(SkeletalDisplay.ModelDisplay):
    model = m.Round
    index = 2
    
    class DjangoTable(tables.Table):
        competitor = tables.LinkColumn('display_item', args=['ht_scoring__scoring', 'Round', A('pk')], verbose_name='Competitor')
        competition = tables.Column(verbose_name='Competition')
        get_faults = tables.Column(verbose_name='Faults')
        time_start_str = tables.Column(verbose_name='Start Time')
        time_finish_str = tables.Column(verbose_name='Finish Time')
        time_diff = tables.Column(verbose_name='Time Error')
        place = tables.Column(verbose_name='Place')
        
        class Meta(SkeletalDisplay.ModelDisplayMeta):
            exclude = []
    
    class HotTable(HotDjango.ModelSerialiser):
        competition = HotDjango.IDNameSerialiser(m.Competition)
        competitor = HotDjango.IDNameSerialiser(m.Competitor, lookup_field=Competitor.hot_table_dft_field)
        class Meta:
            fields = ('id', 'competition', 'competitor', 'not_competative', 
                      'time_start', 'time_finish', 'time_diff', 'place')