import datetime
import json
import random
import tempfile
import time


def beginner_csv():
    ##############################################
    # CSV MODULE - csv output
    # Use the csv module to write out a csv file with headers and no blank lines
    filepath = tempfile.gettempdir() + '/output.csv'
    header = ['column1', 'column2']
    data = [{'column1': 'data1', 'column2': 'data1'},
            {'column1': 'data2', 'column2': 'data2'}]

    # DO WORK HERE


def beginner_nested():
    ##############################################
    # OPTIMIZE - nested for loop
    # Nested for loops can cause massive slows downs if their lists are long enough
    # Without modifying the original data_struct, remove the need for a NESTED iteration
    data_struct = [{'type': 'fileA', 'value': random.randint(0, 10)} for _ in range(10)]
    data_struct += [{'type': 'fileB', 'value': random.randint(0, 10)} for _ in range(10)]

    # DO WORK HERE

    for ext in ('fileA', 'fileB', 'fileC'):
        # Start nested iteration
        # DO WORK HERE
        items = list()
        for item in data_struct:
            if item['type'] == ext:
                items.append(item)
        # End nested iteration
        print ext, len(items)


def intermediate_subclass():
    ##############################################
    # SUBCLASS - incorrect integer
    # Modify the MyDict subclass so that `my_keys` stores the
    #   dictionary's keys in the order they were added
    # Do not use OrderedDict
    class MyDict(dict):
        def __init__(self):
            super(MyDict, self).__init__()

            self.my_keys = list()

            # DO WORK HERE

    # Test
    d = MyDict()
    d['apple'] = 'A'
    d['banana'] = 'B'
    d['carrot'] = 'C'
    d['danish'] = 'D'
    d.pop('danish')
    assert d.my_keys == ['apple', 'banana', 'carrot']


def intermediate_json():
    ##############################################
    # Json Callback
    # Create two callbacks. One for json.dumps and one for json.loads
    # that convert datetime.date to and from json syntax
    def callback_dump(o):
        # DO WORK HERE
        return o

    def callback_load(d):
        # DO WORK HERE
        return d

    # Test
    json_data = {
        'i': 0,
        's': 'python_test',
        'd': {'a': 'A', 'b': 'B'},
        'dt': datetime.date.today(),
    }

    js = json.dumps(json_data, default=callback_dump)
    jl = json.loads(js, object_hook=callback_load)
    assert type(jl['dt']) == datetime.date


def advanced_decorator():
    ##############################################
    # DECORATOR - timed cache
    # Create a decorator that will cache a function's result for a minimum of (duration) seconds
    def timed_cache(duration=10):
        # DO WORK HERE
        return

    # Test
    @timed_cache(duration=6)
    def a_method():
        return random.randint(0, 100)

    items = set()
    for i in range(10):
        items.add(a_method())
        time.sleep(1)
    assert len(items) == 2


if __name__ == '__main__':
    beginner_csv()
    beginner_nested()
    intermediate_subclass()
    intermediate_json()
    advanced_decorator()
