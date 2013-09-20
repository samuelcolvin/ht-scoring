import django_tables2 as tables
from django_tables2.utils import A
import SkeletalDisplay
import ht_scoring.scoring.models as m
import HotDjango

class Competitor(SkeletalDisplay.ModelDisplay):
    model = m.Competitor
    index = 0
    
    class DjangoTable(tables.Table):
        number = tables.LinkColumn('display_item', args=['ht_scoring.scoring', 'Competitor', A('pk')])
        name = tables.Column()
        total_rounds = tables.Column(verbose_name='Rounds')
        
        class Meta(SkeletalDisplay.ModelDisplayMeta):
            exclude = ('id', 'first_name', 'last_name', '')
    
    class HotTable(HotDjango.ModelSerialiser):
        class Meta:
            fields = ('id', 'name', 'description', 'comment', 'minimum_order', 'lead_time', 'nominal_price', 'costlevels')