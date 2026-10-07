import subprocess
import sys

from event_serialization import event_from_payload, event_to_payload
from models import Event, SourceRecord


def test_cache_payload_preserves_schedule_provenance_and_is_independent():
    event = Event(id='a', title='Utställning', event_type='Utställning', category='Konst',
                  start_date='2026-10-07', end_date='2026-11-07', start_time=None,
                  venue='Galleriet', city='Stockholm', region='', country='Sverige',
                  excluded_dates=['2026-10-12'], source_records=[SourceRecord(source='Visit Stockholm', external_id='a')])
    payload = event_to_payload(event)
    restored = event_from_payload(payload)
    assert restored == event
    restored.excluded_dates.append('2026-10-19')
    assert payload['excluded_dates'] == event.excluded_dates == ['2026-10-12']
    assert restored.source_records[0].source == 'Visit Stockholm'


def test_cached_payload_survives_real_dataclass_module_reload():
    result = subprocess.run([sys.executable, '-c', '''
import importlib, pickle, models
from event_serialization import event_to_payload, event_from_payload
old = models.Event(id='a', title='Event', event_type='Sport', category='Sport', start_date='2026-10-07', end_date=None, start_time=None, venue='', city='Örebro', region='', country='Sverige')
old.source_records = [models.SourceRecord(source='Test', external_id='a')]
importlib.reload(models)
try:
    pickle.dumps(old)
except pickle.PicklingError:
    pass
else:
    raise AssertionError('stale dataclass must reproduce the deployment error')
payload = pickle.loads(pickle.dumps(event_to_payload(old)))
restored = event_from_payload(payload)
assert isinstance(restored, models.Event)
assert isinstance(restored.source_records[0], models.SourceRecord)
assert restored.id == old.id
'''], capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
